# controller/AuthController.py
from fastapi import APIRouter, Depends, HTTPException, status
from dependencies.auth import get_current_user
from model.model import Account, User
from service.AuthService import AuthService
from pydantic import BaseModel
from repository.UserRepositoryImpl import UserRepositoryImpl
from dependencies.repositories import get_user_repository

from helper.jwt import decode_token, create_access_token
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    account: Account,
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
):
    auth_service = AuthService(user_repo)
    try:
        user = await auth_service.register(account)
        return {"message": "User registered successfully", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(
    account: Account,
    user_repo: UserRepositoryImpl = Depends(get_user_repository),
):
    auth_service = AuthService(user_repo)
    try:
        return await auth_service.login(account)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return current_user

