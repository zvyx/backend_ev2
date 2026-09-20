from rest_framework import serializers
from .models import Usuario, Sala, Taller, Inscripcion, Asistencia

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model=Usuario
        fields='__all__'
        
class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model=Sala
        fields='__all__'
        

class TallerSerializer(serializers.ModelSerializer):
    class Meta:
        model=Taller
        fields='__all__'
        
  
class InscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Inscripcion
        fields='__all__'
        
  
class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model=Asistencia
        fields='__all__'
        
  