# Guía Rápida de Despliegue y Pruebas - Evaluación 3
**Sistema Back End de Gestión de Talleres Extracurriculares (Django + DRF)**

Esta guía contiene todos los pasos necesarios para descargar el repositorio en un equipo limpio, preparar el entorno, levantar el servidor y realizar las pruebas en vivo para la presentación.

---

## 1. Descarga del Repositorio desde GitHub

Abre una terminal (PowerShell o Git Bash) y ejecuta:

```powershell
git clone https://github.com/zvyx/backend_ev2.git
cd backend_ev2
```

---

## 2. Creación y Activación del Entorno Virtual

Crea el entorno virtual con Python:

### En Windows (PowerShell):
```powershell
python -m venv venv_ev2
.\venv_ev2\Scripts\Activate.ps1
```
*(Si PowerShell bloquea scripts, ejecuta primero: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### En Windows (Símbolo del sistema / CMD):
```cmd
python -m venv venv_ev2
venv_ev2\Scripts\activate.bat
```

### En Linux / Mac:
```bash
python3 -m venv venv_ev2
source venv_ev2/bin/activate
```

---

## 3. Instalación de Dependencias

Con el entorno virtual activado, instala las librerías necesarias:

```powershell
pip install -r requirements.txt
```

*(Instala Django 6.1+, djangorestframework 3.18+ y complementos necesarios)*

---

## 4. Base de Datos y Datos Semilla

El repositorio ya incluye el archivo `db.sqlite3` listo y poblado. Sin embargo, para asegurar integridad ejecuta:

```powershell
python manage.py migrate
```

### 💡 Si necesitas resetear o recargar los datos de prueba:
El repositorio incluye el fixture `datos_semilla.json` con todos los 29 usuarios, salas y talleres:
```powershell
python manage.py loaddata datos_semilla.json
```

---

## 5. Ejecutar la Suite de Pruebas Automatizadas

Antes de iniciar la presentación frente al profesor, puedes demostrar que todo el sistema funciona al 100% ejecutando los tests unitarios:

```powershell
python manage.py test
```
**Resultado esperado:** `Ran 5 tests ... OK` (Valida permisos, tokens, bloqueo a no enrolados y flujo de talleres).

---

## 6. Levantar el Servicio en Vivo

Para iniciar el servidor de desarrollo en local:

```powershell
python manage.py runserver
```

El servicio quedará escuchando en:
> 🌐 **`http://127.0.0.1:8000/`**

La API navegable de DRF estará disponible en:
> 🌐 **`http://127.0.0.1:8000/api/`**

---

## 7. Cuentas de Prueba para la Demostración

**Contraseña unificada para todas las cuentas de prueba:** `inacap123`

| Rol | Nombre | Correo Electrónico (Login) | Contraseña |
| :--- | :--- | :--- | :---: |
| **ADMIN** | Administrador General | `admin@inacap.cl` | `inacap123` |
| **JEFE** | Hernán Valenzuela | `hernan.valenzuela@inacap.cl` | `inacap123` |
| **PROFESOR** | Roberto Morales | `roberto.morales@inacap.cl` | `inacap123` |
| **PROFESOR** | Marcela Fuentes | `marcela.fuentes@inacap.cl` | `inacap123` |
| **ALUMNO** | Matías Silva | `matias.silva@inacap.cl` | `inacap123` |
| **ALUMNO** | Valentina Castro | `valentina.castro@inacap.cl` | `inacap123` |
| **ALUMNO** | Nicolás Gómez | `nicolas.gomez@inacap.cl` | `inacap123` |
| **ALUMNO** | Sofía Araya | `sofia.araya@inacap.cl` | `inacap123` |

---

## 8. Guía de Pruebas 1 a 1 para la Defensa (Postman o Navegador)

### Paso 1: Intentar entrar sin Token (Seguridad 401)
* **Método:** `GET`
* **URL:** `http://127.0.0.1:8000/api/talleres/`
* **Cabeceras:** Ninguna
* **Respuesta esperada:** `401 Unauthorized`
  ```json
  {
    "detail": "Debes iniciar sesión con tu correo para acceder al sistema.",
    "mensaje": "No has iniciado sesión. Ingresa en /api/login/ con tu correo para obtener tu token."
  }
  ```

---

### Paso 2: Intentar login con correo no registrado (Control 404)
* **Método:** `POST`
* **URL:** `http://127.0.0.1:8000/api/login/`
* **Body (JSON):**
  ```json
  {
    "email": "persona.desconocida@inacap.cl",
    "password": "123"
  }
  ```
* **Respuesta esperada:** `404 Not Found`
  ```json
  {
    "error": "Usuario no enrolado",
    "mensaje": "El correo ingresado no se encuentra registrado en el sistema. Por favor, eleve una solicitud a Administración para ser enrolado."
  }
  ```

---

### Paso 3: Login de Administrador y Creación de Sala
1. **Login:** `POST http://127.0.0.1:8000/api/login/`
   ```json
   { "email": "admin@inacap.cl", "password": "inacap123" }
   ```
   * Copia el valor `"token"` devuelto en la respuesta.

2. **Crear Sala:** `POST http://127.0.0.1:8000/api/salas/`
   * **Headers:** `Authorization: Token <tu_token_de_admin>`
   * **Body (JSON):**
     ```json
     {
       "nombre": "Laboratorio Multimedia",
       "codigo": "LAB-MEDIA-01",
       "capacidad_maxima": 20,
       "ubicacion": "Edificio A",
       "disponible": true
     }
     ```
   * **Respuesta esperada:** `201 Created`

---

### Paso 4: Docente intenta crear Sala y luego propone Taller
1. **Login Docente:** `POST http://127.0.0.1:8000/api/login/`
   ```json
   { "email": "roberto.morales@inacap.cl", "password": "inacap123" }
   ```
   * Copia el `"token"` del docente.

2. **Docente intenta crear Sala:** `POST http://127.0.0.1:8000/api/salas/` con su token.
   * **Respuesta esperada:** `403 Forbidden` (`"Solo el administrador puede crear o modificar este recurso."`).

3. **Docente propone Taller:** `POST http://127.0.0.1:8000/api/talleres/`
   * **Headers:** `Authorization: Token <token_docente>`
   * **Body (JSON):**
     ```json
     {
       "nombre": "Taller de Desarrollo de Videojuegos",
       "descripcion": "Creación de prototipos con Godot Engine",
       "cupo_maximo": 3,
       "fecha_inicio": "2026-11-20T10:00:00Z",
       "sala": 1
     }
     ```
   * **Respuesta esperada:** `201 Created` con `"estado": "solicitado"`. Anota el `"id"` del taller generado.

---

### Paso 5: Alumno intenta aprobar (Bloqueo 403) y Jefatura aprueba
1. **Login Alumno:** `POST http://127.0.0.1:8000/api/login/` con `matias.silva@inacap.cl`.
2. **Alumno intenta aprobar:** `POST http://127.0.0.1:8000/api/talleres/<id_del_taller>/aprobar/`
   * **Respuesta esperada:** `403 Forbidden` (`"Solo la jefatura o el administrador pueden realizar esta acción."`).

3. **Login Jefatura:** `POST http://127.0.0.1:8000/api/login/`
   ```json
   { "email": "hernan.valenzuela@inacap.cl", "password": "inacap123" }
   ```
4. **Jefatura aprueba:** `POST http://127.0.0.1:8000/api/talleres/<id_del_taller>/aprobar/` con token de jefatura.
   * **Respuesta esperada:** `200 OK`
     ```json
     {
       "mensaje": "El taller '...' ha sido aprobado por la jefatura.",
       "taller": { "estado": "aprobado" }
     }
     ```

---

### Paso 6: Inscripción y Validación de Sobrecupo (Cupo = 3)
1. Inscribe con token al Alumno 1 (`matias.silva@inacap.cl`):
   * `POST http://127.0.0.1:8000/api/inscripciones/` con body `{"taller": <id_del_taller>}` $\rightarrow$ `201 Created`.
2. Inscribe al Alumno 2 (`valentina.castro@inacap.cl`) $\rightarrow$ `201 Created`.
3. Inscribe al Alumno 3 (`nicolas.gomez@inacap.cl`) $\rightarrow$ `201 Created` *(Cupo lleno: 3 de 3)*.
4. Intenta inscribir al Alumno 4 (`sofia.araya@inacap.cl`):
   * **Respuesta esperada:** `400 Bad Request`
     ```json
     {
       "taller": ["No quedan cupos disponibles para este taller (Máximo: 3)."]
     }
     ```

---

### Paso 7: Consultas ORM con Filtros (Catálogo y Búsqueda)
Con cualquier token de alumno autenticado:
* **Ver solo talleres aprobados:**
  `GET http://127.0.0.1:8000/api/talleres/?estado=aprobado`
* **Buscar taller por palabra clave:**
  `GET http://127.0.0.1:8000/api/talleres/?buscar=videojuegos`
* **Ver talleres de un profesor específico:**
  `GET http://127.0.0.1:8000/api/talleres/?profesor=1`
* **Ver alumnos inscritos en un taller:**
  `GET http://127.0.0.1:8000/api/talleres/<id>/inscripciones/`
