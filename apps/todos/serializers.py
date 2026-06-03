from rest_framework import serializers
from apps.todos.models import Todo


class TodoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Todo.

    Campos read_only:
    - id: asignado por la BD, el cliente no lo manda.
    - created_at / updated_at: manejados por Django (auto_now_add / auto_now).

    Campo ausente:
    - user: NO está en fields. Se asigna en la vista con serializer.save(user=request.user).
      Esto evita que el cliente pueda crear todos en nombre de otro usuario.
    """

    class Meta:
        model = Todo
        fields = ('id', 'title', 'description', 'completed', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_title(self, value):
        """
        Validación a nivel de campo: el título no puede estar vacío ni ser solo espacios.
        DRF llama automáticamente a validate_<nombre_del_campo>() antes de validate().
        """
        if not value.strip():
            raise serializers.ValidationError('Title cannot be empty or whitespace.')
        return value.strip()
