import asyncio
import html
import json
import logging
import os
import re
import shutil
import sys
import urllib.parse

from pyrogram_styled import Client, filters, idle
from pyrogram_styled.enums import ChatType, ParseMode
from pyrogram_styled.helpers.helpers import ikb
from pyrogram_styled.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DAFTAR ANIMATED EMOJI =================
class AnimEmoji:
    PETIR: int = 5431449001532594346      # ⚡️
    BERLIAN: int = 5471952986970267163    # 💎
    API: int = 5420315771991497307        # 🔥
    ROKET: int = 5445284980978621387      # 🚀
    TAUTAN: int = 5375129357373165375     # 🔗
    CHAT: int = 5465300082628763143       # 💬

AUTO_EMOJIS = [
    AnimEmoji.API,
    AnimEmoji.PETIR,
    AnimEmoji.BERLIAN,
    AnimEmoji.ROKET,
]

# ================= KONFIGURASI ENV =================
def _load_env_file(path: str):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_env_file(os.path.join(BASE_DIR, ".env"))

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "1492743978"))
USER_SESSION = os.environ.get("USER_SESSION", "").strip()

DATA_FILE = os.path.join(BASE_DIR, "channel_buttons.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = Client(
    "channel_button_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)

user_client = None
if USER_SESSION:
    user_client = Client(
        "bridge_userbot_buttons",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION,
    )

# ================= DATABASE =================
def get_all_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_all_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_channel_grid(chat_id: int):
    data = get_all_data()
    raw = str(chat_id)
    clean = raw.replace("-100", "").replace("-", "")
    return data.get(raw) or data.get(f"-100{clean}") or data.get(clean)

def build_styled_markup(grid: list) -> InlineKeyboardMarkup:
    styled_rows = []
    plain_rows = []
    for r_idx, row in enumerate(grid):
        s_row = []
        p_row = []
        for c_idx, item in enumerate(row):
            text = item.get("text", "")
            url = item.get("url", "")
            eid = item.get("emoji_id") or AUTO_EMOJIS[(r_idx + c_idx) % len(AUTO_EMOJIS)]
            p_row.append(InlineKeyboardButton(text=text, url=url))
            s_row.append((f" {text} ", url, int(eid), "primary"))
        styled_rows.append(s_row)
        plain_rows.append(p_row)
    try:
        return ikb(styled_rows)
    except Exception:
        return InlineKeyboardMarkup(plain_rows)

# ================= COMMAND ADMIN =================
@app.on_message(filters.private & filters.command("setbutton") & filters.user(OWNER_ID))
async def set_button_cmd(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_parts = lines[0].split()
    if len(first_parts) < 2 or len(lines) < 2:
        return await message.reply(
            "⚠️ <b>Format Penggunaan:</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "LIVE NYA DISINI - https://link1.com\n"
            "VVIP NYA DISINI - https://link2.com</code>"
        )
    
    chat_key = first_parts[1].strip()
    grid = []
    for line in lines[1:]:
        row = []
        for b in line.split("|"):
            if " - " in b:
                txt, url = b.split(" - ", 1)
                row.append({"text": txt.strip(), "url": url.strip()})
        if row:
            grid.append(row)
    
    data = get_all_data()
    data[chat_key] = grid
    save_all_data(data)
    
    markup = build_styled_markup(grid)
    await message.reply(f"✅ <b>Tombol Disimpan!</b> Channel: <code>{chat_key}</code>\n\nPratinjau:", reply_markup=markup)

# ================= INLINE QUERY HANDLER (KUNCI ANIMASI) =================
@app.on_inline_query()
async def inline_button_provider(client: Client, inline_query: InlineQuery):
    q = inline_query.query.strip()
    if not q:
        return
    
    grid = get_channel_grid(int(q)) if q.lstrip("-").isdigit() else None
    if not grid:
        return
    
    markup = build_styled_markup(grid)
    results = [
        InlineQueryResultArticle(
            id=f"btn_{q}",
            title="Tempel Tombol Bergerak",
            input_message_content=InputTextMessageContent("."),
            reply_markup=markup
        )
    ]
    await inline_query.answer(results, cache_time=1)

# ================= AUTO ATTACH VIA USERBOT INLINE =================
_PROCESSED = set()

async def handle_post(client: Client, message: Message):
    if not message or getattr(message, "empty", False) or message.service:
        return
    
    cid = message.chat.id
    mid = message.id
    key = f"{cid}_{mid}"
    if key in _PROCESSED:
        return
    _PROCESSED.add(key)
    
    grid = get_channel_grid(cid)
    if not grid:
        return
    
    markup = build_styled_markup(grid)
    await asyncio.sleep(0.5)

    # 1. Edit via Userbot Premium langsung
    applied = False
    if user_client:
        try:
            bot_user = await app.get_me()
            # Panggil inline bot dari Userbot
            inline_res = await user_client.get_inline_bot_results(bot_user.username, str(cid))
            if inline_res and inline_res.results:
                # Ambil reply_markup ber-emoji yang di-generate inline
                target_markup = inline_res.results[0].send_message.reply_markup
                await user_client.edit_message_reply_markup(
                    chat_id=cid,
                    message_id=mid,
                    reply_markup=target_markup
                )
                applied = True
                print(f"🔥 [SUCCESS] Tombol Animasi BERGERAK Berhasil via Userbot Inline di ID {mid}!")
        except Exception as e:
            print(f"⚠️ Userbot Inline gagal: {e}")
            try:
                # Fallback manual userbot styled markup
                await user_client.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
                applied = True
                print(f"🔥 [SUCCESS] Tombol Animasi Berhasil via Direct Userbot di ID {mid}!")
            except Exception as e2:
                print(f"⚠️ Userbot Direct gagal: {e2}")

    # 2. Fallback BotFather jika userbot gagal
    if not applied:
        try:
            await app.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
            print(f"✅ Tombol dipasang via BotFather di ID {mid}!")
        except Exception as err:
            print(f"❌ BotFather gagal: {err}")

@app.on_message(filters.channel)
async def bot_listener(_: Client, m: Message):
    await handle_post(app, m)

def setup_userbot():
    if user_client:
        @user_client.on_message(filters.channel)
        async def user_listener(_: Client, m: Message):
            await handle_post(user_client, m)

# ================= RUNNER =================
async def main():
    await app.start()
    print("BotFather Aktif.")
    if user_client:
        await user_client.start()
        setup_userbot()
        print("Userbot Premium Aktif.")
    await idle()
    if user_client:
        await user_client.stop()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
