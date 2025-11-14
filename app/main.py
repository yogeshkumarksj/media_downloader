import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from http import HTTPStatus
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
import yt_dlp
import traceback


# ==========================
#  FULL YOUTUBE COOKIE TEXT
# ==========================
YOUTUBE_COOKIE_TEXT = """
# Netscape HTTP Cookie File
# http://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file!  Do not edit.

.youtube.com	TRUE	/	FALSE	1797335911	HSID	A4Qg7gnSQ6VsmSwAR
.youtube.com	TRUE	/	TRUE	1797335911	SSID	AzK9_LWJPp46KiXR8
.youtube.com	TRUE	/	FALSE	1797335911	APISID	S6_z30224ajUOUrn/ACEJVOiStb8uFEQ6i
.youtube.com	TRUE	/	TRUE	1797335911	SAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	TRUE	1797335911	__Secure-1PAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	TRUE	1797335911	__Secure-3PAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	FALSE	1797335911	SID	g.a0003Qi2f26WBp2Udqb-BcHxMvW1NuQdqX4bdj52opy16EesgS2nLUhHAWd17QRD6f2oYQVLYAACgYKAcESARESFQHGX2Mifwi1j5ZMlbdBpzmSNTbowhoVAUF8yKrUnnyEMCFjRKqQW0i_Wgu90076
.youtube.com	TRUE	/	TRUE	1797335911	__Secure-1PSID	g.a0003Qi2f26WBp2Udqb-BcHxMvW1NuQdqX4bdj52opy16EesgS2nqkz-BIUTC3GPBUAyUtGIwgACgYKAaMSARESFQHGX2MiC8Rk_bMBniY_NQH-q7houxoVAUF8yKoR0mlApZB0C3lUL_yMarOt0076
.youtube.com	TRUE	/	TRUE	1797335911	__Secure-3PSID	g.a0003Qi2f26WBp2Udqb-BcHxMvW1NuQdqX4bdj52opy16EesgS2nWS0RLiyD2sbuMlOXi5Gi3gACgYKAc8SARESFQHGX2Mi67H4O6SJhZ8FspLJhqR0TRoVAUF8yKrHFGBbdMXvrhN3fZRdyIIq0076
"""

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# ================
# CREATE COOKIE FILE
# ================
COOKIE_PATH = "/app/cookies/cookie_youtube.txt"
os.makedirs("/app/cookies", exist_ok=True)

with open(COOKIE_PATH, "w", encoding="utf-8") as f:
    f.write(YOUTUBE_COOKIE_TEXT)


# Telegram App
ptb_app = Application.builder().token(BOT_TOKEN).build()


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send any video link (YouTube, Instagram, TikTok, Facebook).")


# Handle URL
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    ydl_opts_meta = {
        "quiet": True,
        "skip_download": True,
        "cookies": COOKIE_PATH,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        },
        "extractor_args": {"youtube": {"player_client": ["web", "android"]}},
    }

    try:
        ydl = yt_dlp.YoutubeDL(ydl_opts_meta)
        info = ydl.extract_info(url, download=False)
    except Exception:
        logging.error("Metadata ERROR:\n" + traceback.format_exc())
        await update.message.reply_text("❌ Unable to fetch video details. Try another link.")
        return

    title = info.get("title", "No Title")
    thumbnail = info.get("thumbnail")
    platform = info.get("extractor_key", "Unknown")

    context.user_data["url"] = url

    await update.message.reply_photo(
        photo=thumbnail,
        caption=f"📌 *{title}*\n🎬 Platform: {platform}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download MP4", callback_data="dl")]]),
        parse_mode="Markdown"
    )


# Download button
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data["url"]

    await query.edit_message_caption("⏳ Downloading… Please wait...")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": "/tmp/%(title)s.%(ext)s",
        "cookies": COOKIE_PATH,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            )
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, "rb") as f:
            await query.message.reply_video(video=f)

        os.remove(file_path)

    except Exception:
        logging.error("YT-DLP ERROR:\n" + traceback.format_exc())
        await query.message.reply_text("❌ Download failed. Try another link.")


# Webhook
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
ptb_app.add_handler(CallbackQueryHandler(button))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ptb_app.bot.set_webhook(WEBHOOK_URL)
    async with ptb_app:
        await ptb_app.start()
        yield
        await ptb_app.stop()


app = FastAPI(lifespan=lifespan)


@app.post(WEBHOOK_PATH)
async def webhook_handler(request: Request):
    update = Update.de_json(await request.json(), ptb_app.bot)
    await ptb_app.process_update(update)
    return Response(status_code=HTTPStatus.OK)


@app.get("/")
def home():
    return {"status": "Bot running"}
