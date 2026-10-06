from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, SalaViewSet, TallerViewSet,
    InscripcionViewSet, AsistenciaViewSet, LoginView
)

# Router con endpoints CRUD
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'salas', SalaViewSet, basename='sala')
router.register(r'talleres', TallerViewSet, basename='taller')
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')

urlpatterns = [
    # Autenticación e ingreso por correo
    path('api/login/', LoginView.as_view(), name='login'),
    # Endpoints de los recursos
    path('api/', include(router.urls)),
]

# Guía rápida de endpoints para defensa y pruebas:
# 1. Login / Obtención de Token:
#    POST /api/login/ { "email": "edgar.lopez@inacap.cl", "password": "..." }
# 2. Salas (Solo Admin crea):
#    GET  /api/salas/
#    POST /api/salas/
# 3. Usuarios (Solo Admin crea):
#    GET  /api/usuarios/
#    POST /api/usuarios/
# 4. Talleres:
#    POST /api/talleres/                  (Docente solicita taller)
#    GET  /api/talleres/?estado=solicitado (Jefatura revisa pendientes)
#    POST /api/talleres/<id>/aprobar/     (Jefatura aprueba)
#    POST /api/talleres/<id>/rechazar/    (Jefatura rechaza)
#    GET  /api/talleres/?estado=aprobado  (Catálogo para alumnos)
#    GET  /api/talleres/?profesor=5       (Talleres de un docente)
# 5. Inscripciones:
#    POST /api/inscripciones/             (Alumno se inscribe en taller aprobado)
#    GET  /api/talleres/<id>/inscripciones/ (Alumnos inscritos en el taller)
