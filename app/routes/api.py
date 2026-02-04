from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import re

from app.database import get_db, Recommendation, BotSettings
from app.config import settings
from app.services import songlink
from app.services.telegram_bot import post_recommendation

router = APIRouter(prefix="/api")


class SubmissionRequest(BaseModel):
    name: str
    album_url: str
    context: str
    access_code: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name is required")
        return v.strip()

    @field_validator("album_url")
    @classmethod
    def valid_music_url(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Album URL is required")
        # Check for Spotify or Apple Music URL
        spotify_pattern = r"(open\.spotify\.com|spotify\.link)"
        apple_pattern = r"(music\.apple\.com|itunes\.apple\.com)"
        if not (re.search(spotify_pattern, v) or re.search(apple_pattern, v)):
            raise ValueError("Please provide a Spotify or Apple Music URL")
        return v

    @field_validator("context")
    @classmethod
    def context_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Context is required")
        return v.strip()


class SubmissionResponse(BaseModel):
    success: bool
    message: str
    album_title: str | None = None
    artist_name: str | None = None


class QueueItem(BaseModel):
    id: int
    submitter_name: str
    album_title: str | None
    artist_name: str | None
    submitted_at: str

    class Config:
        from_attributes = True


@router.post("/submit", response_model=SubmissionResponse)
async def submit_recommendation(request: SubmissionRequest, db: Session = Depends(get_db)):
    # Check access code
    if request.access_code != settings.ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid access code")

    try:
        # Get data from Songlink API
        link_data = await songlink.get_songlink_data(request.album_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch album data: {str(e)}")

    # Create recommendation
    recommendation = Recommendation(
        submitter_name=request.name,
        album_title=link_data.get("album_title"),
        artist_name=link_data.get("artist_name"),
        context=request.context,
        spotify_url=link_data.get("spotify_url"),
        apple_music_url=link_data.get("apple_music_url"),
        songlink_url=link_data.get("songlink_url"),
        album_art_url=link_data.get("album_art_url"),
    )

    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return SubmissionResponse(
        success=True,
        message="Recommendation submitted successfully!",
        album_title=recommendation.album_title,
        artist_name=recommendation.artist_name,
    )


@router.get("/queue", response_model=list[QueueItem])
async def get_queue(db: Session = Depends(get_db)):
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.is_posted == False)
        .order_by(Recommendation.submitted_at.asc())
        .all()
    )

    return [
        QueueItem(
            id=r.id,
            submitter_name=r.submitter_name,
            album_title=r.album_title,
            artist_name=r.artist_name,
            submitted_at=r.submitted_at.isoformat(),
        )
        for r in recommendations
    ]


@router.post("/trigger-post")
async def trigger_post():
    """Manually trigger a Telegram post (for testing)."""
    await post_recommendation()
    return {"success": True, "message": "Post triggered"}


class AdminLoginRequest(BaseModel):
    password: str


class AdminStatusResponse(BaseModel):
    is_paused: bool
    paused_at: str | None = None


class AdminActionRequest(BaseModel):
    password: str


@router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Verify admin password."""
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"success": True}


@router.get("/admin/status", response_model=AdminStatusResponse)
async def admin_status(db: Session = Depends(get_db)):
    """Get current bot status."""
    bot_settings = db.query(BotSettings).first()
    if not bot_settings:
        return AdminStatusResponse(is_paused=False, paused_at=None)
    return AdminStatusResponse(
        is_paused=bot_settings.is_paused,
        paused_at=bot_settings.paused_at.isoformat() if bot_settings.paused_at else None,
    )


@router.post("/admin/pause")
async def admin_pause(request: AdminActionRequest, db: Session = Depends(get_db)):
    """Pause the bot."""
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")

    bot_settings = db.query(BotSettings).first()
    if not bot_settings:
        bot_settings = BotSettings(is_paused=True, paused_at=datetime.utcnow())
        db.add(bot_settings)
    else:
        bot_settings.is_paused = True
        bot_settings.paused_at = datetime.utcnow()

    db.commit()
    return {"success": True, "message": "Bot paused"}


@router.post("/admin/resume")
async def admin_resume(request: AdminActionRequest, db: Session = Depends(get_db)):
    """Resume the bot."""
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")

    bot_settings = db.query(BotSettings).first()
    if not bot_settings:
        bot_settings = BotSettings(is_paused=False, paused_at=None)
        db.add(bot_settings)
    else:
        bot_settings.is_paused = False
        bot_settings.paused_at = None

    db.commit()
    return {"success": True, "message": "Bot resumed"}


class PostedAlbumItem(BaseModel):
    post_number: int
    album_title: str | None
    artist_name: str | None
    submitter_name: str
    posted_at: str
    spotify_url: str | None
    apple_music_url: str | None
    songlink_url: str | None

    class Config:
        from_attributes = True


@router.get("/admin/posted", response_model=list[PostedAlbumItem])
async def get_posted_albums(db: Session = Depends(get_db)):
    """Get list of all posted albums."""
    recommendations = (
        db.query(Recommendation)
        .filter(Recommendation.is_posted == True)
        .filter(Recommendation.post_number.isnot(None))
        .order_by(Recommendation.post_number.asc())
        .all()
    )

    return [
        PostedAlbumItem(
            post_number=r.post_number,
            album_title=r.album_title,
            artist_name=r.artist_name,
            submitter_name=r.submitter_name,
            posted_at=r.posted_at.isoformat() if r.posted_at else "",
            spotify_url=r.spotify_url,
            apple_music_url=r.apple_music_url,
            songlink_url=r.songlink_url,
        )
        for r in recommendations
    ]
