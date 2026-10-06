from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

from .models import Usuario, Sala, Taller, Inscripcion, Asistencia
from .serializers import (
    UsuarioSerializer, SalaSerializer, TallerSerializer,
    InscripcionSerializer, AsistenciaSerializer, LoginSerializer
)
from .permissions import EsAdmin, EsAdminOReadOnly, EsJefatura, EsProfesor


# Endpoint para iniciar sesion con el correo
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].strip().lower()
        password = serializer.validated_data['password']

        # 1. Buscar si el correo existe en la base de datos
        usuario = Usuario.objects.filter(email__iexact=email).first()
        if not usuario:
            return Response({
                "error": "Usuario no enrolado",
                "mensaje": "El correo ingresado no se encuentra registrado en el sistema. Por favor, eleve una solicitud a Administración para ser enrolado."
            }, status=status.HTTP_404_NOT_FOUND)

        if not usuario.activo:
            return Response({
                "error": "Usuario inactivo",
                "mensaje": "Tu cuenta está desactivada. Consulta con el administrador."
            }, status=status.HTTP_403_FORBIDDEN)

        # 2. Si el usuario no tiene cuenta en User de Django, se crea
        if not usuario.user:
            username = email.split('@')[0]
            auth_user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
            auth_user.set_password(password)
            auth_user.save()
            usuario.user = auth_user
            usuario.save()

        # 3. Validar contrasena
        if not usuario.user.check_password(password):
            return Response({
                "error": "Credenciales incorrectas",
                "mensaje": "La contraseña ingresada no es válida."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 4. Obtener o crear el token de autenticacion
        token, _ = Token.objects.get_or_create(user=usuario.user)

        return Response({
            "token": token.key,
            "usuario_id": usuario.id,
            "nombre_completo": usuario.nombre_completo,
            "email": usuario.email,
            "rol": usuario.rol,
            "mensaje": f"Bienvenido(a) {usuario.nombre_completo}"
        }, status=status.HTTP_200_OK)


# CRUD de usuarios (solo admin puede crear o modificar)
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by('nombre_completo')
    serializer_class = UsuarioSerializer

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
