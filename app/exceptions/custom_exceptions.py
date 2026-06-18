class AppException(Exception):

    status_code = 400
    message = "Application Error"

    def __init__(self, message: str = None):
        if message:
            self.message = message


class NotFoundException(AppException):
    status_code = 404
    message = "Resource not found"


class AlreadyExistsException(AppException):
    status_code = 409
    message = "Resource already exists"


class BadRequestException(AppException):
    status_code = 400
    message = "Bad request"


class InvalidCredentialsException(AppException):
    status_code = 401
    message = "Invalid credentials"


class UnauthorizedException(AppException):
    status_code = 401
    message = "Not authenticated"
