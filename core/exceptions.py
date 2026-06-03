from django.http import Http404 as DjangoHttp404
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    NotAuthenticated,
    AuthenticationFailed,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    Throttled,
)


def custom_exception_handler(exc, context):
    """
    Reemplaza el exception handler por defecto de DRF para que todos los errores
    sigan el formato uniforme de la API:

        {"success": false, "error": {"code": "...", "message": "...", "details": {...}}}

    Se registra en settings.py:
        REST_FRAMEWORK = {'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler'}
    """
    response = exception_handler(exc, context)

    if response is None:
        return None

    error_code = 'server_error'
    message = 'An unexpected error occurred.'
    details = None

    if isinstance(exc, ValidationError):
        error_code = 'validation_error'
        message = 'Validation failed.'
        details = response.data

    elif isinstance(exc, NotAuthenticated):
        error_code = 'authentication_error'
        message = 'Authentication credentials were not provided.'

    elif isinstance(exc, AuthenticationFailed):
        error_code = 'authentication_failed'
        message = 'Invalid authentication credentials.'

    elif isinstance(exc, PermissionDenied):
        error_code = 'permission_denied'
        message = 'You do not have permission to perform this action.'

    elif isinstance(exc, (NotFound, DjangoHttp404)):
        error_code = 'not_found'
        message = 'The requested resource was not found.'

    elif isinstance(exc, MethodNotAllowed):
        error_code = 'method_not_allowed'
        message = f'Method "{exc.args[0]}" not allowed.'

    elif isinstance(exc, Throttled):
        error_code = 'throttled'
        message = 'Request was throttled. Try again later.'

    error_body = {'code': error_code, 'message': message}
    if details is not None:
        error_body['details'] = details

    response.data = {'success': False, 'error': error_body}
    return response
