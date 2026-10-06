from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render

from .models import Usuario, Sala, Taller, Inscripcion, Asistencia
from .serializers import (
    UsuarioSerializer, SalaSerializer, TallerSerializer,
    InscripcionSerializer, AsistenciaSerializer, LoginSerializer
)
from .permissions import EsAdmin, EsAdminOReadOnly, EsJefatura, EsProfesor


# Endpoint para iniciar sesion con correo o RUT y obtener token JWT (Soporta HTML y JSON)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Renderiza el formulario visual para el navegador (tipo Django Admin)
        return render(request, 'talleres/login.html')

    def post(self, request):
        # Determinar si la petición proviene de un formulario web HTML o de una API JSON
        es_formulario_web = (
            request.content_type in ['application/x-www-form-urlencoded', 'multipart/form-data'] or
            request.headers.get('Sec-Fetch-Dest') == 'document' or
            'identificador' in request.POST
        )

        identificador = (
            request.data.get('identificador') or
            request.data.get('email') or
            request.data.get('rut') or
            ''
        ).strip()
        password = request.data.get('password', '')

        if not identificador or not password:
            msg = "Debe ingresar su RUT o correo y contraseña."
            if es_formulario_web:
                return render(request, 'talleres/login.html', {'error_mensaje': msg}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Datos incompletos", "mensaje": msg}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Buscar usuario por correo electrónico o por RUT
        usuario = Usuario.objects.filter(
            Q(email__iexact=identificador) | Q(rut__iexact=identificador)
        ).first()

        if not usuario:
            msg = "Usuario no existe, solicite su creación al administrador."
            if es_formulario_web:
                return render(request, 'talleres/login.html', {
                    'error_mensaje': msg,
                    'valor_identificador': identificador
                }, status=status.HTTP_404_NOT_FOUND)
            return Response({
                "error": "Usuario no encontrado",
                "mensaje": msg
            }, status=status.HTTP_404_NOT_FOUND)

        if not usuario.activo:
            msg = "Tu cuenta está desactivada. Consulta con el administrador."
            if es_formulario_web:
                return render(request, 'talleres/login.html', {
                    'error_mensaje': msg,
                    'valor_identificador': identificador
                }, status=status.HTTP_403_FORBIDDEN)
            return Response({
                "error": "Usuario inactivo",
                "mensaje": msg
            }, status=status.HTTP_403_FORBIDDEN)

        # 2. Si el usuario no tiene cuenta en User de Django, se crea
        if not usuario.user:
            username = usuario.email.split('@')[0]
            auth_user, _ = User.objects.get_or_create(username=username, defaults={'email': usuario.email})
            auth_user.set_password(password)
            auth_user.save()
            usuario.user = auth_user
            usuario.save()

        # 3. Validar contrasena
        if not usuario.user.check_password(password):
            msg = "Usuario no encontrado, verifique sus datos y vuelva a intentarlo."
            if es_formulario_web:
                return render(request, 'talleres/login.html', {
                    'error_mensaje': msg,
                    'valor_identificador': identificador
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                "error": "Credenciales inválidas",
                "mensaje": msg
            }, status=status.HTTP_400_BAD_REQUEST)

        # 4. Generar tokens JWT (Access y Refresh)
        refresh = RefreshToken.for_user(usuario.user)
        refresh['rol'] = usuario.rol
        refresh['email'] = usuario.email
        refresh['nombre'] = usuario.nombre_completo

        access_token = str(refresh.access_token)

        # Si es formulario web, renderizar vista de bienvenida interactiva
        if es_formulario_web:
            return render(request, 'talleres/login.html', {
                'usuario_logueado': usuario,
                'token_access': access_token,
                'token_refresh': str(refresh),
            }, status=status.HTTP_200_OK)

        return Response({
            "access": access_token,
            "refresh": str(refresh),
            "token": access_token,
            "usuario_id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            "rut": usuario.rut,
            "rol": usuario.rol,
            "mensaje": f"Bienvenido(a) {usuario.nombre_completo}"
        }, status=status.HTTP_200_OK)


# CRUD de usuarios (solo admin puede crear o modificar)
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('nombre_completo')
    serializer_class = UsuarioSerializer

    def get_queryset(self):
        queryset = Usuario.objects.all().order_by('nombre_completo')
        rut = self.request.query_params.get('rut')
        if rut:
            queryset = queryset.filter(rut__icontains=rut.strip())
        rol = self.request.query_params.get('rol')
        if rol:
            queryset = queryset.filter(rol=rol.upper().strip())
        buscar = self.request.query_params.get('buscar')
        if buscar:
            queryset = queryset.filter(
                Q(nombre_completo__icontains=buscar) |
                Q(email__icontains=buscar) |
                Q(rut__icontains=buscar)
            )
        return queryset

    def get_permissions(self):
        # Crear, editar o borrar solo el admin
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdmin()]
        # Ver usuarios cualquier usuario autenticado
        return [permissions.IsAuthenticated()]


