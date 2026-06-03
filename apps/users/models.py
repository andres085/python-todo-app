# Usamos el User built-in de Django (django.contrib.auth.models.User).
# Sus campos son: id, username, email, password, first_name, last_name,
#                 is_active, is_staff, date_joined, last_login.
#
# Si en el futuro necesitás campos extra (avatar, bio, etc.), el patrón
# recomendado es agregar un modelo Profile con OneToOneField(User, ...).
