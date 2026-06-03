from rest_framework.response import Response


class ApiResponse:
    """
    Centraliza el formato de todas las respuestas de la API.

    Success:
        {"success": true, "data": {...}, "message": "opcional"}

    Error:
        {"success": false, "error": {"code": "...", "message": "...", "details": {...}}}
    """

    @staticmethod
    def success(data=None, message=None, status=200):
        payload = {'success': True, 'data': data}
        if message:
            payload['message'] = message
        return Response(payload, status=status)

    @staticmethod
    def error(code, message, details=None, status=400):
        error = {'code': code, 'message': message}
        if details is not None:
            error['details'] = details
        return Response({'success': False, 'error': error}, status=status)
