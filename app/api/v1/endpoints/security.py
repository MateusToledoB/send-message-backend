from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.security_schema import (
    CreateUserRequest,
    CreateUserResponse,
    PasswordHashRequest,
    PasswordHashResponse,
)
from app.core.security import get_password_hash
from app.infra.db.db_client import db_client
from app.infra.db.models import User

router = APIRouter()


@router.post("/security/hash-password", response_model=PasswordHashResponse, status_code=status.HTTP_200_OK)
def hash_password(data: PasswordHashRequest):
    return PasswordHashResponse(password_hash=get_password_hash(data.password))


@router.post("/security/create", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: CreateUserRequest, session: Session = Depends(db_client.get_session)):
    existing_user = session.query(User).filter(User.name == data.user).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario ja existe")

    user = User(name=data.user, password=get_password_hash(data.password), setor=data.setor)
    session.add(user)
    session.commit()
    session.refresh(user)

    return CreateUserResponse(id=user.id, user=user.name, setor=user.setor)
