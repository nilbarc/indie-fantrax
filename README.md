# Indie Fantrax

A music recommendation bot for group chats. Users submit album recommendations via a web form, and a bot posts them to Telegram on Monday/Wednesday/Friday at 7am.

## Features

- **Web Form**: Submit album recommendations with Spotify or Apple Music links
- **Link Conversion**: Automatically finds the album on both platforms using Songlink API
- **Scheduled Posts**: Bot posts to Telegram on Mon/Wed/Fri at 7am
- **Queue System**: View pending recommendations

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the prompts
3. Save the bot token you receive

### 2. Get Your Chat ID

1. Add your bot to your group chat
2. Send a message in the group
3. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Find the `chat.id` value (will be negative for groups)

### 3. Environment Variables

Set these environment variables (or create a `.env` file):

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/indie_fantrax
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ACCESS_CODE=your_secret_code
TIMEZONE=Europe/London
```

### 4. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to access the form.

## Deployment (Railway)

1. Create a new project on [Railway](https://railway.app)
2. Add a PostgreSQL database
3. Connect your GitHub repo or deploy manually
4. Set the environment variables in Railway
5. Railway will auto-detect the Procfile and deploy

## API Endpoints

- `GET /` - Submission form
- `POST /api/submit` - Submit a recommendation
- `GET /api/queue` - View pending recommendations
- `POST /api/trigger-post` - Manually trigger a Telegram post (for testing)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy
- **Scheduler**: APScheduler
- **Link Conversion**: Songlink/Odesli API
- **Frontend**: Vanilla HTML/CSS/JS
