from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.users.serializers import RegisterSerializer, UserSerializer
from core.responses import ApiResponse


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Crea un nuevo usuario. No requiere autenticación (AllowAny).
    Devuelve los datos del usuario creado (sin password) con status 201.
    """

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


class LoginView(APIView):
    """
    POST /api/auth/login/

    Autentica al usuario y devuelve un par de tokens JWT:
    - access: token de corta duración (60 min) para hacer requests autenticadas.
    - refresh: token de larga duración (7 días) para obtener un nuevo access token.

    Usar: Authorization: Bearer <access_token>
    """

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


class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Invalida el refresh token añadiéndolo a la blacklist de SimpleJWT.
    Después de esto, ese refresh token no puede generar nuevos access tokens.
    El access token sigue siendo válido hasta que expire (por eso su vida es corta).
    """

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


class MeView(generics.RetrieveAPIView):
    """
    GET /api/auth/me/

    Devuelve el perfil del usuario autenticado.
    No recibe pk: get_object() retorna request.user directamente.
    """

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return ApiResponse.success(data=serializer.data)
