from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import Usuario, Sala, Taller, Inscripcion, Asistencia

# quitar el auth del panel admin
admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'email', 'rol', 'activo')
    list_filter = ('rol', 'activo')
    search_fields = ('nombre_completo', 'rut', 'email')

@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'capacidad_maxima', 'ubicacion', 'disponible')
    list_filter = ('disponible',)
    search_fields = ('nombre', 'codigo')

@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'profesor', 'sala', 'cupo_maximo', 'estado', 'fecha_inicio')
    list_filter = ('estado', 'sala')
    search_fields = ('nombre', 'profesor__nombre_completo')

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('alumno', 'taller', 'fecha_inscripcion', 'estado')
    list_filter = ('estado', 'taller')

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('inscripcion', 'fecha_sesion', 'presente', 'observacion')
    list_filter = ('presente', 'fecha_sesion')
