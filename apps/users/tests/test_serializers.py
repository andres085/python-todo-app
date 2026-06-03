"""
Tests unitarios para los serializers de users.

"Unitario" = testeamos la lógica del serializer de forma aislada,
sin pasar por HTTP ni el router. Le pasamos datos directamente y verificamos
que valide/transforme correctamente.

Usamos @pytest.mark.django_db porque RegisterSerializer.validate_email()
hace una query (User.objects.filter(email=...)).
"""

import pytest
from apps.users.serializers import RegisterSerializer, UserSerializer
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestRegisterSerializer:

    def _valid_data(self, **overrides):
        """Helper: devuelve datos válidos de registro, con overrides opcionales."""
        return {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            **overrides,
        }

    def test_valid_data_creates_user(self):
        serializer = RegisterSerializer(data=self._valid_data())
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()
        assert user.pk is not None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'

    def test_password_is_hashed(self):
        """create_user() hashea la password; nunca se guarda en texto plano."""
        serializer = RegisterSerializer(data=self._valid_data())
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password('SecurePass123!')
        assert user.password != 'SecurePass123!'

    def test_passwords_do_not_match(self):
        data = self._valid_data(password_confirm='OtherPass999!')
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        # El error está en password_confirm (definido así en validate())
        assert 'password_confirm' in str(serializer.errors)

    def test_duplicate_email_rejected(self):
        UserFactory(email='taken@example.com')
        data = self._valid_data(username='other', email='taken@example.com')
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_weak_password_rejected(self):
        """Django's AUTH_PASSWORD_VALIDATORS rechaza passwords demasiado simples."""
        data = self._valid_data(password='123', password_confirm='123')
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_password_not_exposed_in_output(self):
        """
        Los campos write_only jamás aparecen en la representación del serializer.
        Crítico: nunca devolver passwords en las respuestas.
        """
        serializer = RegisterSerializer(data=self._valid_data())
        assert serializer.is_valid()
        user = serializer.save()
        output = RegisterSerializer(user).data
        assert 'password' not in output
        assert 'password_confirm' not in output

    def test_email_required(self):
        data = self._valid_data()
        del data['email']
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_password_confirm_required(self):
        data = self._valid_data()
        del data['password_confirm']
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()


class TestUserSerializer:
    """No necesita DB: solo verifica la estructura del serializer."""

    def test_fields_present(self, db):
        user = UserFactory()
        serializer = UserSerializer(user)
        assert set(serializer.data.keys()) == {'id', 'username', 'email', 'date_joined'}

    def test_password_not_in_fields(self, db):
        user = UserFactory()
        data = UserSerializer(user).data
        assert 'password' not in data
