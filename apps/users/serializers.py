from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as dj_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.

    Puntos clave:
    - password y password_confirm son write_only: nunca aparecen en las respuestas.
    - validate_<field>() valida un campo individual antes de validate().
    - validate() valida relaciones entre campos (aquí: que las passwords coincidan).
    - create() llama a create_user() que hashea la password correctamente.
      Nunca guardar la password en texto plano con User(password=...).
    """

    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
        }

    def validate_email(self, value):
        """Valida que el email no esté registrado."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already in use.')
        return value

    def validate_password(self, value):
        """
        Aplica los validadores de contraseña configurados en AUTH_PASSWORD_VALIDATORS.
        Por defecto Django verifica: longitud mínima, no ser muy común, no ser solo
        números y no parecerse demasiado al username/email.
        """
        try:
            dj_validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        """Validación cruzada: password y password_confirm deben ser iguales."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )


class UserSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para exponer datos del usuario autenticado."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined')
        read_only_fields = ('id', 'date_joined')
