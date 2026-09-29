import asyncio
import html
import json
import logging
import os
import re
import shutil
import sys
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any, Optional, Tuple, TypeVar

import aiohttp
from pyrogram_styled import Client, filters, idle
from pyrogram_styled.enums import ChatType, ParseMode
from pyrogram_styled.errors import DocumentInvalid, FloodWait, MessageNotModified
from pyrogram_styled.helpers.helpers import clean_emoji
from pyrogram_styled.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
T = TypeVar("T")

# ================= DAFTAR EMOJI TERTANAM =================
EMOJI_LIST = ["⚡️", "💎", "🔥", "🚀", "🔗", "💬", "👑", "✨"]

# ================= PARSER FORMAT & STYLED PIPELINE =================
def format_to_html(text: str | None) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"!?\[([^\]]*?)\]\(tg://emoji\?id=(\d+)\)", r"\1", t)
    t = re.sub(r'<tg-emoji\s+emoji-id=[\'"]?(\d+)[\'"]?>(.*?)</tg-emoji>', r"\2", t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r'<emoji\s+id=[\'"]?(\d+)[\'"]?\s*>(.*?)</emoji>', r"\2", t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.DOTALL)
    t = re.sub(r"__(.+?)__", r"<i>\1</i>", t, flags=re.DOTALL)
    t = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<i>\1</i>", t, flags=re.DOTALL)
    t = re.sub(r"`([^`]+?)`", r"<code>\1</code>", t)
    t = re.sub(r"\[([^\]]+?)\]\(((?:https?://\vert{}tg://)[^\)]+)\)", r'<a href="\2">\1</a>', t)
    return t


def strip_custom_emojis(text: str | None) -> str:
    if not text:
        return ""
    cleaned = clean_emoji(text)
    if cleaned:
        return re.sub(r'<tg-emoji\s+emoji-id=[\'"]?\d+[\'"]?>(.*?)</tg-emoji>', r"\1", cleaned)
    return ""


def _is_custom_emoji_rejection(err: Exception) -> bool:
    if isinstance(err, DocumentInvalid):
        return True
    err_str = str(err).upper()
    return "DOCUMENT_INVALID" in err_str or "ENTITY_BOUNDS_INVALID" in err_str


async def _execute_styled_pipeline(
    styled_callable: Callable[[], Awaitable[T]],
    plain_callable: Callable[[], Awaitable[T]],
) -> T:
    try:
        return await styled_callable()
    except FloodWait as flood:
        await asyncio.sleep(flood.value)
        try:
            return await styled_callable()
        except Exception as retry_err:
            if _is_custom_emoji_rejection(retry_err):
                return await plain_callable()
            raise
    except Exception as exc:
        if _is_custom_emoji_rejection(exc):
            return await plain_callable()
        raise


async def safe_reply(m: Message, text: str, **kwargs: Any) -> Message:
    html_text = format_to_html(text)
    return await _execute_styled_pipeline(
        lambda: m.reply(html_text, **kwargs),
        lambda: m.reply(strip_custom_emojis(html_text), **kwargs),
    )


async def safe_edit(msg: Message, text: str, **kwargs: Any) -> Message:
    html_text = format_to_html(text)
    return await _execute_styled_pipeline(
        lambda: msg.edit(html_text, **kwargs),
        lambda: msg.edit(strip_custom_emojis(html_text), **kwargs),
    )


# ================= KONFIGURASI BOT =================
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


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"❌ Variabel {name} belum diisi (environment variable atau file .env).")
    return value


API_ID = int(_require_env("API_ID"))
API_HASH = _require_env("API_HASH")
BOT_TOKEN = _require_env("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "1492743978"))
IMGBB_KEY = os.environ.get("IMGBB_KEY", "")

BASE_WEBAPP_URL = "https://rohidygy.github.io/tagall/"
WEBAPP_BUTTON_TEXT = "✨ ʙᴜᴋᴀ ᴍᴇɴᴜ ᴠɪᴘ ✨"

DATA_FILE = os.path.join(BASE_DIR, "channel_buttons.json")
ADMINS_FILE = os.path.join(BASE_DIR, "bot_admins.json")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)


def esc(value) -> str:
    return html.escape(str(value))


def command_text(message: Message) -> str:
    return str(message.text or message.caption or "")


# ================= DATABASE HANDLERS =================
def _read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Gagal membaca {os.path.basename(path)}: {e}")
        return default


