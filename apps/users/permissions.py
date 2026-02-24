from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow Admin users.
    """
    def has_permission(self, request, view):
        try:
            return (
                request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'role') and
                request.user.role == 'Admin'
            )
        except Exception as e:
            print(f"IsAdmin permission error: {e}")
            return False


class IsDoctor(permissions.BasePermission):
    """
    Custom permission to only allow Doctor users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'Doctor'
        )


class IsNurse(permissions.BasePermission):
    """
    Custom permission to only allow Nurse users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'Nurse'
        )


class IsAdminOrDoctor(permissions.BasePermission):
    """
    Custom permission to allow Admin or Doctor users.
    """
    def has_permission(self, request, view):
        try:
            return (
                request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'role') and
                request.user.role in ['Admin', 'Doctor']
            )
        except Exception as e:
            print(f"IsAdminOrDoctor permission error: {e}")
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow Admin full access, others read-only.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and
            request.user.role == 'Admin'
        )
