from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UsuarioViewSet, SalaViewSet, TallerViewSet,
    InscripcionViewSet, AsistenciaViewSet
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'salas', SalaViewSet, basename='sala')
router.register(r'talleres', TallerViewSet, basename='taller')
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')
router.register(r'asistencias', AsistenciaViewSet, basename='asistencia')

urlpatterns = [
    path('api/', include(router.urls)),
]
