from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RegisterUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    create_ts: datetime