"""
Tests de integración para los endpoints de users.

"Integración" = levantamos el stack completo (router → view → serializer → DB)
y hacemos requests HTTP reales con APIClient. Verificamos respuestas HTTP.

force_authenticate() bypasea JWT para los tests — no queremos testear
que SimpleJWT funcione (es una librería externa), queremos testear NUESTRA lógica.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.factories import UserFactory

REGISTER_URL = '/api/auth/register/'
LOGIN_URL = '/api/auth/login/'
LOGOUT_URL = '/api/auth/logout/'
ME_URL = '/api/auth/me/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    """Cliente con autenticación forzada (sin necesidad de hacer login)."""
    api_client.force_authenticate(user=user)
    return api_client


# ─────────────────────────────────────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegisterView:

    def test_register_success(self, api_client):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = api_client.post(REGISTER_URL, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['username'] == 'alice'
        assert response.data['message'] == 'User created successfully.'

    def test_register_password_not_in_response(self, api_client):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = api_client.post(REGISTER_URL, data, format='json')
        assert 'password' not in response.data['data']

    def test_register_duplicate_username(self, api_client, user):
        data = {
            'username': user.username,
            'email': 'other@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = api_client.post(REGISTER_URL, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'validation_error'

    def test_register_duplicate_email(self, api_client, user):
        data = {
            'username': 'newuser',
            'email': user.email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        response = api_client.post(REGISTER_URL, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data['error']['details']

    def test_register_passwords_mismatch(self, api_client):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass!',
        }
        response = api_client.post(REGISTER_URL, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self, api_client):
        data = {
            'username': 'alice',
            'email': 'alice@example.com',
            'password': '123',
            'password_confirm': '123',
        }
        response = api_client.post(REGISTER_URL, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_field(self, api_client):
        response = api_client.post(REGISTER_URL, {'username': 'alice'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLoginView:

    def test_login_success_returns_tokens(self, api_client, user):
        response = api_client.post(
            LOGIN_URL,
            {'username': user.username, 'password': 'TestPass123!'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data['data']
        assert 'refresh' in response.data['data']
        assert response.data['data']['user']['username'] == user.username

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(
            LOGIN_URL,
            {'username': user.username, 'password': 'wrong'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'authentication_failed'

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(
            LOGIN_URL,
            {'username': 'nobody', 'password': 'SecurePass123!'},
            format='json',
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields(self, api_client):
        response = api_client.post(LOGIN_URL, {'username': 'alice'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# Logout
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutView:

    def test_logout_blacklists_refresh_token(self, auth_client, user):
        """El refresh token queda en la blacklist y no se puede volver a usar."""
        refresh = RefreshToken.for_user(user)
        response = auth_client.post(
            LOGOUT_URL,
            {'refresh': str(refresh)},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK

    def test_logout_missing_refresh(self, auth_client):
        response = auth_client.post(LOGOUT_URL, {}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_invalid_token(self, auth_client):
        response = auth_client.post(LOGOUT_URL, {'refresh': 'token-invalido'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_requires_authentication(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        response = api_client.post(LOGOUT_URL, {'refresh': str(refresh)}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# Me
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMeView:

    def test_me_returns_current_user(self, auth_client, user):
        response = auth_client.get(ME_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['username'] == user.username
        assert response.data['data']['email'] == user.email

    def test_me_unauthenticated_returns_401(self, api_client):
        response = api_client.get(ME_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'authentication_error'
