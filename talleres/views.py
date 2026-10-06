from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login as django_login
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from .models import Usuario, Sala, Taller, Inscripcion, Asistencia
from .serializers import (
    UsuarioSerializer, SalaSerializer, TallerSerializer,
    InscripcionSerializer, AsistenciaSerializer, LoginSerializer
)
from .permissions import EsAdmin, EsAdminOReadOnly, EsJefatura, EsProfesor


# Endpoint para cerrar sesion de Django (limpia cookies de sesion y vuelve a login)
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        logout(request)
        return redirect('/login/')

    def post(self, request):
        logout(request)
        return redirect('/login/')


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

        # Si es formulario web, autenticar también la sesión de Django para navegación web fluida
        if es_formulario_web:
            django_login(request, usuario.user)
            request.session['jwt_access'] = access_token
            # Redireccionar directamente al catálogo interactivo para una experiencia web intuitiva
            return redirect('catalogo_talleres')

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


# Vista web interactiva para explorar el catálogo de talleres, inscribirse y gestionar estados
class CatalogoTalleresView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_perfil(self, request):
        if request.user.is_authenticated:
            return getattr(request.user, 'usuario', None)
        return None

    def get(self, request):
        perfil = self.get_perfil(request)
        if not perfil:
            return redirect('web_login')

        # Obtener talleres aprobados
        talleres_aprobados = Taller.objects.filter(estado='aprobado').select_related('profesor', 'sala').order_by('nombre')
        
        # Enriquecer información de cada taller con cupos e inscripción del usuario actual
        talleres_info = []
        mis_inscripciones = []
        if perfil.rol == 'ALUMNO':
            mis_inscripciones = Inscripcion.objects.filter(alumno=perfil, estado='activa').select_related('taller')
            talleres_inscritos_ids = set(mis_inscripciones.values_list('taller_id', flat=True))
        else:
            talleres_inscritos_ids = set()

        for t in talleres_aprobados:
            inscritos_count = t.inscripciones.filter(estado='activa').count()
            talleres_info.append({
                'id': t.id,
                'nombre': t.nombre,
                'descripcion': t.descripcion,
                'profesor': t.profesor,
                'sala': t.sala,
                'cupo_maximo': t.cupo_maximo,
                'total_inscritos': inscritos_count,
                'cupos_disponibles': max(0, t.cupo_maximo - inscritos_count),
                'lleno': inscritos_count >= t.cupo_maximo,
                'esta_inscrito': t.id in talleres_inscritos_ids,
            })

        # Si es profesor, obtener todos los talleres dictados por él (con contador de inscritos)
        mis_talleres_docente = []
        salas_disponibles = []
        if perfil.rol == 'PROFESOR':
            talleres_prof = Taller.objects.filter(profesor=perfil).select_related('sala').order_by('-fecha_creacion')
            for tp in talleres_prof:
                insc_act = tp.inscripciones.filter(estado='activa').count()
                mis_talleres_docente.append({
                    'id': tp.id,
                    'nombre': tp.nombre,
                    'descripcion': tp.descripcion,
                    'sala': tp.sala,
                    'cupo_maximo': tp.cupo_maximo,
                    'estado': tp.estado,
                    'total_inscritos': insc_act,
                    'fecha_inicio': tp.fecha_inicio,
                })
            salas_disponibles = Sala.objects.filter(disponible=True).order_by('nombre')

        # Si es jefatura o admin, obtener talleres en estado solicitado para aprobación/rechazo
        talleres_solicitados = []
        if perfil.rol in ['JEFE', 'ADMIN']:
            talleres_solicitados = Taller.objects.filter(estado='solicitado').select_related('profesor', 'sala')

        jwt_token = request.session.get('jwt_access', '')

        return render(request, 'talleres/catalogo.html', {
            'usuario': perfil,
            'talleres': talleres_info,
            'mis_inscripciones': mis_inscripciones,
            'mis_talleres_docente': mis_talleres_docente,
            'salas_disponibles': salas_disponibles,
            'talleres_solicitados': talleres_solicitados,
            'jwt_token': jwt_token,
        })

    def post(self, request):
        perfil = self.get_perfil(request)
        if not perfil:
            return redirect('web_login')

        accion = request.POST.get('accion')
        taller_id = request.POST.get('taller_id')

        # 1. Alumno se inscribe en taller aprobado
        if accion == 'inscribir' and perfil.rol == 'ALUMNO':
            taller = Taller.objects.filter(id=taller_id, estado='aprobado').first()
            if not taller:
                messages.error(request, "El taller no existe o no se encuentra disponible para inscripción.")
            elif taller.inscripciones.filter(estado='activa').count() >= taller.cupo_maximo:
                messages.error(request, "Lo sentimos, el taller no cuenta con cupos disponibles.")
            elif Inscripcion.objects.filter(alumno=perfil, taller=taller, estado='activa').exists():
                messages.warning(request, "Ya estás inscrito en este taller.")
            else:
                Inscripcion.objects.create(alumno=perfil, taller=taller, estado='activa')
                messages.success(request, f"¡Te has inscrito exitosamente en el taller '{taller.nombre}'!")

        # 2. Alumno cancela su inscripción
        elif accion == 'cancelar' and perfil.rol == 'ALUMNO':
            inscripcion = Inscripcion.objects.filter(alumno=perfil, taller_id=taller_id, estado='activa').first()
            if inscripcion:
                inscripcion.estado = 'cancelada'
                inscripcion.save()
                messages.success(request, "Inscripción cancelada correctamente.")
            else:
                messages.error(request, "No se encontró una inscripción activa en este taller.")

        # 3. Docente solicita la creación de un nuevo taller
        elif accion == 'solicitar_taller' and perfil.rol == 'PROFESOR':
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            cupo_maximo_raw = request.POST.get('cupo_maximo', '').strip()
            sala_id = request.POST.get('sala_id', '').strip()
            fecha_inicio_raw = request.POST.get('fecha_inicio', '').strip()

            if not nombre or not cupo_maximo_raw or not sala_id:
                messages.error(request, "Por favor completa todos los campos obligatorios (Nombre, Cupo y Sala).")
            else:
                try:
                    cupo_maximo = int(cupo_maximo_raw)
                    if cupo_maximo <= 0:
                        raise ValueError()
                except ValueError:
                    messages.error(request, "El cupo máximo debe ser un número entero mayor a 0.")
                    return redirect('catalogo_talleres')

                sala = Sala.objects.filter(id=sala_id).first()
                if not sala:
                    messages.error(request, "La sala seleccionada no es válida.")
                    return redirect('catalogo_talleres')

                # Validar fecha_inicio
                fecha_inicio = None
                if fecha_inicio_raw:
                    fecha_inicio = parse_datetime(fecha_inicio_raw)
                if not fecha_inicio:
                    fecha_inicio = timezone.now() + timezone.timedelta(days=7)

                nuevo_taller = Taller.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    cupo_maximo=cupo_maximo,
                    fecha_inicio=fecha_inicio,
                    sala=sala,
                    profesor=perfil,
                    estado='solicitado'
                )
                messages.success(
                    request,
                    f"¡Solicitud enviada! El taller '{nuevo_taller.nombre}' fue propuesto y está pendiente de aprobación por Jefatura."
                )

        # 4. Jefatura o Administrador aprueba propuesta
        elif accion == 'aprobar' and perfil.rol in ['JEFE', 'ADMIN']:
            taller = Taller.objects.filter(id=taller_id, estado='solicitado').first()
            if taller:
                taller.estado = 'aprobado'
                taller.save()
                messages.success(request, f"Taller '{taller.nombre}' aprobado con éxito.")
            else:
                messages.error(request, "El taller no existe o ya no se encuentra en estado solicitado.")

        # 5. Jefatura o Administrador rechaza propuesta
        elif accion == 'rechazar' and perfil.rol in ['JEFE', 'ADMIN']:
            taller = Taller.objects.filter(id=taller_id, estado='solicitado').first()
            if taller:
                taller.estado = 'rechazado'
                taller.save()
                messages.warning(request, f"Taller '{taller.nombre}' rechazado.")
            else:
                messages.error(request, "El taller no existe o ya no se encuentra en estado solicitado.")

        # Redirigir de vuelta a la vista GET del catálogo
        return redirect('catalogo_talleres')


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
