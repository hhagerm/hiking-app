from email_validator import validate_email, EmailNotValidError
from argon2 import PasswordHasher

from hiking_app.db import UserRepository
from hiking_app.core.exceptions import ValidationFailed, EmailTaken, UsernameTaken

SPECIAL = "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~"
ph = PasswordHasher()

def _validate_password(password: str):
    if not 8 <= len(password) <= 64:
        raise ValidationFailed("password1", "must be between 8 and 64 characters")
    if not any(c.isupper() for c in password):
        raise ValidationFailed("password1", "must contain an uppercase letter")
    if not any(c.islower() for c in password):
        raise ValidationFailed("password1", "must contain a lowercase letter")
    if not any(c.isdigit() for c in password):
        raise ValidationFailed("password1", "must contain a digit")
    if not any(c in SPECIAL for c in password):
        raise ValidationFailed("password1", "must contain a special character")
    

class UserService():
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo
        
    async def register_account(
        self, 
        email: str, 
        username: str, 
        password1: str, 
        password2: str
        ):
        try:
            info = validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise ValidationFailed("email", str(e)) from e
        email = info.normalized.lower()
        
        _validate_password(password1)
  
        if password1 != password2:
            raise ValidationFailed("password2", "passwords do not match")
        
        if not 3 <= len(username) <= 32:
            raise ValidationFailed("username", "must be between 3 and 32 characters")
        
        hashed_password = ph.hash(password1)
        try:
            return await self.user_repo.add_user(email, username, hashed_password)
        except EmailTaken:
            raise ValidationFailed("email", "email already taken")
        except UsernameTaken:
            raise ValidationFailed("username", "username already taken")
        