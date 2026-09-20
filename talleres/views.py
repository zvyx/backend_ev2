#from django.shortcuts import render

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Usuario, Sala, Taller, Inscripcion, Asistencia
from .serializers import (
    UsuarioSerializer, SalaSerializer, TallerSerializer, InscripcionSerializer, AsistenciaSerializer    
    )

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset=Usuario.objects.all()
    serializer_class= UsuarioSerializer 
    
class SalaViewSet(viewsets.ModelViewSet):
    queryset=Sala.objects.all()
    serializer_class=SalaSerializer

class TallerViewSet(viewsets.ModelViewSet):
    queryset=Taller.objects.all()
    serializer_class=TallerSerializer
    
    def get_queryset(self):
        self.queryset=Taller.objects.all()
        
        estado=self.request.query.params.get('estado') #filtro GET para ver el estado del taller
        if estado:
            queryset=queryset.filter(estado=estado)
    
        profesor=self.request.query.params.get('profesor') #fltro GET para ver el profesor del taller
        if profesor:
            queryset=queryset.filter(profesor_id=profesor)
            
        buscar=self.request.query.params.get('buscar') #filtro GET para ubscar por taller
        if buscar:
            queryset=queryset.filter(nombre__incontains=buscar)
            
        return queryset
        
    @action(detail=True, methods=['get']) #consulta metodo GET para la url /api/talleres/1/inscripciones/ muestra los alumnos segun el id del taller
    def inscripciones(self, request, pk=None):
        taller = self.get_object()
        inscripciones = taller.inscripciones.filter(estado='activa')
        serializer = InscripcionSerializer(inscripciones, many=True)
        return Response(serializer.data)

class InscripcionViewSet(viewsets.ModelViewSet):
    queryset=Inscripcion.objects.all()
    serializer_class=InscripcionSerializer
    
    def get_queryset(self):#filtro GET para buscar alumno /api/inscripciones/?alumno=1
        queryset=Inscripcion.objects.all()
        alumno=self.request.query.params.get('alumno')
        if alumno:
            queryset=queryset.filter(alumno_id=alumno)
        return queryset
    
class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.all()
    serializer_class = AsistenciaSerializer
