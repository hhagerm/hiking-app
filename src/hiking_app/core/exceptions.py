class NotAuthenticated(Exception):
    pass

# service
class ValidationFailed(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class InvalidCredentials(Exception):
    pass

# repos
class EmailTaken(Exception):
    pass
class UsernameTaken(Exception):
    pass