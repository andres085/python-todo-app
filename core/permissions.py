from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permiso a nivel de objeto: solo el dueño del recurso puede acceder.

    DRF llama a has_object_permission() DESPUÉS de has_permission() y solo
    en operaciones sobre un objeto individual (retrieve, update, destroy).
    Para list/create se filtra por usuario en get_queryset().
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