def _write_json(path: str, data):
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, path)


def get_all_data() -> dict:
    data = _read_json(DATA_FILE, {})
    return data if isinstance(data, dict) else {}


def save_all_data(data: dict):
    _write_json(DATA_FILE, data)


def get_admins() -> list:
    data = _read_json(ADMINS_FILE, [])
    admins = [a for a in data if isinstance(a, int)] if isinstance(data, list) else []
    if OWNER_ID not in admins:
        admins.append(OWNER_ID)
    return admins


def save_admins(admins: list):
    _write_json(ADMINS_FILE, admins)


def check_is_admin(_, __, message: Message):
    return bool(message.from_user and message.from_user.id in get_admins())


is_bot_admin = filters.create(check_is_admin)


# ================= HELPER URL & KEYBOARD BUILDER =================
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def clean_url(raw_url: str) -> str:
    url = raw_url.strip().replace(" ", "")
    if not _SCHEME_RE.match(url):
        url = "https://" + url
    return url


def is_valid_url(url: str) -> bool:
    return url.startswith("tg://") or "." in url


def parse_channel_id(raw: str) -> Optional[str]:
    try:
        return str(int(raw.strip()))
    except (ValueError, AttributeError):
        return None


def build_markup(grid: list) -> InlineKeyboardMarkup:
    rows = []
    for row_idx, row in enumerate(grid):
        btn_row = []
        for col_idx, item in enumerate(row):
            raw_text = item.get("text", "").strip()
            url = item.get("url", "").strip()
            emoji_icon = EMOJI_LIST[(row_idx + col_idx) % len(EMOJI_LIST)]

            # Pastikan teks tombol memiliki icon emoji
            clean_btn_text = raw_text
            if not any(char in clean_btn_text for char in ["⚡", "💎", "🔥", "🚀", "🔗", "💬", "👑", "✨"]):
                clean_btn_text = f"{emoji_icon} {clean_btn_text}"

            btn_row.append(InlineKeyboardButton(text=clean_btn_text, url=url))
        if btn_row:
            rows.append(btn_row)
    return InlineKeyboardMarkup(rows)


def get_channel_markup(chat_id: int) -> Optional[InlineKeyboardMarkup]:
    data = get_all_data()
    raw_id = str(chat_id)
    clean_id = raw_id.replace("-100", "").replace("-", "")

    grid = (
        data.get(raw_id)
        or data.get(f"-100{clean_id}")
        or data.get(f"-{clean_id}")
        or data.get(clean_id)
    )

    if not grid:
        return None
    return build_markup(grid)


# ================= HELPER WEBAPP =================
def build_webapp_link(payload: dict) -> str:
    encoded = urllib.parse.quote(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )
    return f"{BASE_WEBAPP_URL}#{encoded}"


def parse_webapp_link(url: str) -> Optional[dict]:
    if not url.startswith(BASE_WEBAPP_URL + "#"):
        return None
    try:
        payload = json.loads(urllib.parse.unquote(url.split("#", 1)[1]))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def payload_from_grid(grid) -> Optional[dict]:
    try:
        return parse_webapp_link(grid[0][0]["url"])
    except (IndexError, KeyError, TypeError):
        return None


def webapp_grid(payload: dict) -> list:
    return [[{
        "text": WEBAPP_BUTTON_TEXT,
        "url": build_webapp_link(payload)
    }]]


async def save_after_preview(
    message: Message, chat_key: str, grid: list, text: str
) -> bool:
    try:
        markup = build_markup(grid)
        await safe_reply(message, text, reply_markup=markup)
    except Exception as e:
        await safe_reply(
            message,
            f"⚠️ <b>Tidak disimpan</b> — Telegram menolak tombol ini:\n"
            f"<code>{esc(e)}</code>"
        )
        return False

    data = get_all_data()
    data[chat_key] = grid
    save_all_data(data)
    return True


# ================= UPLOAD GAMBAR =================
UPLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def _upload_imgbb(session, content: bytes, filename: str) -> str:
    form = aiohttp.FormData()
    form.add_field("image", content, filename=filename)
    async with session.post(
        "https://api.imgbb.com/1/upload", params={"key": IMGBB_KEY}, data=form
    ) as resp:
        js = await resp.json(content_type=None)
        if resp.status == 200 and js.get("success"):
            return js["data"]["url"]
        raise RuntimeError(f"status {resp.status}")


