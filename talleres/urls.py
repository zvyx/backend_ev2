from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, SalaViewSet, TallerViewSet,
    InscripcionViewSet, AsistenciaViewSet
)

# router con los endpoints crud
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'salas', SalaViewSet, basename='sala')
router.register(r'talleres', TallerViewSet, basename='taller')
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')

urlpatterns = [
    path('api/', include(router.urls)),
]

# urls para probar y estudiar las consultas de la evaluacion:
# ver talleres aprobados (catalogo alumno): /api/talleres/?estado=aprobado
# ver talleres de un profe: /api/talleres/?profesor=1
# ver talleres solicitados (jefatura): /api/talleres/?estado=solicitado
# buscar taller por nombre: /api/talleres/?buscar=robotica
# alumnos inscritos en un taller (action): /api/talleres/1/inscripciones/
# inscripciones de un alumno: /api/inscripciones/?alumno=1

