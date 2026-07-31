"""
Custom DRF permission classes.
"""

from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    
    Checks the custom role field, not Django's is_staff.
    """
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to the object owner or admin users.
    
    Expects the object to have a 'user', 'owner', or 'seller' field.
    """
    message = 'You do not have permission to perform this action.'

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True

        # Check common owner field names
        for field in ['user', 'owner', 'seller', 'bidder']:
            owner = getattr(obj, field, None)
            if owner and owner == request.user:
                return True

        return False
