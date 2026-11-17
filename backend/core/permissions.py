from rest_framework.permissions import SAFE_METHODS, BasePermission

from core.constants import ADMIN_ROLES, MANAGER_ROLES, ROLE_DENIED_MESSAGE


class HasRole(BasePermission):
    roles = ()
    message = ROLE_DENIED_MESSAGE

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in self.roles)


class IsAdminRole(HasRole):
    """SUPER_ADMIN ou ADMIN."""

    roles = ADMIN_ROLES


class IsManagerRole(HasRole):
    """SUPER_ADMIN, ADMIN ou MANAGER."""

    roles = MANAGER_ROLES


class ManagerWriteOnly(BasePermission):
    """Lecture : tout utilisateur authentifié. Écriture : managers et au-dessus."""

    message = ROLE_DENIED_MESSAGE

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in MANAGER_ROLES
