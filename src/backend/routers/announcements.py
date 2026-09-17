"""Announcement endpoints for the High School Management System API."""

from datetime import date, datetime, time, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..database import announcements_collection, teachers_collection
from .auth import active_sessions

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    start_date: Optional[date] = None
    expiration_date: date


def require_teacher(authorization: Optional[str]) -> None:
    token = authorization.removeprefix("Bearer ") if authorization else None
    username = active_sessions.get(token) if token else None
    if not username or not teachers_collection.find_one({"_id": username}):
        raise HTTPException(status_code=401, detail="Authentication required")


def announcement_dates(data: AnnouncementInput) -> tuple[Optional[datetime], datetime]:
    start_date = (
        datetime.combine(data.start_date, time.min, tzinfo=timezone.utc)
        if data.start_date
        else None
    )
    expiration_date = datetime.combine(
        data.expiration_date, time.max, tzinfo=timezone.utc
    )
    if start_date and start_date > expiration_date:
        raise HTTPException(
            status_code=400, detail="Start date must be on or before expiration date"
        )
    return start_date, expiration_date


def serialize_announcement(announcement: dict) -> dict:
    return {
        "id": str(announcement["_id"]),
        "message": announcement["message"],
        "start_date": (
            announcement["start_date"].date().isoformat()
            if announcement.get("start_date")
            else None
        ),
        "expiration_date": announcement["expiration_date"].date().isoformat(),
    }


def announcement_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail="Announcement not found")
    return ObjectId(value)


@router.get("")
@router.get("/")
def get_announcements(authorization: Optional[str] = Header(None)) -> list[dict]:
    """List active announcements publicly, or all announcements for a signed-in teacher."""
    query = {}
    if authorization:
        require_teacher(authorization)
    else:
        now = datetime.now(timezone.utc)
        query = {
            "expiration_date": {"$gte": now},
            "$or": [{"start_date": None}, {"start_date": {"$lte": now}}],
        }

    announcements = announcements_collection.find(query).sort("expiration_date", 1)
    return [serialize_announcement(item) for item in announcements]


@router.post("", status_code=201)
@router.post("/", status_code=201)
def create_announcement(
    data: AnnouncementInput, authorization: Optional[str] = Header(None)
) -> dict:
    """Create an announcement. Requires a signed-in teacher."""
    require_teacher(authorization)
    start_date, expiration_date = announcement_dates(data)
    document = {
        "message": data.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
    }
    if not document["message"]:
        raise HTTPException(status_code=400, detail="Message is required")
    result = announcements_collection.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_announcement(document)


@router.put("/{item_id}")
def update_announcement(
    item_id: str,
    data: AnnouncementInput,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Modify an announcement. Requires a signed-in teacher."""
    require_teacher(authorization)
    start_date, expiration_date = announcement_dates(data)
    document = {
        "message": data.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
    }
    if not document["message"]:
        raise HTTPException(status_code=400, detail="Message is required")
    result = announcements_collection.find_one_and_update(
        {"_id": announcement_id(item_id)}, {"$set": document}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return serialize_announcement(result)


@router.delete("/{item_id}", status_code=204)
def delete_announcement(
    item_id: str, authorization: Optional[str] = Header(None)
) -> None:
    """Delete an announcement. Requires a signed-in teacher."""
    require_teacher(authorization)
    result = announcements_collection.delete_one({"_id": announcement_id(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")