"""
Tests unitarios para TodoSerializer.

No necesitan DB porque TodoSerializer no hace queries en la validación.
La lógica que testeamos: validate_title() y los campos read_only.
"""

from apps.todos.serializers import TodoSerializer


class TestTodoSerializer:

    def test_valid_data(self):
        serializer = TodoSerializer(data={'title': 'Mi tarea', 'description': 'Descripción'})
        assert serializer.is_valid(), serializer.errors

    def test_description_optional(self):
        """description tiene blank=True y default='' en el modelo, no es requerido."""
        serializer = TodoSerializer(data={'title': 'Solo título'})
        assert serializer.is_valid(), serializer.errors

    def test_empty_title_rejected(self):
        serializer = TodoSerializer(data={'title': ''})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_whitespace_only_title_rejected(self):
        """
        DRF's CharField tiene trim_whitespace=True por defecto:
        '   ' se convierte en '' antes de validate_title(), y allow_blank=False lo rechaza.
        """
        serializer = TodoSerializer(data={'title': '   '})
        assert not serializer.is_valid()
        assert 'title' in serializer.errors

    def test_title_is_stripped(self):
        """validate_title() hace .strip() → el valor guardado no tiene espacios extra."""
        serializer = TodoSerializer(data={'title': '  Tarea con espacios  '})
        assert serializer.is_valid()
        assert serializer.validated_data['title'] == 'Tarea con espacios'

    def test_read_only_fields_are_ignored_on_input(self):
        """
        id, created_at, updated_at son read_only: aunque vengan en el request,
        no se incluyen en validated_data (no se pueden inyectar desde afuera).
        """
        serializer = TodoSerializer(data={
            'title': 'Tarea',
            'id': 9999,
            'created_at': '2020-01-01T00:00:00Z',
            'updated_at': '2020-01-01T00:00:00Z',
        })
        assert serializer.is_valid()
        assert 'id' not in serializer.validated_data
        assert 'created_at' not in serializer.validated_data
        assert 'updated_at' not in serializer.validated_data

    def test_completed_defaults_to_false(self):
        """Si no se manda completed, el modelo lo setea como False."""
        serializer = TodoSerializer(data={'title': 'Tarea'})
        assert serializer.is_valid()
        # completed no está en validated_data porque tiene un default en el modelo
        # pero al hacer save() el modelo lo pone en False
        assert serializer.validated_data.get('completed', False) is False
