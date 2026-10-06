from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Usuario, Sala, Taller, Inscripcion

class SistemaTalleresEvaluacion3Tests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Admin
        self.user_admin = User.objects.create_user(username='admin_test', email='admin@inacap.cl', password='password123')
        self.usuario_admin = Usuario.objects.create(
            user=self.user_admin, nombre_completo='Administrador',
            email='admin@inacap.cl', rut='1-1', rol='ADMIN'
        )

        # 2. Profesor
        self.user_profe = User.objects.create_user(username='profe_test', email='profe@inacap.cl', password='password123')
        self.usuario_profe = Usuario.objects.create(
            user=self.user_profe, nombre_completo='Profesor Edgar',
            email='profe@inacap.cl', rut='2-2', rol='PROFESOR'
        )

        # 3. Jefatura
        self.user_jefe = User.objects.create_user(username='jefe_test', email='jefe@inacap.cl', password='password123')
        self.usuario_jefe = Usuario.objects.create(
            user=self.user_jefe, nombre_completo='Jefe Eugenio',
            email='jefe@inacap.cl', rut='3-3', rol='JEFE'
        )

        # 4. Alumno
        self.user_alumno = User.objects.create_user(username='alumno_test', email='alumno@inacap.cl', password='password123')
        self.usuario_alumno = Usuario.objects.create(
            user=self.user_alumno, nombre_completo='Alumno Camila',
            email='alumno@inacap.cl', rut='4-4', rol='ALUMNO'
        )

        # Sala de prueba
        self.sala = Sala.objects.create(
            nombre='Laboratorio 101', codigo='LAB-101', capacidad_maxima=20, disponible=True
        )

    def test_login_usuario_no_enrolado(self):
        """Verifica que un correo no registrado devuelva 404 con mensaje de elevar al admin."""
        response = self.client.post('/api/login/', {
            'email': 'fantasma@inacap.cl',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("eleve una solicitud a Administración", response.data['mensaje'])

    def test_login_usuario_exitoso_y_token(self):
        """Verifica que un usuario existente reciba su Token DRF y rol."""
        response = self.client.post('/api/login/', {
            'email': 'profe@inacap.cl',
            'password': 'password123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['rol'], 'PROFESOR')

    def test_creacion_sala_solo_por_admin(self):
        """Un alumno no puede crear salas (403), solo el Administrador (201)."""
        # Login como Alumno
        login_res = self.client.post('/api/login/', {'email': 'alumno@inacap.cl', 'password': 'password123'})
        token_alumno = login_res.data['token']

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_alumno)
        res_fallida = self.client.post('/api/salas/', {
            'nombre': 'Sala 202', 'codigo': 'S-202', 'capacidad_maxima': 15, 'disponible': True
        })
        self.assertEqual(res_fallida.status_code, status.HTTP_403_FORBIDDEN)

        # Login como Admin
        login_res = self.client.post('/api/login/', {'email': 'admin@inacap.cl', 'password': 'password123'})
        token_admin = login_res.data['token']

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_admin)
        res_exitosa = self.client.post('/api/salas/', {
            'nombre': 'Sala 202', 'codigo': 'S-202', 'capacidad_maxima': 15, 'disponible': True
        })
        self.assertEqual(res_exitosa.status_code, status.HTTP_201_CREATED)

    def test_creacion_usuario_solo_por_admin(self):
        """Un docente no puede enrolar usuarios (403), solo el Admin (201)."""
        # Docente intenta enrolar
        login_res = self.client.post('/api/login/', {'email': 'profe@inacap.cl', 'password': 'password123'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_res.data['token'])
        res_fallida = self.client.post('/api/usuarios/', {
            'nombre_completo': 'Nuevo Alumno', 'email': 'nuevo@inacap.cl', 'rut': '5-5', 'rol': 'ALUMNO'
        })
        self.assertEqual(res_fallida.status_code, status.HTTP_403_FORBIDDEN)

        # Admin enrola
        login_res = self.client.post('/api/login/', {'email': 'admin@inacap.cl', 'password': 'password123'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_res.data['token'])
        res_exitosa = self.client.post('/api/usuarios/', {
            'nombre_completo': 'Nuevo Alumno', 'email': 'nuevo@inacap.cl', 'rut': '5-5', 'rol': 'ALUMNO'
        })
        self.assertEqual(res_exitosa.status_code, status.HTTP_201_CREATED)

    def test_flujo_solicitud_y_aprobacion_taller(self):
        """Docente solicita taller (estado='solicitado'), Jefatura lo aprueba y pasa a 'aprobado'."""
        # 1. Docente solicita taller
        login_res = self.client.post('/api/login/', {'email': 'profe@inacap.cl', 'password': 'password123'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_res.data['token'])

        res_taller = self.client.post('/api/talleres/', {
            'nombre': 'Taller de Python Avanzado',
            'descripcion': 'Backend con Django REST Framework',
            'cupo_maximo': 25,
            'fecha_inicio': '2026-11-01T10:00:00Z',
            'sala': self.sala.id
        })
        self.assertEqual(res_taller.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_taller.data['estado'], 'solicitado')
        taller_id = res_taller.data['id']

        # 2. Alumno intenta aprobar (403)
        login_alumno = self.client.post('/api/login/', {'email': 'alumno@inacap.cl', 'password': 'password123'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_alumno.data['token'])
        res_aprobar_alumno = self.client.post(f'/api/talleres/{taller_id}/aprobar/')
        self.assertEqual(res_aprobar_alumno.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Jefatura aprueba el taller (200)
        login_jefe = self.client.post('/api/login/', {'email': 'jefe@inacap.cl', 'password': 'password123'})
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_jefe.data['token'])
        res_aprobar_jefe = self.client.post(f'/api/talleres/{taller_id}/aprobar/')
        self.assertEqual(res_aprobar_jefe.status_code, status.HTTP_200_OK)
        self.assertEqual(res_aprobar_jefe.data['taller']['estado'], 'aprobado')

        # 4. Alumno se inscribe exitosamente ahora que está aprobado
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + login_alumno.data['token'])
        res_inscribir = self.client.post('/api/inscripciones/', {
            'taller': taller_id
        })
        self.assertEqual(res_inscribir.status_code, status.HTTP_201_CREATED)
