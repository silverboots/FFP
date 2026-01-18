from sqlalchemy import select
import bcrypt
import hashlib
import secrets
from database.db import SessionLocal, engine, Base
from database.models import User
from database.lookup_helpers import get_current_gameweek
from database.sync_helpers import sync_single_user_players
from fplapi.fpl_services import fetch_fpl_team, FPLError


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

        # Create user
        user = User(email=email, password_hash=hash_password(password), name=name, team_id=team_id)
        db.add(user)
        db.commit()

        # Fetch and sync user's team picks (best effort - user still created if this fails)
        try:
            gameweek = get_current_gameweek()
            if gameweek:
                team_data = fetch_fpl_team(team_id, gameweek)
                sync_single_user_players(db, team_id, team_data["picks"])
        except FPLError:
            pass  # Team sync will happen when batch runs (e.g., GW1 before team is set)


def authenticate(email: str, password: str) -> User | None:
    email = email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user


def generate_session_token(email: str) -> str:
    """Generate a secure session token for the user."""
    random_bytes = secrets.token_bytes(32)
    data = f"{email}{random_bytes.hex()}"
    return hashlib.sha256(data.encode()).hexdigest()


def get_user_by_email(email: str) -> User | None:
    """Retrieve user by email."""
    with SessionLocal() as db:
        return db.scalar(select(User).where(User.email == email))