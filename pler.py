import asyncio
import json
import logging
import os
import re
import sys

from pyrogram_styled import Client, filters, idle
from pyrogram_styled.enums import ParseMode
from pyrogram_styled.errors import FloodWait, MessageNotModified
from pyrogram_styled.helpers.helpers import ikb
from pyrogram_styled.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================= DAFTAR CUSTOM EMOJI & WARNA =================
class AnimEmoji:
    API: int = 5420315771991497307        # 🔥
    BERLIAN: int = 5471952986970267163    # 💎
    PETIR: int = 5431449001532594346      # ⚡️
    ROKET: int = 5445284980978621387      # 🚀
    TAUTAN: int = 5375129357373165375     # 🔗
    CHAT: int = 5465300082628763143       # 💬

AUTO_PRESETS = [
    (AnimEmoji.API, "danger"),     # Merah (LIVE NYA DISINI)
    (AnimEmoji.BERLIAN, "primary"),# Putih/Biru (VVIP NYA DISINI)
    (AnimEmoji.PETIR, "success"),  # Hijau
    (AnimEmoji.ROKET, "primary"),
]

# ================= LOAD ENV =================
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

# Client BotFather untuk menu perintah admin
app = Client(
    "channel_button_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)

# Client Userbot Premium untuk eksekusi postingan ber-emoji di channel
user_client = None
if USER_SESSION:
    user_client = Client(
        "premium_userbot_worker",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION,
    )

# ================= DATABASE HANDLER =================
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
    return data.get(raw) or data.get(f"-100{clean}") or data.get(f"-{clean}") or data.get(clean)

def build_styled_markup(grid: list) -> InlineKeyboardMarkup:
    styled_rows = []
    plain_rows = []

    for r_idx, row in enumerate(grid):
        s_row = []
        p_row = []
        for c_idx, item in enumerate(row):
            text = item.get("text", "").strip()
            url = item.get("url", "").strip()
            preset = AUTO_PRESETS[(r_idx + c_idx) % len(AUTO_PRESETS)]
            eid = int(item.get("emoji_id") or preset[0])
            style = str(item.get("style") or preset[1])

            p_row.append(InlineKeyboardButton(text=text, url=url))
            s_row.append((f" {text} ", url, eid, style))

        styled_rows.append(s_row)
        plain_rows.append(p_row)

    try:
        return ikb(styled_rows)
    except Exception:
        return InlineKeyboardMarkup(plain_rows)

# ================= COMMAND /SETBUTTON VIA BOT =================
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
    for r_idx, line in enumerate(lines[1:]):
        row = []
        for c_idx, b in enumerate(line.split("|")):
            if " - " in b:
                txt, url = b.split(" - ", 1)
                txt = txt.strip()
                url = url.strip()
                if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", url):
                    url = "https://" + url

                preset = AUTO_PRESETS[(r_idx + c_idx) % len(AUTO_PRESETS)]
                row.append({
                    "text": txt,
                    "url": url,
                    "emoji_id": preset[0],
                    "style": preset[1]
                })
        if row:
            grid.append(row)

    if not grid:
        return await message.reply("❌ Format salah! Gunakan pemisah: <code> - </code>")

    data = get_all_data()
    data[chat_key] = grid
    save_all_data(data)

    markup = build_styled_markup(grid)
    await message.reply(
        f"✅ <b>Tombol Berhasil Disimpan!</b>\n"
        f"Channel: <code>{chat_key}</code>\n\nPratinjau:",
        reply_markup=markup
    )

@app.on_message(filters.private & filters.command("cekbutton") & filters.user(OWNER_ID))
async def cek_button_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Ketik: <code>/cekbutton &lt;ID_CHANNEL&gt;</code>")

    ch_key = args[1].strip()
    grid = get_channel_grid(int(ch_key)) if ch_key.lstrip("-").isdigit() else None
    if not grid:
        return await message.reply(f"ℹ️ Belum ada tombol untuk channel <code>{ch_key}</code>.")

    markup = build_styled_markup(grid)
    await message.reply(f"💎 <b>Tombol aktif channel</b> <code>{ch_key}</code>:", reply_markup=markup)

@app.on_message(filters.private & filters.command("delbutton") & filters.user(OWNER_ID))
async def del_button_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Ketik: <code>/delbutton &lt;ID_CHANNEL&gt;</code>")

    ch_id = args[1].strip()
    data = get_all_data()
    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await message.reply(f"🗑 Tombol channel <code>{ch_id}</code> berhasil dihapus.")
    else:
        await message.reply(f"⚠️ Channel <code>{ch_id}</code> tidak ditemukan.")

# ================= GIT UPDATE & RESTART =================
def restart_process():
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.private & filters.command(["update", "gitpull"]) & filters.user(OWNER_ID))
async def git_pull_cmd(client: Client, message: Message):
    msg = await message.reply("⚡ <i>Menarik pembaruan dari Git...</i>")
    try:
        proc = await asyncio.create_subprocess_shell(
            "git fetch --all && git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=BASE_DIR,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode().strip() or stderr.decode().strip()
        await msg.edit(f"⭐️ <b>Git Output:</b>\n<code>{output}</code>\n\n<i>Restarting...</i>")
        await asyncio.sleep(1.5)
        restart_process()
    except Exception as e:
        await msg.edit(f"❌ Gagal update: <code>{e}</code>")

@app.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_cmd(client: Client, message: Message):
    await message.reply("⚡️ <b>Memulai ulang bot...</b>")
    await asyncio.sleep(1)
    restart_process()

# ================= USERBOT WORKER: AUTO-REPLACE POSTINGAN CHANNEL =================
_SENT_BY_USERBOT = set()

def setup_userbot_worker():
    if not user_client:
        return

    @user_client.on_message(filters.channel)
    async def userbot_channel_replacer(client: Client, message: Message):
        if not message or getattr(message, "empty", False) or message.service:
            return

        cid = message.chat.id
        mid = message.id

        # Cegah looping tak hingga dari pesan yang diposting oleh userbot sendiri
        if mid in _SENT_BY_USERBOT:
            return

        grid = get_channel_grid(cid)
        if not grid:
            return

        print(f"\n[USERBOT] Mendeteksi postingan baru di channel {cid} (ID: {mid})")
        styled_markup = build_styled_markup(grid)

        try:
            # 1. Userbot Premium memposting ulang pesan bersama tombol & custom emoji bergerak
            new_msg = await message.copy(
                chat_id=cid,
                reply_markup=styled_markup
            )
            _SENT_BY_USERBOT.add(new_msg.id)
            print(f"🔥 [USERBOT SUCCESS] Postingan baru berhasil terbit dengan Emoji Bergerak di ID {new_msg.id}!")

            # 2. Hapus pesan lama yang tadi diposting manual agar channel tetap rapi
            await message.delete()
            print(f"🧹 Pesan mentah ID {mid} berhasil dihapus.")

        except FloodWait as flood:
            await asyncio.sleep(flood.value)
            try:
                new_msg = await message.copy(chat_id=cid, reply_markup=styled_markup)
                _SENT_BY_USERBOT.add(new_msg.id)
                await message.delete()
            except Exception:
                pass
        except Exception as e:
            print(f"❌ Userbot gagal memproses replace: {e}")

# ================= RUNNER =================
async def main():
    await app.start()
    logging.info("BotFather Admin Listener Aktif.")

    if user_client:
        await user_client.start()
        setup_userbot_worker()
        logging.info("Userbot Premium Worker Aktif & Siap Memasang Tombol Bergerak!")

    await idle()

    if user_client:
        await user_client.stop()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
