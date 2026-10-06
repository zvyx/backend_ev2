# 📘 GUÍA MAESTRA DE INSTALACIÓN, CONFIGURACIÓN Y PRUEBAS
## Sistema de Gestión de Talleres Extracurriculares INACAP (Evaluación 3 - Back End)

Esta guía detalla paso a paso cómo clonar, configurar, restaurar la base de datos completa con todas las semillas y ejecutar tanto el portal web interactivo como la API REST y la suite de pruebas automatizadas.

---

## 1. Requisitos Previos

- **Python:** 3.10 o superior (verificado con Python 3.10+ y 3.14).
- **Git:** Instalado y configurado.
- **Sistema Operativo:** Windows, Linux o macOS.
- **Navegador Web:** Google Chrome, Firefox, Edge o Safari.
- **Cliente API (Opcional):** Postman, Insomnia, Thunder Client o cURL.

---

## 2. Clonación del Repositorio y Entorno Virtual

Abre tu terminal (PowerShell en Windows o Bash en Linux/Mac):

```powershell
# 1. Clonar el repositorio oficial
git clone https://github.com/zvyx/backend_ev2.git
cd backend_ev2

# 2. Crear el entorno virtual de Python
python -m venv venv_ev2

# 3. Activar el entorno virtual
# En Windows (PowerShell):
.\venv_ev2\Scripts\Activate.ps1
# En Linux/Mac:
# source venv_ev2/bin/activate

# 4. Instalar las dependencias del proyecto
pip install -r requirements.txt
```

---

## 3. Preparación y Restauración de la Base de Datos