# CRUD de salas (solo admin puede crear salas)
class SalaViewSet(viewsets.ModelViewSet):
    queryset = Sala.objects.all()
    serializer_class = SalaSerializer
    permission_classes = [EsAdminOReadOnly]

    def get_queryset(self):
        queryset = Sala.objects.all()
        # Filtro opcional por disponibilidad: ?disponible=true
        disponible = self.request.query_params.get('disponible')
        if disponible is not None:
            es_disponible = disponible.lower() in ['true', '1', 'si']
            queryset = queryset.filter(disponible=es_disponible)
        return queryset


# CRUD y flujo de talleres
class TallerViewSet(viewsets.ModelViewSet):
    queryset = Taller.objects.all()
    serializer_class = TallerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        perfil = getattr(user, 'usuario', None)

        if not user.is_superuser:
            if not perfil or perfil.rol not in ['PROFESOR', 'ADMIN']:
                raise PermissionDenied("Los alumnos no pueden solicitar talleres.")

        # Si lo propone un docente, se asigna como docente a cargo y queda en solicitado
        if perfil and perfil.rol == 'PROFESOR':
            serializer.save(profesor=perfil, estado='solicitado')
        else:
            serializer.save()

    def get_queryset(self):
        queryset = Taller.objects.all()

        # Filtro por estado: ?estado=aprobado o ?estado=solicitado
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)

        # Filtro por profesor: ?profesor=5
        profesor = self.request.query_params.get('profesor')
        if profesor:
            queryset = queryset.filter(profesor_id=profesor)

        # Filtro por nombre: ?buscar=ciberseguridad
        buscar = self.request.query_params.get('buscar')
        if buscar:
            queryset = queryset.filter(nombre__icontains=buscar)

        return queryset

    # Accion para que jefatura apruebe un taller
    @action(detail=True, methods=['post'], permission_classes=[EsJefatura])
    def aprobar(self, request, pk=None):
        taller = self.get_object()
        taller.estado = 'aprobado'
        taller.save()
        return Response({
            "mensaje": f"El taller '{taller.nombre}' ha sido aprobado por la jefatura.",
            "taller": TallerSerializer(taller).data
        }, status=status.HTTP_200_OK)

    # Accion para que jefatura rechace un taller
    @action(detail=True, methods=['post'], permission_classes=[EsJefatura])
    def rechazar(self, request, pk=None):
        taller = self.get_object()
        taller.estado = 'rechazado'
        taller.save()
        return Response({
            "mensaje": f"El taller '{taller.nombre}' ha sido rechazado por la jefatura.",
            "taller": TallerSerializer(taller).data
        }, status=status.HTTP_200_OK)

    # Consulta de alumnos inscritos en un taller especifico
    @action(detail=True, methods=['get'])
    def inscripciones(self, request, pk=None):
        taller = self.get_object()
        inscripciones = taller.inscripciones.filter(estado='activa')
        serializer = InscripcionSerializer(inscripciones, many=True)
        return Response(serializer.data)


# CRUD de inscripciones de alumnos
class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.all()
    serializer_class = InscripcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        perfil = getattr(user, 'usuario', None)
        # Si el usuario es un alumno, se asocia su perfil automaticamente
        if perfil and perfil.rol == 'ALUMNO':
            serializer.save(alumno=perfil)
        else:
            serializer.save()

    def get_queryset(self):
        queryset = Inscripcion.objects.all()
        user = self.request.user
        perfil = getattr(user, 'usuario', None)

        # Un alumno solo puede ver sus propias inscripciones
        if perfil and perfil.rol == 'ALUMNO':
            return queryset.filter(alumno=perfil)

        # Profesores y jefatura pueden filtrar por ?alumno=id
        alumno = self.request.query_params.get('alumno')
        if alumno:
            queryset = queryset.filter(alumno_id=alumno)
        return queryset


# CRUD de asistencias
class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
