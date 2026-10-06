from rest_framework import permissions

# Solo el usuario con rol ADMIN o superusuario
class EsAdmin(permissions.BasePermission):
    message = "Solo el administrador puede realizar esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'usuario', None)
        return bool(perfil and perfil.rol == 'ADMIN' and perfil.activo)


# Cualquiera autenticado puede ver (GET), pero solo ADMIN puede crear, editar o borrar
class EsAdminOReadOnly(permissions.BasePermission):
    message = "Solo el administrador puede crear o modificar este recurso."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        # Metodos seguros son GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'usuario', None)
        return bool(perfil and perfil.rol == 'ADMIN' and perfil.activo)


# Solo Jefatura o Administrador
class EsJefatura(permissions.BasePermission):
    message = "Solo la jefatura o el administrador pueden realizar esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'usuario', None)
        return bool(perfil and perfil.rol in ['JEFE', 'ADMIN'] and perfil.activo)


# Solo Docentes o Administrador
class EsProfesor(permissions.BasePermission):
    message = "Solo los docentes pueden realizar esta acción."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        perfil = getattr(request.user, 'usuario', None)
        return bool(perfil and perfil.rol in ['PROFESOR', 'ADMIN'] and perfil.activo)
