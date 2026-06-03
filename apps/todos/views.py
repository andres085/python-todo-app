from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from apps.todos.models import Todo
from apps.todos.serializers import TodoSerializer
from core.permissions import IsOwner
from core.responses import ApiResponse


class TodoViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para el CRUD de todos.

    ModelViewSet provee automáticamente: list, create, retrieve, update,
    partial_update y destroy. Sobreescribimos cada acción solo para aplicar
    nuestro formato de respuesta uniforme (ApiResponse).

    Aislamiento de datos:
    - get_queryset() filtra por usuario → ningún usuario puede ver los todos de otro.
    - perform_create() inyecta request.user → el cliente no decide de quién es el todo.
    - IsOwner en permission_classes → en retrieve/update/destroy verifica que
      el todo pertenezca al usuario autenticado (por si alguien intenta /api/todos/999/).
    """

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = TodoSerializer

    def get_queryset(self):
        # SELECT * FROM todos_todo WHERE user_id = <usuario autenticado>
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Asigna el usuario autenticado al crear un todo.
        # El campo 'user' no viene del request body, se fuerza aquí.
        serializer.save(user=self.request.user)

    # ── Acciones ──────────────────────────────────────────────────────────────

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ApiResponse.success(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return ApiResponse.success(data=serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ApiResponse.success(data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return ApiResponse.success(data=serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # 204 No Content es el estándar HTTP para DELETE exitoso: no hay cuerpo.
        return ApiResponse.success(status=status.HTTP_204_NO_CONTENT)
