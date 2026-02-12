"""
Authentication API endpoints - SQLite-based user auth with JWT tokens
"""

import os
import sqlite3
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("auth_api")
router = APIRouter()

# Database path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "users.db")

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES


# ── Schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None


class UserProfile(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None


# ── Database helpers ─────────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    """Get a SQLite connection, creating the DB + table if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            salt        TEXT    NOT NULL,
            full_name   TEXT,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


def _hash_password(password: str, salt: str) -> str:
    """Hash a password with the given salt using SHA-256."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def _create_token(user_id: int, username: str) -> str:
    """Create a JWT token for the user."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Auth dependency ──────────────────────────────────────────────────

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Extract and validate the current user from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization format. Use: Bearer <token>")

    payload = _decode_token(parts[1])
    return {"user_id": payload["sub"], "username": payload["username"]}


# ── Endpoints ────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user."""
    conn = _get_db()
    try:
        # Check if username or email already exists
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (request.username, request.email),
        ).fetchone()

        if existing:
            raise HTTPException(status_code=409, detail="Username or email already exists")

        salt = secrets.token_hex(16)
        hashed = _hash_password(request.password, salt)
        now = datetime.utcnow().isoformat()

        cursor = conn.execute(
            "INSERT INTO users (username, email, password, salt, full_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (request.username, request.email, hashed, salt, request.full_name, now, now),
        )
        conn.commit()

        user_id = cursor.lastrowid
        token = _create_token(user_id, request.username)

        logger.info(f"User registered: {request.username}")

        return AuthResponse(
            success=True,
            message="Registration successful",
            token=token,
            user={"username": request.username, "email": request.email, "full_name": request.full_name},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")
    finally:
        conn.close()


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate a user and return a JWT token."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT id, username, email, password, salt, full_name FROM users WHERE username = ?",
            (request.username,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        hashed = _hash_password(request.password, row["salt"])
        if hashed != row["password"]:
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = _create_token(row["id"], row["username"])

        logger.info(f"User logged in: {request.username}")

        return AuthResponse(
            success=True,
            message="Login successful",
            token=token,
            user={"username": row["username"], "email": row["email"], "full_name": row["full_name"]},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")
    finally:
        conn.close()


@router.get("/me", response_model=AuthResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the current user profile (validates the token)."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT username, email, full_name FROM users WHERE id = ?",
            (current_user["user_id"],),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        return AuthResponse(
            success=True,
            message="Profile retrieved",
            user={"username": row["username"], "email": row["email"], "full_name": row["full_name"]},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")
    finally:
        conn.close()
