from sqlalchemy import select
import bcrypt
from database.db import SessionLocal, engine, Base
from database.models import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        bytes(password, encoding="utf-8"),
        bcrypt.gensalt(),
    ).decode()

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
            bytes(password, encoding="utf-8"),
            bytes(password_hash, encoding="utf-8"),
        )

def create_user(email: str, password: str, name: str, team_id: int) -> None:
    email = email.strip().lower()
    with SessionLocal() as db:
        exists = db.scalar(select(User).where(User.email == email))
        if exists:
            raise ValueError("Email already registered.")
        user = User(email=email, password_hash=hash_password(password), name=name, team_id=team_id)
        db.add(user)
        db.commit()

def authenticate(email: str, password: str) -> User | None:
    email = email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user