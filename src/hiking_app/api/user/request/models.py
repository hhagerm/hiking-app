from pydantic import BaseModel

class RegisterUserRequest(BaseModel):
    email: str
    username: str
    password1: str
    password2: str