from django.db import models

#(Docentes, Alumnos, Jefatura, Admins)
class Usuario(models.Model):
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('PROFESOR', 'Docente'),
        ('ALUMNO', 'Estudiante'),
        ('JEFE', 'Jefatura / Rector'),
    ]
    
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    rut=models.CharField(max_length=12, unique=True)
    rol=models.CharField(max_length=15, choices=ROLES, default='ALUMNO')
    activo=models.BooleanField(default=True)
    fecha_registro=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.nombre_completo} ({self.get_rol_display()})'
    

   
class Sala(models.Model):
    nombre=models.CharField(max_length=50)
    codigo=models.CharField(max_length=20, unique=True)
    capacidad_maxima=models.PositiveIntegerField()
    ubicacion=models.CharField(max_length=120,blank=True, null=True)
    disponible=models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.nombre} [{self.codigo}] (Capacidad {self.capacidad_maxima})'
    
class Taller(models.Model):
    ESTADOS=[
        ('solicitado','Solicitado por Docente'),
        ('aprobado','Aprobado'),
        ('rechazado','Rechazado por jefatura'),
        ('finalizado','Finalizado'),
        
    ]
    
    nombre=models.CharField(max_length=198)
    descripcion=models.TextField(blank=True)
    cupo_maximo=models.PositiveIntegerField()
    fecha_inicio=models.DateTimeField()
    estado=models.CharField(max_length=22, choices=ESTADOS, default='solicitado')
    #instancias a usuarios y sala 
    profesor=models.ForeignKey(Usuario,on_delete=models.PROTECT, related_name='talleres_a_cargo') 
    sala=models.ForeignKey(Sala, on_delete=models.PROTECT, related_name='talleres')
    fecha_creacion=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.nombre} - Estado: {self.estado}'
    
class Inscripcion(models.Model):
    ESTADOS_INSCRIPCION=[
        ('activa','Activa'),
        ('cancelada', 'Cancelada'),
    ]
    
    alumno=models.ForeignKey(Usuario,on_delete=models.CASCADE, related_name='inscripciones')
    taller=models.ForeignKey(Taller, on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion=models.DateTimeField(auto_now_add=True)
    estado=models.CharField(max_length=15, choices=ESTADOS_INSCRIPCION, default='activa')
    
    class Meta: #para no inscribir un alumno dos veces en el mismo taller
        unique_together=('alumno', 'taller')
        
    def __str__(self):
        return f'{self.alumno.nombre_completo}: {self.taller.nombre} ({self.estado})'
    
class Asistencia(models.Model):
    inscripcion=models.ForeignKey(Inscripcion, on_delete=models.CASCADE, related_name='asistencias')
    fecha_sesion=models.DateField()
    presente=models.BooleanField(default=False)
    observacion=models.TextField(max_length=210, blank=True, null=True)
    
    def __str__(self):
        estado_str='Presente' if self.presente else 'Ausente'
        return f'{self.inscripcion.alumno.nombre_completo} - {self.fecha_sesion}: {estado_str}'