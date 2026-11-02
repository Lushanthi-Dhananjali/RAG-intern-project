import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Header
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.db.mongo import get_auth_users_collection
from app.schemas.auth_dto import SignupRequest, LoginRequest, AuthResponse, UserResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

logger = logging.getLogger("AuthAPI")

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _user_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["_id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        created_at=user.get("created_at"),
    )


def _database_unavailable(exc: PyMongoError, operation: str) -> HTTPException:
    logger.error("MongoDB error during %s: %s", operation, exc)
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication database is currently unavailable. Please verify MongoDB is running.",
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration"
)
def signup(payload: SignupRequest):
    """
    Register a new user:
    - Validates passwords match
    - Checks for duplicate username or email
    - Securely hashes password with bcrypt
    - Persists the user to MongoDB
    - Returns JWT auth token and user profile
    """
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create Password and Confirm Password do not match."
        )

    clean_username = payload.username.strip().lower()
    clean_email = payload.email.strip().lower()

    try:
        users: Collection = get_auth_users_collection()
        existing_user = users.find_one({
            "$or": [
                {"username": clean_username},
                {"email": clean_email},
            ]
        })
    except PyMongoError as db_err:
        raise _database_unavailable(db_err, "signup lookup") from db_err

    if existing_user:
        if existing_user["username"] == clean_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this username already exists."
            )
        if existing_user["email"] == clean_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists."
            )

    hashed = hash_password(payload.password)
    new_user = {
        "_id": str(uuid.uuid4()),
        "username": clean_username,
        "email": clean_email,
        "password_hash": hashed,
        "full_name": payload.username.strip(),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        users.insert_one(new_user)
    except DuplicateKeyError as save_err:
        try:
            existing_user = users.find_one({
                "$or": [
                    {"username": clean_username},
                    {"email": clean_email},
                ]
            })
        except PyMongoError as db_err:
            raise _database_unavailable(db_err, "signup duplicate check") from db_err

        if existing_user and existing_user["username"] == clean_username:
            detail = "A user with this username already exists."
        elif existing_user and existing_user["email"] == clean_email:
            detail = "A user with this email address already exists."
        else:
            logger.error("MongoDB rejected signup due to a duplicate key: %s", save_err)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with these details already exists.",
            ) from save_err
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        ) from save_err
    except PyMongoError as save_err:
        raise _database_unavailable(save_err, "signup save") from save_err

    logger.info("New user registered successfully: %s (%s)", clean_username, clean_email)

    token = create_access_token(
        data={"sub": new_user["_id"], "username": clean_username, "email": clean_email}
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_user_response(new_user),
        message="Registration successful! Welcome to Lesson Planner."
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login"
)
def login(payload: LoginRequest):
    """
    Authenticate a user:
    - Accepts username or email
    - Verifies bcrypt hashed password
    - Issues JWT access token upon successful verification
    """
    identifier = payload.username.strip().lower()

    try:
        users: Collection = get_auth_users_collection()
        user = users.find_one({
            "$or": [
                {"username": identifier},
                {"email": identifier},
            ]
        })
    except PyMongoError as db_err:
        raise _database_unavailable(db_err, "login lookup") from db_err

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    token = create_access_token(
        data={"sub": user["_id"], "username": user["username"], "email": user["email"]}
    )

    logger.info("User logged in successfully: %s", user["username"])

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=_user_response(user),
        message="Login successful."
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile"
)
def get_current_user(
    authorization: Optional[str] = Header(None),
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

    try:
        users: Collection = get_auth_users_collection()
        user = users.find_one({"_id": payload["sub"]})
    except PyMongoError as db_err:
        raise _database_unavailable(db_err, "profile lookup") from db_err

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return _user_response(user)


@router.get(
    "/db-status",
    summary="Database Connectivity Check"
)
def check_db_status():
    """
    Verifies MongoDB connectivity and reports the number of registered users.
    """
    try:
        users: Collection = get_auth_users_collection()
        users.database.client.admin.command("ping")
        user_count = users.count_documents({})

        return {
            "status": "connected",
            "dialect": "mongodb",
            "database_url_type": "mongodb",
            "registered_users": user_count,
            "message": "Successfully connected to MongoDB authentication database."
        }
    except PyMongoError as exc:
        logger.error("Database connection check failed: %s", exc)
        return {
            "status": "error",
            "error": "MongoDB connection failed.",
            "message": "Could not connect to MongoDB. Please check MONGODB_URI in the backend .env file."
        }
