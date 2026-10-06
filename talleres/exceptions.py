from rest_framework.views import exception_handler
from rest_framework import status

# Manejo de errores global para dar respuestas claras
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Cuando falta el token o no es válido (error 401)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data = {
                'detail': 'Debes iniciar sesión con tu correo para acceder al sistema.',
                'mensaje': 'No has iniciado sesión. Ingresa en /api/login/ con tu correo para obtener tu token.'
            }

    return response
