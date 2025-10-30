from rest_framework.permissions import IsAuthenticated


class canModifyPermission(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        userIsAuthenticated = super().has_object_permission(request, view, obj)
        return userIsAuthenticated and (
            request.user.is_landlord or request.user.is_superuser
        )
