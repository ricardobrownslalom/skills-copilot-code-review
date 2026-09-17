"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import secrets

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

active_sessions: dict[str, str] = {}


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = username

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": session_token,
    }


@router.get("/check-session")
def check_session(session_token: str) -> Dict[str, Any]:
    """Check whether a login-issued session is valid."""
    username = active_sessions.get(session_token)
    teacher = teachers_collection.find_one({"_id": username}) if username else None

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"],
        "session_token": session_token,
    }


@router.post("/logout", status_code=204)
def logout(session_token: str) -> None:
    """Invalidate a login session."""
    active_sessions.pop(session_token, None)
