"""
Tests de integración para los endpoints de todos.

Cubren el comportamiento completo end-to-end:
  - Aislamiento de datos entre usuarios (cada usuario solo ve sus propios todos)
  - Permisos: autenticación requerida, no se puede operar sobre todos ajenos
  - CRUD completo: list, create, retrieve, update (PUT/PATCH), delete
  - Validaciones: título vacío, etc.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.todos.tests.factories import TodoFactory
from apps.users.tests.factories import UserFactory

TODOS_URL = '/api/todos/'


def todo_url(pk):
    return f'/api/todos/{pk}/'


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


# ─────────────────────────────────────────────────────────────────────────────
# List + Create
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTodoList:

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(TODOS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error']['code'] == 'authentication_error'

    def test_empty_list_for_new_user(self, auth_client):
        response = auth_client.get(TODOS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data'] == []

    def test_returns_only_own_todos(self, auth_client, user, other_user):
        """
        Clave de seguridad: get_queryset() filtra por usuario.
        Los todos de other_user NO deben aparecer en la lista de user.
        """
        TodoFactory(user=user, title='Mío 1')
        TodoFactory(user=user, title='Mío 2')
        TodoFactory(user=other_user, title='Ajeno')

        response = auth_client.get(TODOS_URL)
        assert response.status_code == status.HTTP_200_OK
        titles = [t['title'] for t in response.data['data']]
        assert len(titles) == 2
        assert 'Ajeno' not in titles

    def test_todos_ordered_newest_first(self, auth_client, user):
        """Meta.ordering = ['-created_at'] en el modelo."""
        todo1 = TodoFactory(user=user, title='Primero')
        todo2 = TodoFactory(user=user, title='Segundo')

        response = auth_client.get(TODOS_URL)
        titles = [t['title'] for t in response.data['data']]
        # El más reciente (todo2) aparece primero
        assert titles[0] == todo2.title

    def test_create_todo_success(self, auth_client):
        data = {'title': 'Nueva tarea', 'description': 'Con descripción'}
        response = auth_client.post(TODOS_URL, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['title'] == 'Nueva tarea'
        assert response.data['data']['completed'] is False

    def test_create_assigns_current_user(self, auth_client, user):
        """
        perform_create() inyecta request.user.
        El cliente no puede asignar un user_id diferente desde el body.
        """
        auth_client.post(TODOS_URL, {'title': 'Tarea'}, format='json')
        from apps.todos.models import Todo
        todo = Todo.objects.get(title='Tarea')
        assert todo.user == user

    def test_create_without_description(self, auth_client):
        response = auth_client.post(TODOS_URL, {'title': 'Sin desc'}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['description'] == ''

    def test_create_empty_title_returns_400(self, auth_client):
        response = auth_client.post(TODOS_URL, {'title': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error']['code'] == 'validation_error'
        assert 'title' in response.data['error']['details']

    def test_create_unauthenticated_returns_401(self, api_client):
        response = api_client.post(TODOS_URL, {'title': 'Test'}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ─────────────────────────────────────────────────────────────────────────────
# Retrieve
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTodoRetrieve:

    def test_retrieve_own_todo(self, auth_client, user):
        todo = TodoFactory(user=user, title='Mi tarea')
        response = auth_client.get(todo_url(todo.pk))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == 'Mi tarea'
        assert response.data['data']['id'] == todo.pk

    def test_retrieve_other_user_todo_returns_404(self, auth_client, other_user):
        """
        Por diseño, devolvemos 404 (not_found) y no 403 (permission_denied).
        Esto sigue el principio de no revelar si el recurso existe para otro usuario.
        """
        todo = TodoFactory(user=other_user)
        response = auth_client.get(todo_url(todo.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error']['code'] == 'not_found'

    def test_retrieve_nonexistent_todo(self, auth_client):
        response = auth_client.get(todo_url(99999))
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ─────────────────────────────────────────────────────────────────────────────
# Update (PUT / PATCH)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTodoUpdate:

    def test_patch_completed(self, auth_client, user):
        """PATCH: actualización parcial, solo los campos enviados se modifican."""
        todo = TodoFactory(user=user, completed=False)
        response = auth_client.patch(todo_url(todo.pk), {'completed': True}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['completed'] is True
        assert response.data['data']['title'] == todo.title  # no cambió

    def test_put_requires_all_fields(self, auth_client, user):
        """PUT: actualización completa; si falta un campo requerido, 400."""
        todo = TodoFactory(user=user)
        response = auth_client.put(todo_url(todo.pk), {'completed': True}, format='json')

        # title es requerido; sin él, PUT devuelve 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_put_success(self, auth_client, user):
        todo = TodoFactory(user=user)
        data = {'title': 'Título actualizado', 'description': 'Nueva desc', 'completed': True}
        response = auth_client.put(todo_url(todo.pk), data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == 'Título actualizado'
        assert response.data['data']['completed'] is True

    def test_cannot_update_other_user_todo(self, auth_client, other_user):
        todo = TodoFactory(user=other_user)
        response = auth_client.patch(todo_url(todo.pk), {'completed': True}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cannot_change_user_via_patch(self, auth_client, user, other_user):
        """
        El campo 'user' no está en los fields del serializer.
        Mandar user_id en el body no tiene efecto.
        """
        todo = TodoFactory(user=user)
        auth_client.patch(todo_url(todo.pk), {'user': other_user.pk}, format='json')

        from apps.todos.models import Todo
        todo.refresh_from_db()
        assert todo.user == user  # sigue siendo el mismo usuario


# ─────────────────────────────────────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTodoDelete:

    def test_delete_own_todo(self, auth_client, user):
        todo = TodoFactory(user=user)
        response = auth_client.delete(todo_url(todo.pk))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        from apps.todos.models import Todo
        assert not Todo.objects.filter(pk=todo.pk).exists()

    def test_cannot_delete_other_user_todo(self, auth_client, other_user):
        todo = TodoFactory(user=other_user)
        response = auth_client.delete(todo_url(todo.pk))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        from apps.todos.models import Todo
        assert Todo.objects.filter(pk=todo.pk).exists()  # no fue eliminado

    def test_delete_unauthenticated(self, api_client, user):
        todo = TodoFactory(user=user)
        response = api_client.delete(todo_url(todo.pk))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
