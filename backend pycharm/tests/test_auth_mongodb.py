import os
import sys
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.api.v1.endpoints import auth
from app.schemas.auth_dto import LoginRequest, SignupRequest


class FakeUsersCollection:
    def __init__(self):
        self.documents = []

    def find_one(self, query):
        if "_id" in query:
            return next(
                (document for document in self.documents if document["_id"] == query["_id"]),
                None,
            )

        for document in self.documents:
            if any(
                document.get(field) == value
                for condition in query["$or"]
                for field, value in condition.items()
            ):
                return document
        return None


    def insert_one(self, document):
        if self.find_one({"$or": [{"username": document["username"]}]}) or self.find_one({
            "$or": [{"email": document["email"]}]
        }):
            raise DuplicateKeyError("duplicate key")
        self.documents.append(document)


def test_signup_login_and_profile_use_mongodb_users(monkeypatch):
    users = FakeUsersCollection()
    monkeypatch.setattr(auth, "get_auth_users_collection", lambda: users)

    signup_response = auth.signup(SignupRequest(
        username="  TeacherOne ",
        email="TEACHER@example.com",
        password="secure-pass-123",
        confirm_password="secure-pass-123",
    ))

    assert signup_response.user.username == "teacherone"
    assert signup_response.user.email == "teacher@example.com"
    assert signup_response.user.created_at.tzinfo is not None
    assert users.documents[0]["password_hash"] != "secure-pass-123"
    assert isinstance(users.documents[0]["created_at"], datetime)
    assert users.documents[0]["created_at"].tzinfo == timezone.utc

    login_response = auth.login(LoginRequest(
        username="TEACHER@example.com",
        password="secure-pass-123",
    ))

    assert login_response.user.id == signup_response.user.id

    profile = auth.get_current_user(
        authorization=f"Bearer {login_response.access_token}"
    )
    assert profile.id == signup_response.user.id
    assert profile.email == "teacher@example.com"


def test_signup_rejects_duplicate_username(monkeypatch):
    users = FakeUsersCollection()
    monkeypatch.setattr(auth, "get_auth_users_collection", lambda: users)
    auth.signup(SignupRequest(
        username="teacher",
        email="teacher@example.com",
        password="secure-pass-123",
        confirm_password="secure-pass-123",
    ))

    with pytest.raises(HTTPException) as exc_info:
        auth.signup(SignupRequest(
            username="TEACHER",
            email="another@example.com",
            password="secure-pass-123",
            confirm_password="secure-pass-123",
        ))

    assert exc_info.value.status_code == 400
    assert "username already exists" in exc_info.value.detail
