from pydantic import AliasChoices, BaseModel, Field


class PasswordHashRequest(BaseModel):
    password: str


class PasswordHashResponse(BaseModel):
    password_hash: str


class CreateUserRequest(BaseModel):
    user: str
    password: str = Field(validation_alias=AliasChoices("password", "passwor"))
    setor: str


class CreateUserResponse(BaseModel):
    id: int
    user: str
    setor: str
