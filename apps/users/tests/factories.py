import factory
from django.contrib.auth.models import User


class UserFactory(factory.django.DjangoModelFactory):
    """
    Fábrica para crear usuarios de prueba.

    factory.Sequence garantiza username únicos entre tests.
    LazyAttribute deriva el email del username para evitar colisiones.
    @factory.post_generation hashea la contraseña DESPUÉS de hacer INSERT y
    llama save() explícitamente. skip_postgeneration_save=True evita el doble
    save() que factory-boy hacía por defecto (deprecado en v4).
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.set_password(extracted or 'TestPass123!')
        obj.save()