async def _upload_catbox(session, content: bytes, filename: str) -> str:
    form = aiohttp.FormData()
    form.add_field("reqtype", "fileupload")
    form.add_field("fileToUpload", content, filename=filename)
    async with session.post("https://catbox.moe/user/api.php", data=form) as resp:
        text = (await resp.text()).strip()
        if resp.status == 200 and text.startswith("http"):
            return text
        raise RuntimeError(f"status {resp.status}: {text[:100]}")


async def upload_image(file_path: str) -> Tuple[str, bool]:
    with open(file_path, "rb") as f:
        content = f.read()
    filename = os.path.basename(file_path)

    providers = []
    if IMGBB_KEY:
        providers.append(("ImgBB", _upload_imgbb, False))
    providers.append(("Catbox", _upload_catbox, False))

    errors = []
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(headers=UPLOAD_HEADERS, timeout=timeout) as session:
        for name, func, temporary in providers:
            try:
                return await func(session, content, filename), temporary
            except Exception as err:
                errors.append(f"{name}: {err}")
    raise RuntimeError("Upload gagal: " + "; ".join(errors))


def find_image_message(message: Message) -> Optional[Message]:
    if message.photo:
        return message
    if message.reply_to_message and message.reply_to_message.photo:
        return message.reply_to_message
    return None


async def upload_message_image(source: Message) -> Tuple[str, bool]:
    file_path = None
    try:
        file_path = await source.download()
        return await upload_image(file_path)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


# ================= COMMAND /START =================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    admins = get_admins()

    if user_id not in admins:
        return await safe_reply(message, "👋 <b>Bot aktif mengelola tombol channel.</b>")

    is_owner = user_id == OWNER_ID
    role_text = "👑 <b>Owner Utama</b>" if is_owner else "🥇 <b>Admin Terdaftar</b>"

    text = (
        f"👋 Halo <b>{esc(message.from_user.first_name)}</b>! ({role_text})\n\n"
        "⚡️ <b>Perintah Pengaturan:</b>\n"
        "• <code>/setbutton &lt;ID_CH&gt;</code> → Tombol channel biasa\n"
        "• <code>/setweb &lt;ID_CH&gt; [JUDUL | SUBTITLE | BADGE | BG_URL]</code> → Mini App WebApp\n"
        "• <code>/cekbutton &lt;ID_CH&gt;</code> → Cek tombol channel\n"
        "• <code>/delbutton &lt;ID_CH&gt;</code> → Hapus tombol channel\n"
        "• <code>/listchannel</code> → Daftar channel aktif"
    )

    if is_owner:
        text += (
            "\n\n👑 <b>Perintah Khusus Owner:</b>\n"
            "• <code>/update</code> → Git pull &amp; restart\n"
            "• <code>/restart</code> → Restart bot\n"
            "• <code>/addadmin &lt;USER_ID&gt;</code> | <code>/deladmin</code> | <code>/listadmin</code>"
        )

    await safe_reply(message, text)


# ================= SET TOMBOL (/setbutton) =================
@app.on_message(filters.private & filters.command("setbutton") & is_bot_admin)
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in command_text(message).splitlines() if line.strip()]
    first_line_parts = lines[0].split() if lines else []

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await safe_reply(
            message,
            "⚠️ <b>Format Penggunaan:</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "Website - https://contoh.com\n"
            "CS 1 - https://t.me/admin1 | CS 2 - https://t.me/admin2\n"
            "Join VIP - https://t.me/channel</code>"
        )

    chat_key = parse_channel_id(first_line_parts[1])
    if chat_key is None:
        return await safe_reply(message, "❌ ID channel harus berupa angka.")

    button_grid = []
    for line in lines[1:]:
        row = []
        for btn in line.split("|"):
            if " - " in btn:
                text, url = btn.split(" - ", 1)
                text = text.strip()
                url = clean_url(url)
                if text and is_valid_url(url):
                    row.append({"text": text, "url": url})
        if row:
            button_grid.append(row)

    if not button_grid:
        return await safe_reply(message, "❌ Format salah! Gunakan pemisah: <code> - </code>")

    await save_after_preview(
        message,
        chat_key,
        button_grid,
        f"✅ <b>Tombol Berhasil Disimpan!</b>\nChannel: <code>{chat_key}</code>\n\nPratinjau:",
    )


