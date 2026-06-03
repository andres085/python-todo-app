from django.contrib.auth import authenticate
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.openapi import OpenApiTypes

from apps.users.serializers import RegisterSerializer, UserSerializer
from core.responses import ApiResponse


# ── Inline serializers para documentar las respuestas envueltas en ApiResponse ──
# drf-spectacular no puede inferir el shape de ApiResponse.success() automáticamente,
# así que lo describimos a mano una vez por endpoint.

_user_response = inline_serializer(
    name='UserResponse',
    fields={
        'success': serializers.BooleanField(),
        'data': UserSerializer(),
        'message': serializers.CharField(allow_null=True),
    },
)

_login_response = inline_serializer(
    name='LoginResponse',
    fields={
        'success': serializers.BooleanField(),
        'data': inline_serializer(
            name='LoginData',
            fields={
                'access': serializers.CharField(),
                'refresh': serializers.CharField(),
                'user': UserSerializer(),
            },
        ),
    },
)

_message_response = inline_serializer(
    name='MessageResponse',
    fields={
        'success': serializers.BooleanField(),
        'message': serializers.CharField(),
    },
)


# ── Vistas ────────────────────────────────────────────────────────────────────

@extend_schema(
    tags=['Auth'],
    summary='Registrar usuario',
    description=(
        'Crea una cuenta nueva. Requiere `username`, `email`, `password` y '
        '`password_confirm`. La contraseña debe tener al menos 8 caracteres '
        'y no ser demasiado común.'
    ),
    request=RegisterSerializer,
    responses={201: _user_response},
)
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return ApiResponse.success(
            data=UserSerializer(user).data,
            message='User created successfully.',
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=['Auth'],
    summary='Iniciar sesión',
    description=(
        'Autentica al usuario y devuelve un par de tokens JWT. '
        'Usá el `access` token en el header `Authorization: Bearer <access>` '
        'para las requests protegidas. Cuando expire (60 min), usá el `refresh` '
        'token en `/api/auth/refresh/` para obtener un nuevo par.'
    ),
    request=inline_serializer(
        name='LoginRequest',
        fields={
            'username': serializers.CharField(),
            'password': serializers.CharField(),
        },
    ),
    responses={200: _login_response},
)
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return ApiResponse.error(
                code='validation_error',
                message='username and password are required.',
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is None:
            return ApiResponse.error(
                code='authentication_failed',
                message='Invalid credentials.',
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return ApiResponse.success(data={
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


@extend_schema(
    tags=['Auth'],
    summary='Cerrar sesión',
    description=(
        'Invalida el `refresh` token agregándolo a la blacklist. '
        'Después de esto no se pueden obtener nuevos access tokens con ese refresh. '
        'El access token actual sigue siendo válido hasta que expire.'
    ),
    request=inline_serializer(
        name='LogoutRequest',
        fields={'refresh': serializers.CharField()},
    ),
    responses={200: _message_response},
)
class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return ApiResponse.error(
                code='validation_error',
                message='refresh token is required.',
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return ApiResponse.error(
                code='token_error',
                message=str(e),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return ApiResponse.success(message='Logged out successfully.')


@extend_schema(
    tags=['Auth'],
    summary='Perfil del usuario autenticado',
    description='Devuelve los datos del usuario dueño del token JWT enviado en el header.',
    responses={200: _user_response},
)
class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return ApiResponse.success(data=serializer.data)
