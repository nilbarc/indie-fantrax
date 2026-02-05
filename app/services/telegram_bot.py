import logging
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from sqlalchemy import func

from app.config import settings
from app.database import SessionLocal, Recommendation, BotSettings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def get_bot() -> Bot:
    return Bot(token=settings.TELEGRAM_BOT_TOKEN)


def is_bot_paused() -> bool:
    """Check if the bot is currently paused."""
    db = SessionLocal()
    try:
        bot_settings = db.query(BotSettings).first()
        if bot_settings:
            return bot_settings.is_paused
        return False
    finally:
        db.close()


async def post_recommendation():
    """Post the oldest unposted recommendation to Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured, skipping post")
        return

    if is_bot_paused():
        logger.info("Bot is paused, skipping post")
        return

    db = SessionLocal()
    try:
        # Get a random unposted recommendation
        recommendation = (
            db.query(Recommendation)
            .filter(Recommendation.is_posted == False)
            .order_by(func.random())
            .first()
        )

        if not recommendation:
            logger.info("No pending recommendations to post")
            return

        # Calculate the next post number
        max_post_number = db.query(func.max(Recommendation.post_number)).scalar() or 0
        next_post_number = max_post_number + 1

        # Format the message
        message = format_recommendation_message(recommendation, next_post_number)

        # Send to Telegram
        bot = get_bot()

        if recommendation.album_art_url:
            # Send with album art
            sent_message = await bot.send_photo(
                chat_id=settings.TELEGRAM_CHAT_ID,
                photo=recommendation.album_art_url,
                caption=message,
                parse_mode=ParseMode.HTML,
            )
        else:
            # Send text only
            sent_message = await bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.HTML,
            )

        # Pin the message (disable_notification to avoid pinging everyone)
        await bot.pin_chat_message(
            chat_id=settings.TELEGRAM_CHAT_ID,
            message_id=sent_message.message_id,
            disable_notification=True,
        )

        # Mark as posted
        recommendation.is_posted = True
        recommendation.posted_at = datetime.utcnow()
        recommendation.post_number = next_post_number
        db.commit()

        logger.info(f"Posted recommendation #{next_post_number}: {recommendation.album_title} by {recommendation.artist_name}")

    except Exception as e:
        logger.error(f"Error posting recommendation: {e}")
        db.rollback()
    finally:
        db.close()


def format_recommendation_message(rec: Recommendation, post_number: int) -> str:
    """Format a recommendation for Telegram posting."""
    lines = [
        f"<b>Indie Fantrax Recommends - No. {post_number}</b>",
        "",
        f"🎵 <b>{rec.album_title or 'Unknown Album'}</b>",
        f"👤 {rec.artist_name or 'Unknown Artist'}",
        "",
        f"📝 Recommended by <b>{rec.submitter_name}</b>:",
        f"<i>{rec.context}</i>",
        "",
        "🔗 Listen:",
    ]

    if rec.spotify_url:
        lines.append(f"• <a href=\"{rec.spotify_url}\">Spotify</a>")
    if rec.apple_music_url:
        lines.append(f"• <a href=\"{rec.apple_music_url}\">Apple Music</a>")
    if rec.songlink_url:
        lines.append(f"• <a href=\"{rec.songlink_url}\">Other platforms</a>")

    return "\n".join(lines)


def start_scheduler():
    """Start the APScheduler for scheduled Telegram posts."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram bot token not set, scheduler not started")
        return

    tz = pytz.timezone(settings.TIMEZONE)

    # Schedule for Monday, Wednesday, Friday at 7am
    scheduler.add_job(
        post_recommendation,
        CronTrigger(day_of_week="mon,wed,fri", hour=7, minute=0, timezone=tz),
        id="post_recommendation",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"Scheduler started - posting Mon/Wed/Fri at 7am {settings.TIMEZONE}")


def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
