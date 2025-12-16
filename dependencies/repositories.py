# dependencies/repositories.py
from repository.UserRepositoryImpl import UserRepositoryImpl

def get_user_repository() -> UserRepositoryImpl:
    return UserRepositoryImpl()