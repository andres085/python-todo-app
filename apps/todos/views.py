from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer

from apps.todos.models import Todo
from apps.todos.serializers import TodoSerializer
from core.permissions import IsOwner
from core.responses import ApiResponse


# ── Inline serializers para las respuestas envueltas en ApiResponse ───────────

_todo_response = inline_serializer(
    name='TodoResponse',
    fields={
        'success': serializers.BooleanField(),
        'data': TodoSerializer(),
    },
)

_todo_list_response = inline_serializer(
    name='TodoListResponse',
    fields={
        'success': serializers.BooleanField(),
        'data': TodoSerializer(many=True),
    },
)


# ── ViewSet ───────────────────────────────────────────────────────────────────

@extend_schema_view(
    list=extend_schema(
        tags=['Todos'],
        summary='Listar tareas',
        description='Devuelve todas las tareas del usuario autenticado, ordenadas de más reciente a más antigua.',
        responses={200: _todo_list_response},
    ),
    create=extend_schema(
        tags=['Todos'],
        summary='Crear tarea',
        description='Crea una nueva tarea asociada al usuario autenticado. El campo `user` se asigna automáticamente.',
        request=TodoSerializer,
        responses={201: _todo_response},
    ),
    retrieve=extend_schema(
        tags=['Todos'],
        summary='Obtener tarea',
        description='Devuelve una tarea por su `id`. Solo accesible si le pertenece al usuario autenticado.',
        responses={200: _todo_response},
    ),
    update=extend_schema(
        tags=['Todos'],
        summary='Actualizar tarea (completo)',
        description='Reemplaza todos los campos de la tarea. Todos los campos son requeridos.',
        request=TodoSerializer,
        responses={200: _todo_response},
    ),
    partial_update=extend_schema(
        tags=['Todos'],
        summary='Actualizar tarea (parcial)',
        description='Actualiza uno o más campos de la tarea sin necesidad de enviar todos. Ideal para togglear `completed`.',
        request=TodoSerializer,
        responses={200: _todo_response},
    ),
    destroy=extend_schema(
        tags=['Todos'],
        summary='Eliminar tarea',
        description='Elimina la tarea permanentemente. Devuelve 204 No Content sin cuerpo.',
        responses={204: None},
    ),
)
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
