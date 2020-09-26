"""
Common django-rest-framework permissions used throughout the service
"""
from rest_framework import permissions
from rest_framework.request import Request


class IsAuthenticated(permissions.BasePermission):
    """
    Rejects all operations if the user is not authenticated
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated


class IsModeratorOrStaff(permissions.BasePermission):
    """
    Blocks update/partial_updated/destroy if:
    * the user is NOT in the staff group
    * AND the user is NOT in a group called 'Moderators' group
    Everything else is allowed
    """

    def has_object_permission(self, request: Request, view, obj):
        if request.user.is_staff:
            return True
        if (
            view.action == "update"
            or view.action == "partial_update"
            or view.action == "destroy"
        ):
            return request.user.groups.filter(name="Moderators").exists()
        return True


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Blocks update/partial_updated/destroy if:
    * the user is NOT in the staff group
    * AND if the model has a property called 'owner' and its value differs from the request user
    Everything else is allowed
    """

    def has_object_permission(self, request: Request, view, obj):
        if request.user.is_staff:
            return True
        if (
            view.action == "update"
            or view.action == "partial_update"
            or view.action == "destroy"
        ):
            return hasattr(obj, "owner") and obj.owner == request.user
        return True


class IsOwnerOrModeratorOrStaff(permissions.BasePermission):
    """
    Blocks update/partial_updated/destroy if:
    * the user is NOT in the staff group
    * AND if the model has a property called 'owner' and its value differs from the request user
    * AND if the user is not in the Moderators group
    Everything else is allowed
    """

    def has_object_permission(self, request: Request, view, obj):
        if (
            view.action != "update"
            and view.action != "partial_update"
            and view.action != "destroy"
        ):
            return True

        if request.user.is_staff:
            return True

        if request.user.groups.filter(name="Moderators").exists():
            return True

        if hasattr(obj, "owner") and obj.owner == request.user:
            return True

        return False
