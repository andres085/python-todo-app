from django.contrib.auth.models import User
from django.db import models


class Todo(models.Model):
    """
    Modelo principal de la app. Cada tarea pertenece a un usuario.

    Campos importantes:
    - user: ForeignKey con on_delete=CASCADE → si se elimina el usuario, se
      eliminan también todos sus todos. related_name='todos' permite hacer
      user.todos.all() para obtener todos los todos de un usuario.
    - auto_now_add=True en created_at: se setea una sola vez al crear el registro.
    - auto_now=True en updated_at: se actualiza automáticamente en cada save().
    - ordering en Meta: los todos se ordenan por defecto de más reciente a más antiguo.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.user.username}] {self.title}'
