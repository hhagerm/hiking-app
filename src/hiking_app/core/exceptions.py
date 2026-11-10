class APIException(Exception):
    status_code = 500
    code = "internal_error"
    message = "internal server error"
    headers: dict[str, str] | None = None
    field: str | None = None


class NotAuthenticated(APIException):
    status_code = 401
    code = "not_authenticated"
    message = "not authenticated"


class InvalidCredentials(APIException):
    status_code = 401
    code = "invalid_credentials"
    message = "incorrect username or password"
    headers = {"WWW-Authenticate": "Bearer"}


class ValidationFailed(APIException):
    status_code = 422
    code = "validation_failed"

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)

class POINotFound(APIException):
    status_code = 404
    code = "poi_not_found"
    message = "poi not found"

class EmailTaken(Exception):
    pass
class UsernameTaken(Exception):
    pass
