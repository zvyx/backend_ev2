from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Usuario, Sala, Taller, Inscripcion, Asistencia

# Serializador para crear y consultar usuarios
class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, default='inacap123')

    class Meta:
        model = Usuario
        fields = ['id', 'nombre_completo', 'email', 'rut', 'rol', 'activo', 'fecha_registro', 'password']
        read_only_fields = ['id', 'fecha_registro']

    def create(self, validated_data):
        password = validated_data.pop('password', 'inacap123')
        email = validated_data.get('email')
        username = email.split('@')[0]

        # Crear el usuario en auth de Django para que pueda loguearse
        user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
        user.set_password(password)
        user.save()

        usuario = Usuario.objects.create(user=user, **validated_data)
        return usuario


# Datos esperados para el login
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


# Serializador de salas
class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = '__all__'


# Serializador de talleres con nombres legibles de profesor y sala
class TallerSerializer(serializers.ModelSerializer):
    profesor = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=False)
    profesor_nombre = serializers.ReadOnlyField(source='profesor.nombre_completo')
    sala_nombre = serializers.ReadOnlyField(source='sala.nombre')
    estado = serializers.CharField(required=False, default='solicitado')

    class Meta:
        model = Taller
        fields = [
            'id', 'nombre', 'descripcion', 'cupo_maximo', 'fecha_inicio',
            'estado', 'profesor', 'profesor_nombre', 'sala', 'sala_nombre', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


# Serializador de inscripciones con validacion de taller aprobado y cupos
class InscripcionSerializer(serializers.ModelSerializer):
    alumno = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=False)
    alumno_nombre = serializers.ReadOnlyField(source='alumno.nombre_completo')
    taller_nombre = serializers.ReadOnlyField(source='taller.nombre')
    estado = serializers.CharField(required=False, default='activa')

    class Meta:
        model = Inscripcion
        fields = [
            'id', 'alumno', 'alumno_nombre', 'taller', 'taller_nombre',
            'fecha_inscripcion', 'estado'
        ]
        read_only_fields = ['id', 'fecha_inscripcion']
        validators = []

    def validate(self, attrs):
        request = self.context.get('request')
        alumno = attrs.get('alumno')
        # Si no viene en el body, se toma el usuario logueado
        if not alumno and request and hasattr(request.user, 'usuario'):
            alumno = request.user.usuario
            attrs['alumno'] = alumno

        taller = attrs.get('taller')
        if not taller and self.instance:
            taller = self.instance.taller

        # 1. Solo se pueden inscribir en talleres aprobados
        if taller and taller.estado != 'aprobado':
            raise serializers.ValidationError({
                'taller': f"No puedes inscribirte en este taller porque está '{taller.estado}'. Solo se permite en talleres aprobados."
            })

        # 2. Verificar que el alumno no esté ya inscrito
        if alumno and taller and not self.instance:
            if Inscripcion.objects.filter(alumno=alumno, taller=taller).exists():
                raise serializers.ValidationError({
                    'non_field_errors': ["Ya estás inscrito en este taller."]
                })

        # 3. Validar cupos disponibles
        if taller:
            inscritos = taller.inscripciones.filter(estado='activa').count()
            if inscritos >= taller.cupo_maximo:
                raise serializers.ValidationError({
                    'taller': f"No quedan cupos disponibles para este taller (Máximo: {taller.cupo_maximo})."
                })

        return attrs


# Serializador para el registro de asistencia
class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencia
        fields = '__all__'