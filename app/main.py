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
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	FALSE	1797677347	HSID	A4Qg7gnSQ6VsmSwAR
.youtube.com	TRUE	/	TRUE	1797677347	SSID	AzK9_LWJPp46KiXR8
.youtube.com	TRUE	/	FALSE	1797677347	APISID	S6_z30224ajUOUrn/ACEJVOiStb8uFEQ6i
.youtube.com	TRUE	/	TRUE	1797677347	SAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	TRUE	1797677347	__Secure-1PAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	TRUE	1797677347	__Secure-3PAPISID	4Qh2lzrTgdVFgBeR/AMk1PKsojP7inNxoT
.youtube.com	TRUE	/	TRUE	1797679646	PREF	tz=Asia.Calcutta
.youtube.com	TRUE	/	TRUE	1797335988	LOGIN_INFO	AFmmF2swRQIgW_Jp2O0QiATZj3jI4McGhE5P5C1cb9PvgW2JaefWAh4CIQD63Gu4PAnSaXQDGPB5R6HMHqfnhxtQk7J_gwZgE85HSQ:QUQ3MjNmeEJaN3VJYWt2b2ZSZWt6b2lRQ3AxX1BxMk1pdlh1Rnc4anlYN3FXWmlGYWN1RDNTUnd5T0w4a1plSEktd2N4QmY2RDgyVUk5a1paVGVXNTB0MFdRZTZObHVCWDJLcl82bzFUem9zUkQ0NWs2R0Zmc3R3b0ZOWHlId2lEQ1VjQ0FNOHhadUtnN3BMbUpidnlnUVJHTllYVTFLRldR
.youtube.com	TRUE	/	FALSE	1797677347	SID	g.a0003gi2f3TIHWCnPvP9_MFjw36kX93KE__AeON0l4cRismUhSMTLsIiG3asC_sFUic8FNzBigACgYKAaISARESFQHGX2MiZUR6BDriBBmYTxiJYi-LYxoVAUF8yKoSwE8V5ukGl33eyCSf4HWF0076
.youtube.com	TRUE	/	TRUE	1797677347	__Secure-1PSID	g.a0003gi2f3TIHWCnPvP9_MFjw36kX93KE__AeON0l4cRismUhSMT8xhQ76utVPQSyF7oS0558AACgYKAcUSARESFQHGX2MiqBN-d8wvAOAUWqVeSxuhHRoVAUF8yKp5nImB-5VjNJiwKui3o6ZS0076
.youtube.com	TRUE	/	TRUE	1797677347	__Secure-3PSID	g.a0003gi2f3TIHWCnPvP9_MFjw36kX93KE__AeON0l4cRismUhSMTjDGsHS3q2shx4x3mX7kz4AACgYKAacSARESFQHGX2Mi3PdBpAQpZBr1F33QXFDfuhoVAUF8yKoB7eJSsKn0pke44F2qOMsD0076
.youtube.com	TRUE	/	TRUE	1794655651	__Secure-1PSIDTS	sidts-CjQBwQ9iI8dlK38RWzvHRUIefraq9u6Vbh2otV5R9a0SepcEQuasnHuGJ9ZMNNDaXQLijbr7EAA
.youtube.com	TRUE	/	TRUE	1794655651	__Secure-3PSIDTS	sidts-CjQBwQ9iI8dlK38RWzvHRUIefraq9u6Vbh2otV5R9a0SepcEQuasnHuGJ9ZMNNDaXQLijbr7EAA
.youtube.com	TRUE	/	FALSE	1794655651	SIDCC	AKEyXzU0IHHw2oDHk54GpjTfiPHvl4mWTPT_G7gDoGhzv8wbhPEBMpP2Jid5elFDXqnE-oFwbQ
.youtube.com	TRUE	/	TRUE	1794655651	__Secure-1PSIDCC	AKEyXzW52f0ZgpWMBWnuu2mKwzQ2GQRd3Z3F1dfTNcTyB4KAms8FwgmiR7qtPOpsb61WYyXt
.youtube.com	TRUE	/	TRUE	1794655651	__Secure-3PSIDCC	AKEyXzXaEZ8Bozhmio5Bf4ci3JPTfZi8LUh3nWJFieY7gaPXX2GEpgRbZ71dh7PTtMofI-AF
.youtube.com	TRUE	/	FALSE	1763119672	ST-3opvp5	session_logininfo=AFmmF2swRQIgW_Jp2O0QiATZj3jI4McGhE5P5C1cb9PvgW2JaefWAh4CIQD63Gu4PAnSaXQDGPB5R6HMHqfnhxtQk7J_gwZgE85HSQ%3AQUQ3MjNmeEJaN3VJYWt2b2ZSZWt6b2lRQ3AxX1BxMk1pdlh1Rnc4anlYN3FXWmlGYWN1RDNTUnd5T0w4a1plSEktd2N4QmY2RDgyVUk5a1paVGVXNTB0MFdRZTZObHVCWDJLcl82bzFUem9zUkQ0NWs2R0Zmc3R3b0ZOWHlId2lEQ1VjQ0FNOHhadUtnN3BMbUpidnlnUVJHTllYVTFLRldR
.youtube.com	TRUE	/	TRUE	1778671640	VISITOR_INFO1_LIVE	LCfl01nbX04
.youtube.com	TRUE	/	TRUE	1778671640	VISITOR_PRIVACY_METADATA	CgJJThIEGgAgPw%3D%3D
.youtube.com	TRUE	/	TRUE	1778658888	__Secure-ROLLOUT_TOKEN	CO2u4-Kw2ZHeRxCDocqdxOeQAxiNo8eAlfGQAw%3D%3D
.youtube.com	TRUE	/	TRUE	0	YSC	pewdGpmmo5Y

"""
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_PATH = f"/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# ================
# CREATE COOKIE FILE
# ================
COOKIE_PATH =YOUTUBE_COOKIE_TEXT
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
