import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import urllib.parse

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# ================= KONFIGURASI BOT =================
API_ID = 1634450
API_HASH = "1a42e816cae8d86e71a4c466bba19b8c"
BOT_TOKEN = "8862325911:AAFZxAdv0K9jTaBQYillPQCbZdYQu-V67-Q"
OWNER_ID = 1492743978  # Super Admin / Pemilik Utama

BASE_WEBAPP_URL = "https://rohidygy.github.io/tagall/"

DATA_FILE = "channel_buttons.json"
ADMINS_FILE = "bot_admins.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


# ================= DATABASE HANDLERS =================
def get_all_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Gagal membaca data tombol: {e}")
        return {}


def save_all_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_admins() -> list:
    if not os.path.exists(ADMINS_FILE):
        return [OWNER_ID]
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if OWNER_ID not in data:
                data.append(OWNER_ID)
            return data
    except Exception as e:
        logging.error(f"Gagal membaca daftar admin: {e}")
        return [OWNER_ID]


def save_admins(admins: list):
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=4)


def check_is_admin(_, __, message: Message):
    return message.from_user and (message.from_user.id in get_admins())

is_bot_admin = filters.create(check_is_admin)


def clean_url(raw_url: str) -> str:
    url = raw_url.strip().replace(" ", "")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def get_channel_markup(chat_id: int):
    data = get_all_data()
    chat_key = str(chat_id)

    if chat_key not in data or not data[chat_key]:
        return None

    keyboard = []
    for row in data[chat_key]:
        row_buttons = []
        for item in row:
            row_buttons.append(InlineKeyboardButton(item["text"], url=item["url"]))
        keyboard.append(row_buttons)

    return InlineKeyboardMarkup(keyboard)


# ================= COMMAND /START =================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    admins = get_admins()

    if user_id not in admins:
        return await message.reply_text("👋 Bot ini aktif untuk mengelola tombol channel.")

    is_owner = (user_id == OWNER_ID)
    role_text = "👑 **Owner Utama**" if is_owner else "🛠 **Admin Terdaftar**"

    text = (
        f"Halo **{message.from_user.first_name}**! ({role_text})\n\n"
        "**Perintah Pengaturan Tombol:**\n"
        "• `/setbutton <ID_CH>` $\\rightarrow$ Tombol link biasa di channel\n"
        "• `/setweb <ID_CH> [JUDUL | SUBTITLE | BADGE]` $\\rightarrow$ Mini App warna-warni\n"
        "• `/cekbutton <ID_CH>` $\\rightarrow$ Cek tombol channel\n"
        "• `/delbutton <ID_CH>` $\\rightarrow$ Hapus tombol channel\n"
        "• `/listchannel` $\\rightarrow$ Daftar channel aktif\n\n"
        "💡 *Teruskan (forward) pesan dari channel ke bot untuk mendapatkan ID.*"
    )

    if is_owner:
        text += (
            "\n\n**Perintah Khusus Owner:**\n"
            "• `/update` $\\rightarrow$ `git pull` & otomatis restart\n"
            "• `/restart` $\\rightarrow$ Restart bot langsung dari chat\n"
            "• `/addadmin <USER_ID>` $\\rightarrow$ Tambah hak akses admin\n"
            "• `/deladmin <USER_ID>` $\\rightarrow$ Cabut hak akses admin\n"
            "• `/listadmin` $\\rightarrow$ Daftar semua admin"
        )

    await message.reply_text(text)


# ================= FITUR GIT PULL & RESTART (OWNER ONLY) =================
@app.on_message(filters.private & filters.command("update") & filters.user(OWNER_ID))
async def git_pull_handler(client: Client, message: Message):
    msg = await message.reply_text("🔄 **Menjalankan git pull...**")
    try:
        # Jalankan git pull di direktori bot
        process = subprocess.run(
            ["git", "pull"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        output = process.stdout or process.stderr
        
        await msg.edit_text(
            f"📦 **Hasil Git Pull:**\n```text\n{output.strip()}\n
