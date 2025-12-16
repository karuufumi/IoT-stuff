from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from helper.jwt import decode_token
from dependencies.repositories import get_user_repository
from repository.UserRepositoryInterface import UserRepositoryInterface
from model.model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepositoryInterface = Depends(get_user_repository),
) -> User:
    try:
        payload = decode_token(token)

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    user = await user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user