# ================= CEK & HAPUS TOMBOL =================
@app.on_message(filters.private & filters.command("cekbutton") & is_bot_admin)
async def check_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await safe_reply(message, "Ketik: <code>/cekbutton &lt;ID_CHANNEL&gt;</code>")

    chat_key = parse_channel_id(args[1])
    if chat_key is None:
        return await safe_reply(message, "❌ ID Channel harus berupa angka.")

    grid = get_all_data().get(chat_key)
    if not grid:
        return await safe_reply(message, f"ℹ️ Belum ada tombol untuk channel <code>{chat_key}</code>.")

    markup = build_markup(grid)
    await safe_reply(message, f"💎 <b>Tombol aktif channel</b> <code>{chat_key}</code>:", reply_markup=markup)


@app.on_message(filters.private & filters.command("delbutton") & is_bot_admin)
async def delete_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await safe_reply(message, "Ketik: <code>/delbutton &lt;ID_CHANNEL&gt;</code>")

    ch_id = parse_channel_id(args[1]) or args[1]
    data = get_all_data()

    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await safe_reply(message, f"🗑 Tombol channel <code>{esc(ch_id)}</code> berhasil dihapus.")
    else:
        await safe_reply(message, f"⚠️ Channel <code>{esc(ch_id)}</code> tidak ditemukan.")


@app.on_message(filters.private & filters.command("listchannel") & is_bot_admin)
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await safe_reply(message, "ℹ️ Belum ada channel terdaftar.")

    text = "📣 <b>Channel dengan Tombol Aktif:</b>\n\n"
    for ch_id in data.keys():
        text += f"• <code>{esc(ch_id)}</code>\n"
    await safe_reply(message, text)


# ================= GIT UPDATE & RESTART =================
def restart_process():
    os.execl(sys.executable, sys.executable, *sys.argv)


@app.on_message(filters.private & filters.command(["update", "gitpull"]) & filters.user(OWNER_ID))
async def git_pull_handler(client: Client, message: Message):
    msg = await safe_reply(message, "⚡️ <i>Memperbarui bot via git...</i>")
    try:
        proc = await asyncio.create_subprocess_shell(
            "git fetch --all && git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=BASE_DIR,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        output = stdout.decode().strip() or stderr.decode().strip()
        await safe_edit(msg, f"⭐️ <b>Git Output:</b>\n<code>{output}</code>\n\n<i>Restarting...</i>")
        await asyncio.sleep(1.5)
        restart_process()
    except Exception as e:
        await safe_edit(msg, f"❌ Gagal update: <code>{esc(e)}</code>")


@app.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot_handler(client: Client, message: Message):
    await safe_reply(message, "⚡️ <b>Memulai ulang bot...</b>")
    await asyncio.sleep(1)
    restart_process()


# ================= EKSEKUSI PENEMPELAN TOMBOL CHANNEL =================
_PROCESSED_MSGS = set()

@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    if not message or getattr(message, "empty", False) or message.service:
        return

    cid = message.chat.id
    mid = message.id
    key_event = f"{cid}_{mid}"

    if key_event in _PROCESSED_MSGS:
        return
    _PROCESSED_MSGS.add(key_event)

    print(f"\n[EVENT] Postingan terdeteksi! Channel: {cid} | Msg ID: {mid}")

    markup = get_channel_markup(cid)
    if not markup:
        print(f"[SKIP] ID {cid} belum diatur tombolnya di /setbutton")
        return

    await asyncio.sleep(0.5)

    try:
        await client.edit_message_reply_markup(
            chat_id=cid,
            message_id=mid,
            reply_markup=markup
        )
        print(f"✅ [SUCCESS] Tombol berhasil dipasang di pesan ID {mid}!")
    except MessageNotModified:
        print(f"ℹ️️ [INFO] Tombol sudah sesuai pada pesan ID {mid}.")
    except FloodWait as flood:
        await asyncio.sleep(flood.value)
        try:
            await client.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
            print(f"✅ [SUCCESS] Tombol berhasil dipasang setelah FloodWait di ID {mid}!")
        except Exception:
            pass
    except Exception as err:
        print(f"❌ [ERROR] Gagal memasang tombol di pesan ID {mid}: {err}")


# ================= MAIN RUNNER =================
async def main():
    await app.start()
    logging.info("Bot Channel Button Manager Aktif.")
    await idle()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
