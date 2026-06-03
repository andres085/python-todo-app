import factory
from apps.todos.models import Todo
from apps.users.tests.factories import UserFactory


class TodoFactory(factory.django.DjangoModelFactory):
    """
    Fábrica para crear todos de prueba.

    SubFactory crea un usuario nuevo si no se pasa uno explícitamente.
    Cuando en el test llamás TodoFactory(user=mi_usuario), no crea un nuevo usuario.
    """

    class Meta:
        model = Todo

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Todo {n}')
    description = 'Test description'
    completed = False
