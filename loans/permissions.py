from rest_framework.permissions import BasePermission


class IsOfficer(BasePermission):
    message = 'Only officers can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_officer())


class IsCustomer(BasePermission):
    message = 'Only customers can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'customer')