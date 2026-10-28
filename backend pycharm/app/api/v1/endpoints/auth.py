import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import or_, text

from app.db.session import get_db, engine
from app.models.user import User
from app.schemas.auth_dto import SignupRequest, LoginRequest, AuthResponse, UserResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

logger = logging.getLogger("AuthAPI")

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration"
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """
    Register a new user:
    - Validates passwords match
    - Checks for duplicate username or email
    - Securely hashes password with bcrypt
    - Persists user to database (MySQL)
    - Returns JWT auth token and user profile
    """
    # 1. Check passwords match
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create Password and Confirm Password do not match."
        )

    clean_username = payload.username.strip().lower()
    clean_email = payload.email.strip().lower()

    # 2. Check if username or email already registered
    try:
        existing_user = db.query(User).filter(
            or_(
                User.username.ilike(clean_username),
                User.email.ilike(clean_email)
            )
        ).first()
    except Exception as db_err:
        logger.error("Database connection error during signup: %s", db_err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is currently unavailable. Please verify MySQL is running."
        )

    if existing_user:
        if existing_user.username.lower() == clean_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists."
            )
        if existing_user.email.lower() == clean_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

    # 3. Hash password
    hashed = hash_password(payload.password)

    # 4. Create and persist user
    try:
        new_user = User(
            username=clean_username,
            email=clean_email,
            password_hash=hashed,
            full_name=payload.username.strip()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as save_err:
        db.rollback()
        logger.error("Failed to persist user: %s", save_err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user in database: {str(save_err)}"
        )

    logger.info("New user registered successfully: %s (%s)", new_user.username, new_user.email)

    # 5. Generate JWT token
    token = create_access_token(
        data={"sub": new_user.id, "username": new_user.username, "email": new_user.email}
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            created_at=new_user.created_at,
        ),
        message="Registration successful! Welcome to Lesson Planner."
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login"
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user:
    - Accepts username or email
    - Verifies bcrypt hashed password
    - Issues JWT access token upon successful verification
    """
    identifier = payload.username.strip().lower()

    try:
        user = db.query(User).filter(
            or_(
                User.username.ilike(identifier),
                User.email.ilike(identifier)
            )
        ).first()
    except Exception as db_err:
        logger.error("Database error during login: %s", db_err)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please verify MySQL is running."
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    token = create_access_token(
        data={"sub": user.id, "username": user.username, "email": user.email}
    )

    logger.info("User logged in successfully: %s", user.username)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
        ),
        message="Login successful."
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile"
)
def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Validates the bearer token and returns the current user profile.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header."
        )

    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired."
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        created_at=user.created_at,
    )


@router.get(
    "/db-status",
    summary="Database Connectivity Check"
)
def check_db_status(db: Session = Depends(get_db)):
    """
    Verifies database connection (MySQL / SQLite), driver, and table setup.
    """
    try:
        dialect_name = engine.dialect.name
        db.execute(text("SELECT 1"))
        user_count = db.query(User).count()

        return {
            "status": "connected",
            "dialect": dialect_name,
            "database_url_type": "mysql" if "mysql" in str(engine.url) else dialect_name,
            "registered_users": user_count,
            "message": f"Successfully connected to {dialect_name.upper()} database."
        }
    except Exception as exc:
        logger.error("Database connection check failed: %s", exc)
        return {
            "status": "error",
            "error": str(exc),
            "message": "Could not connect to database. Please check your credentials in .env."
        }
