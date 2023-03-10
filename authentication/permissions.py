from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from django.contrib.auth import get_user_model


class ReadOnly(BasePermission):
    def has_permission(self, request, _):
        return request.method in SAFE_METHODS


class IsOwner(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or {get_user_model(): self.owns_user}[
            type(obj)
        ](request, view, obj)

    def owns_user(self, request, _, user):
        return request.user == user
