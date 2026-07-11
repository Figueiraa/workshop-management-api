from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.application.dtos.auth_dtos import RegisterUserInput
from app.application.use_cases.auth import AuthenticateUserUseCase, RegisterUserUseCase
from app.domain.entities.user import User
from app.infrastructure.database import get_db
from app.infrastructure.persistence.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.security import PasswordHasher, TokenIssuer
from app.interfaces.http.dependencies import get_current_user
from app.interfaces.http.schemas.auth_schema import TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    use_case = RegisterUserUseCase(SqlAlchemyUserRepository(db), PasswordHasher())
    return await use_case.execute(RegisterUserInput(**data.model_dump()))


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    use_case = AuthenticateUserUseCase(SqlAlchemyUserRepository(db), PasswordHasher(), TokenIssuer())
    token = await use_case.execute(form.username, form.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
