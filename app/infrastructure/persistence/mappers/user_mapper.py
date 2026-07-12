from app.domain.entities.user import User
from app.infrastructure.persistence.models.user_model import User as UserModel


def to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        is_active=model.is_active,
        created_at=model.created_at,
    )