El repositorio incluye el archivo maestro de semillas con todos los registros pre-cargados: [`datos_semilla.json`](file:///C:/Users/xvyz/Documents/workspace/backend_ev2/datos_semilla.json).

### Opción A: Usar la Base de Datos ya Poblada (`db.sqlite3`)
El repositorio ya contiene `db.sqlite3` listo para usar con los 29 usuarios, salas y talleres.

### Opción B: Reconstruir la Base de Datos desde Cero
Si deseas recrear la base de datos limpia e importar los datos de semilla:

```powershell
# 1. Eliminar base de datos previa (opcional si deseas reconstruir)
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue

# 2. Ejecutar las migraciones estructurales
python manage.py migrate

# 3. Cargar las semillas institucionales completas
python manage.py loaddata datos_semilla.json
```

---

## 4. Inventario Completo de Datos Poblados en la Base de Datos

> [!NOTE]
> **Contraseña universal para todas las cuentas del sistema:** `inacap123`

### 4.1. Cuentas de Acceso (Usuarios Poblados por Rol)

Puedes iniciar sesión indistintamente ingresando tu **RUT** o tu **Correo Electrónico**.

#### Administrador General (Rol: ADMIN)
| Nombre | RUT | Correo Electrónico | Privilegios Principales |
|---|---|---|---|
| Administrador General | `99999999-9` | `admin@inacap.cl` | Gestión total, creación de salas físicas, creación de usuarios y panel Django Admin (`/admin/`). |

#### Jefatura de Carrera (Rol: JEFE)
| Nombre | RUT | Correo Electrónico | Privilegios Principales |
|---|---|---|---|
| Eugenio Bravo | `11111116-1` | `eugenio.bravo@inacap.cl` | Revisión, aprobación y rechazo de talleres propuestos. |
| Hernán Valenzuela | `13101001-1` | `hernan.valenzuela@inacap.cl` | Revisión, aprobación y rechazo de talleres propuestos. |

#### Docentes / Profesores (Rol: PROFESOR)
| Nombre | RUT | Correo Electrónico | Talleres a Cargo |
|---|---|---|---|
| Roberto Morales | `12101001-1` | `roberto.morales@inacap.cl` | Desarrollo Web Fullstack, IA Aplicada |
| Edgar López | `11111115-1` | `edgar.lopez@inacap.cl` | Ciberseguridad Ofensiva, Taller Nivel 1 |
| Leo Rey | `11111117-1` | `brigido@inacap.cl` | Taller Extracurricular |
| Marcela Fuentes | `12101002-2` | `marcela.fuentes@inacap.cl` | IoT (Internet de las Cosas) |
| Rodrigo Soto | `12101003-3` | `rodrigo.soto@inacap.cl` | Bases de Datos Avanzadas y PostgreSQL |
| Patricia Castillo | `12101004-4` | `patricia.castillo@inacap.cl` | IA Aplicada a Negocios (Solicitado) |
| Gonzalo Vergara | `12101005-5` | `gonzalo.vergara@inacap.cl` | Hacking Ético en Redes (Solicitado) |
| Andrea Sepúlveda | `12101006-6` | `andrea.sepulveda@inacap.cl` | Taller de Robótica |
| Felipe Herrera | `12101007-7` | `felipe.herrera@inacap.cl` | Docente |
| Claudia Navas | `12101008-8` | `claudia.navas@inacap.cl` | Docente |
| Mauricio Carrasco | `12101009-9` | `mauricio.carrasco@inacap.cl` | Docente |
| Daniela Riquelme | `12101010-0` | `daniela.riquelme@inacap.cl` | Docente |

#### Estudiantes / Alumnos (Rol: ALUMNO)
| Nombre | RUT | Correo Electrónico |
|---|---|---|
| Matías Silva | `14101001-1` | `matias.silva@inacap.cl` |
| Valentina Castro | `14101002-2` | `valentina.castro@inacap.cl` |
| Nicolás Gómez | `14101003-3` | `nicolas.gomez@inacap.cl` |
| Sofía Araya | `14101004-4` | `sofia.araya@inacap.cl` |
| Lucas Espinoza | `14101005-5` | `lucas.espinoza@inacap.cl` |
| Martina Rojas | `14101006-6` | `martina.rojas@inacap.cl` |
| Benjamín Flores | `14101007-7` | `benjamin.flores@inacap.cl` |
| Isidora Vera | `14101008-8` | `isidora.vera@inacap.cl` |
| Tomás Pérez | `14101009-9` | `tomas.perez@inacap.cl` |
| Fernanda Muñoz | `14101010-0` | `fernanda.munoz@inacap.cl` |
| Camila Martínez | `11111111-1` | `camila.martinez@inacap.cl` |
| Liliana Arias | `11111112-1` | `liliana.arias@inacap.cl` |
| Johan Ortega | `11111113-1` | `johan.ortega@inacap.cl` |
| Cristian Romero | `11111114-1` | `cristian.romero@inacap.cl` |

---

### 4.2. Salas y Laboratorios Físicos Poblados
| Nombre | Código | Capacidad Máxima | Ubicación |
|---|---|---|---|
| Sala 102 | `sala102` | 10 | Primer piso |
| Sala 202 | `sala202` | 15 | Segundo piso |
| Sala 303 | `sala303` | 5 | Tercer piso |
| Laboratorio de Redes | `LAB-REDES-99` | 24 | Sala B |

---

## 5. Puesta en Marcha del Servidor Local

Ejecuta el servidor de desarrollo de Django:

```powershell
python manage.py runserver
```

El servidor quedará escuchando en: **`http://127.0.0.1:8000/`**

---

## 6. Demostración y Pruebas en el Portal Web

Abre tu navegador e ingresa a: **`http://127.0.0.1:8000/login/`**

### Caso A: Estudiante (`ALUMNO`)
1. **RUT:** `14101001-1` | **Contraseña:** `inacap123`.
2. Al ingresar, el estudiante entra al catálogo de talleres (`/talleres/`).
3. Ve todos los talleres disponibles con el cupo restante en tiempo real.
4. Puede hacer clic en **"Inscribirme en este Taller"**.
5. Su inscripción se registra de inmediato y aparece en la tabla superior con la opción de cancelar la inscripción si lo desea.

### Caso B: Docente (`PROFESOR`)
1. **RUT:** `12101001-1` | **Contraseña:** `inacap123`.
2. Al ingresar, visualiza su tabla **"Mis Talleres a Cargo"** con el número de alumnos inscritos y el estado actual de cada uno.
3. Presiona el botón destacado **"➕ Solicitar Creación de Taller"**.
4. Completa el formulario seleccionando una sala disponible y define el cupo máximo.
5. Al enviar, el taller se registra en estado `solicitado` esperando la aprobación de Jefatura.

### Caso C: Jefatura de Carrera (`JEFE`)
1. **RUT:** `11111116-1` | **Contraseña:** `inacap123`.
2. Al ingresar, ve la sección especial **"Talleres Pendientes de Revisión por Jefatura"**.
3. Puede presionar directamente **"Aprobar"** o **"Rechazar"**.
4. Al aprobarlo, el taller queda inmediatamente visible en el catálogo de alumnos para que puedan inscribirse.

### Cerrar Sesión
En la barra superior o en la tarjeta de perfil, presiona **"Cerrar Sesión"** (o navega a `/logout/`).

---

## 7. Ejecución de la Suite de Pruebas Automatizadas

El proyecto incluye dos baterías de pruebas automáticas:

### 7.1. Pruebas Unitarias de Django (Models, Serializers, Views y Permisos)
```powershell
python manage.py test talleres
```
**Resultado esperado:**
```text
Ran 6 tests in ~29s
OK
```

### 7.2. Script de Demostración 1 a 1 de la API REST en Vivo
Con el servidor corriendo en `http://127.0.0.1:8000/`:
```powershell
python test_live_api.py
```
**Resultado esperado:**
```text
=================================================================
  DEMOSTRACIÓN EN VIVO 1 A 1 - SERVIDOR ACTIVO EN 127.0.0.1:8000
=================================================================
[Prueba 1] GET /api/talleres/ (Sin token) -> 401 Unauthorized OK
[Prueba 2] POST /api/login/ (No registrado) -> 404 Not Found OK
[Prueba 3] POST /api/login/ (Admin) -> 200 OK + JWT Access
[Prueba 4] POST /api/salas/ (Admin) -> 201 Created OK
[Prueba 5] POST /api/login/ (Docente) -> 200 OK
[Prueba 6] POST /api/salas/ (Docente crea sala) -> 403 Forbidden OK
[Prueba 7] POST /api/talleres/ (Docente solicita) -> 201 Created (solicitado)
[Prueba 8] POST /api/login/ (Alumno) -> 200 OK
[Prueba 9] POST /api/talleres/13/aprobar/ (Alumno aprueba) -> 403 Forbidden OK
[Prueba 10] POST /api/login/ (Jefatura) -> 200 OK
[Prueba 11] POST /api/talleres/13/aprobar/ (Jefatura aprueba) -> 200 OK
[Prueba 12] POST /api/inscripciones/ (Alumno se inscribe) -> 201 Created OK
[Prueba 13] GET /api/talleres/?estado=aprobado -> 200 OK
=================================================================
  RESULTADO: TODAS LAS PRUEBAS EN VIVO FUERON EXITOSAS (13/13)
=================================================================
```

---

## 8. Contrato de la API REST y Autenticación JWT

Para clientes REST (Postman o aplicaciones frontend):

1. **Obtención del Token JWT:**
   - **URL:** `POST http://127.0.0.1:8000/api/login/`
   - **Body JSON:**
     ```json
     {
       "identificador": "12101001-1",
       "password": "inacap123"
     }
     ```
   - **Respuesta (200 OK):**
     ```json
     {
       "access": "eyJhbGciOiJIUzI1Ni...",
       "refresh": "eyJhbGciOiJIUzI1Ni...",
       "rol": "PROFESOR",
       "nombre_completo": "Roberto Morales"
     }
     ```

2. **Consumo de Endpoints Protegidos:**
   - **Cabecera HTTP requerida:**
     ```http
     Authorization: Bearer <access_token>
     Content-Type: application/json
     ```

3. **Renovación del Token:**
   - **URL:** `POST http://127.0.0.1:8000/api/token/refresh/`
   - **Body JSON:**
     ```json
     {
       "refresh": "<refresh_token>"
     }
     ```
