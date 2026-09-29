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
from pyrogram_styled.helpers.helpers import clean_emoji, ikb
from pyrogram_styled.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
T = TypeVar("T")

# ================= DAFTAR CUSTOM ANIMATED EMOJI TERTANAM =================
class AnimEmoji:
    TANGAN: int = 5472055112702629499     # 👋
    PETIR: int = 5431449001532594346      # ⚡️
    BERLIAN: int = 5471952986970267163    # 💎
    KILAU: int = 5472164874886846699      # ✨
    API: int = 5420315771991497307        # 🔥
    MAHKOTA: int = 5467406098367521267    # 👑
    CENTANG: int = 5427009714745517609    # ✅
    SILANG: int = 5465665476971471368     # ❌
    BINTANG: int = 5435957248314579621    # ⭐️
    ROKET: int = 5445284980978621387      # 🚀
    JAM_PASIR: int = 5451732530048802485  # ⏳
    LAMPU: int = 5472146462362048818      # 💡
    PESTA: int = 5436040291507247633      # 🎉
    CHAT: int = 5465300082628763143       # 💬
    MEGAPHONE: int = 5469903029144657419  # 📣
    GRAFIK: int = 5431577498364158238     # 📊
    TAUTAN: int = 5375129357373165375     # 🔗
    MEDALI_EMAS: int = 5280735858926822987  # 🥇
    MATA: int = 5424885441100782420       # 👀
    DILARANG: int = 5240241223632954241   # 🚫
    PERINGATAN: int = 5447644880824181073 # ⚠️
    SAMPAH: int = 5445267414562389170     # 🗑
    SURAT: int = 5253742260054409879      # ✉️
    INFO: int = 5334544901428229844       # ℹ️


AUTO_EMOJIS = [
    AnimEmoji.PETIR,
    AnimEmoji.BERLIAN,
    AnimEmoji.API,
    AnimEmoji.ROKET,
    AnimEmoji.TAUTAN,
    AnimEmoji.CHAT,
]


# ================= PARSER FORMAT & STYLED PIPELINE =================
def format_to_html(text: str | None) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"!?\[([^\]]*?)\]\(tg://emoji\?id=(\d+)\)", r"<emoji id=\2>\1</emoji>", t)
    t = re.sub(r'<tg-emoji\s+emoji-id=[\'"]?(\d+)[\'"]?>(.*?)</tg-emoji>', r"<emoji id=\1>\2</emoji>", t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r'<emoji\s+id=[\'"]?(\d+)[\'"]?\s*>(.*?)</emoji>', r"<emoji id=\1>\2</emoji>", t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r"<emoji\s+id=(\d+)>!+(.*?)</emoji>", r"<emoji id=\1>\2</emoji>", t)
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


# ================= KONFIGURASI BOT & USERBOT =================
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
USER_SESSION = os.environ.get("USER_SESSION", "").strip()

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

user_client: Optional[Client] = None
if USER_SESSION:
    user_client = Client(
        "bridge_userbot_buttons",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=USER_SESSION,
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
    styled_rows = []
    plain_rows = []

    for row_idx, row in enumerate(grid):
        s_row = []
        p_row = []
        for col_idx, item in enumerate(row):
            text = item.get("text", "")
            url = item.get("url", "")
            emoji_id = item.get("emoji_id") or AUTO_EMOJIS[(row_idx + col_idx) % len(AUTO_EMOJIS)]

            p_row.append(InlineKeyboardButton(text=text, url=url))
            s_row.append((f" {text} ", url, int(emoji_id), "primary"))

        styled_rows.append(s_row)
        plain_rows.append(p_row)

    try:
        return ikb(styled_rows)
    except Exception as exc:
        logging.warning("Fallback keyboard biasa: %s", exc)
        return InlineKeyboardMarkup(plain_rows)


def get_channel_markup(chat_id: int):
    grid = get_all_data().get(str(chat_id))
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
        "url": build_webapp_link(payload),
        "emoji_id": AnimEmoji.KILAU
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
            f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> <b>Tidak disimpan</b> — Telegram menolak tombol ini:\n"
            f"<code>{esc(e)}</code>\n\n"
            "Periksa kembali URL yang dimasukkan."
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


async def _upload_tmpfiles(session, content: bytes, filename: str) -> str:
    form = aiohttp.FormData()
    form.add_field("file", content, filename=filename)
    async with session.post("https://tmpfiles.org/api/v1/upload", data=form) as resp:
        if resp.status != 200:
            raise RuntimeError(f"status {resp.status}")
        js = await resp.json(content_type=None)
        raw_url = (js.get("data") or {}).get("url")
        if not raw_url:
            raise RuntimeError("respons tanpa URL")
        raw_url = raw_url.replace("http://", "https://", 1)
        return raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)


async def upload_image(file_path: str) -> Tuple[str, bool]:
    with open(file_path, "rb") as f:
        content = f.read()
    filename = os.path.basename(file_path)

    providers = []
    if IMGBB_KEY:
        providers.append(("ImgBB", _upload_imgbb, False))
    providers.append(("Catbox", _upload_catbox, False))
    providers.append(("tmpfiles", _upload_tmpfiles, True))

    errors = []
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(headers=UPLOAD_HEADERS, timeout=timeout) as session:
        for name, func, temporary in providers:
            try:
                return await func(session, content, filename), temporary
            except Exception as err:
                errors.append(f"{name}: {err}")
    raise RuntimeError("Semua server upload gagal → " + "; ".join(errors))


def is_image_message(msg: Optional[Message]) -> bool:
    if not msg:
        return False
    if msg.photo:
        return True
    doc = msg.document
    return bool(doc and doc.mime_type and doc.mime_type.startswith("image/"))


def find_image_message(message: Message) -> Optional[Message]:
    if is_image_message(message):
        return message
    if is_image_message(message.reply_to_message):
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


TEMP_WARNING = (
    f"\n\n<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> <i>Foto diunggah ke server sementara (tmpfiles).</i>"
)


# ================= COMMAND /START =================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    admins = get_admins()

    if user_id not in admins:
        return await safe_reply(
            message,
            f"<emoji id={AnimEmoji.TANGAN}>👋</emoji> <b>Bot aktif mengelola tombol channel.</b>"
        )

    is_owner = user_id == OWNER_ID
    role_text = f"<emoji id={AnimEmoji.MAHKOTA}>👑</emoji> <b>Owner Utama</b>" if is_owner else f"<emoji id={AnimEmoji.MEDALI_EMAS}>🥇</emoji> <b>Admin Terdaftar</b>"
    bridge_st = "🟢 AKTIF (Akun Premium)" if user_client else "🔴 NONAKTIF (Cek USER_SESSION di .env)"

    text = (
        f"<emoji id={AnimEmoji.TANGAN}>👋</emoji> Halo <b>{esc(message.from_user.first_name)}</b>! ({role_text})\n\n"
        f"<emoji id={AnimEmoji.PETIR}>⚡️</emoji> <b>Userbot Bridge:</b> {bridge_st}\n"
        f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <b>Status Tombol:</b> <code>Auto Animated Emoji Tertanam</code>\n\n"
        f"<emoji id={AnimEmoji.PETIR}>⚡️</emoji> <b>Perintah Tombol:</b>\n"
        "• <code>/setbutton &lt;ID_CH&gt;</code> → Tombol channel biasa (otomatis ber-emoji)\n"
        "• <code>/setweb &lt;ID_CH&gt; [JUDUL | SUBTITLE | BADGE | BG_URL]</code> → Mini App WebApp\n"
        "• <code>/setfoto &lt;ID_CH&gt;</code> + foto → Ganti background WebApp\n"
        "• <code>/delfoto &lt;ID_CH&gt;</code> → Hapus background WebApp\n"
        "• <code>/setimg</code> + foto → Upload foto jadi direct URL\n"
        "• <code>/cekbutton &lt;ID_CH&gt;</code> → Cek tombol channel\n"
        "• <code>/delbutton &lt;ID_CH&gt;</code> → Hapus tombol channel\n"
        "• <code>/listchannel</code> → Daftar channel aktif"
    )

    if is_owner:
        text += (
            f"\n\n<emoji id={AnimEmoji.MAHKOTA}>👑</emoji> <b>Perintah Khusus Owner:</b>\n"
            "• <code>/update</code> → Git pull reset &amp; restart otomatis\n"
            "• <code>/restart</code> → Restart bot langsung\n"
            "• <code>/addadmin &lt;USER_ID&gt;</code> | <code>/deladmin</code> | <code>/listadmin</code>"
        )

    await safe_reply(message, text)


# ================= UPLOAD GAMBAR (/setimg) =================
@app.on_message(filters.private & filters.command("setimg") & is_bot_admin)
async def set_image_handler(client: Client, message: Message):
    image_msg = find_image_message(message)
    if not image_msg:
        return await safe_reply(
            message,
            f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Kirim/balas foto dengan <code>/setimg</code>."
        )

    status_msg = await safe_reply(message, f"<emoji id={AnimEmoji.JAM_PASIR}>⏳</emoji> <i>Mengunggah gambar...</i>")
    try:
        direct_url, temporary = await upload_message_image(image_msg)
        text = (
            f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <b>Gambar Berhasil Diunggah!</b>\n\n"
            f"<emoji id={AnimEmoji.TAUTAN}>🔗</emoji> <b>Direct URL:</b>\n<code>{esc(direct_url)}</code>"
        )
        if temporary:
            text += TEMP_WARNING
        await safe_edit(status_msg, text)
    except Exception as e:
        await safe_edit(status_msg, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Gagal memproses gambar: <code>{esc(e)}</code>")


# ================= SET FOTO BACKGROUND WEBAPP (/setfoto, /delfoto) =================
@app.on_message(filters.private & filters.command("setfoto") & is_bot_admin)
async def set_photo_handler(client: Client, message: Message):
    parts = command_text(message).split()
    image_msg = find_image_message(message)

    if len(parts) < 2 or not image_msg:
        return await safe_reply(
            message,
            f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Kirim/balas foto dengan caption <code>/setfoto -100xxxxxxxxxx</code>"
        )

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> ID channel harus berupa angka.")

    payload = payload_from_grid(get_all_data().get(chat_key))
    if payload is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Channel <code>{chat_key}</code> belum punya WebApp.")

    status_msg = await safe_reply(message, f"<emoji id={AnimEmoji.JAM_PASIR}>⏳</emoji> <i>Mengunggah foto...</i>")
    try:
        bg_url, temporary = await upload_message_image(image_msg)
    except Exception as e:
        return await safe_edit(status_msg, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Foto gagal diunggah: <code>{esc(e)}</code>")
    await status_msg.delete()

    payload["background"] = bg_url
    text = (
        f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <b>Foto Background Berhasil Diganti!</b>\n\n"
        f"• <b>Channel:</b> <code>{chat_key}</code>\n"
        f"• <b>Background:</b> <code>{esc(bg_url)}</code>\n\n"
        "Pratinjau tombol channel:"
    )
    if temporary:
        text += TEMP_WARNING
    await save_after_preview(message, chat_key, webapp_grid(payload), text)


@app.on_message(filters.private & filters.command("delfoto") & is_bot_admin)
async def delete_photo_handler(client: Client, message: Message):
    parts = command_text(message).split()
    if len(parts) < 2:
        return await safe_reply(message, "Ketik: <code>/delfoto &lt;ID_CHANNEL&gt;</code>")

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> ID channel harus berupa angka.")

    payload = payload_from_grid(get_all_data().get(chat_key))
    if payload is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Channel <code>{chat_key}</code> belum punya WebApp.")

    payload["background"] = ""
    await save_after_preview(
        message,
        chat_key,
        webapp_grid(payload),
        f"<emoji id={AnimEmoji.SAMPAH}>🗑</emoji> Foto background channel <code>{chat_key}</code> dihapus.",
    )


# ================= FITUR GIT UPDATE HARD-RESET (OWNER ONLY) =================
def restart_process():
    os.execl(sys.executable, sys.executable, *sys.argv)


@app.on_message(filters.private & filters.command(["update", "gitpull"]) & filters.user(OWNER_ID))
async def git_pull_handler(client: Client, message: Message):
    msg = await safe_reply(message, f"<emoji id={AnimEmoji.PETIR}>⚡️</emoji> <i>Menarik pembaruan dari Git & membersihkan cache...</i>")
    try:
        pull_cmd = "git fetch --all && git reset --hard origin/$(git rev-parse --abbrev-ref HEAD)"
        proc = await asyncio.create_subprocess_shell(
            pull_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=BASE_DIR,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            return await safe_edit(msg, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> <b>git update timeout (30 detik).</b>")

        output = stdout.decode().strip() or stderr.decode().strip()

        for root, dirs, files in os.walk(BASE_DIR):
            for d in dirs:
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
            for f in files:
                if f.endswith(".pyc") or f.endswith(".pyo"):
                    try:
                        os.remove(os.path.join(root, f))
                    except OSError:
                        pass

        await safe_edit(
            msg,
            f"<emoji id={AnimEmoji.BINTANG}>⭐️</emoji> <b>Git Output:</b>\n\n<code>{output}</code>\n\n"
            f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <i>Cache bersih. Memuat ulang bot...</i>",
        )
        await asyncio.sleep(1.5)
        restart_process()
    except Exception as e:
        await safe_edit(msg, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> <b>Gagal update/restart:</b>\n<code>{esc(e)}</code>")


@app.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot_handler(client: Client, message: Message):
    await safe_reply(message, f"<emoji id={AnimEmoji.PETIR}>⚡️</emoji> <b>Memulai ulang bot... Tunggu beberapa detik.</b>")
    await asyncio.sleep(1)
    restart_process()


# ================= MANAJEMEN AKSES ADMIN (OWNER ONLY) =================
def get_forward_info(message: Message):
    origin = getattr(message, "forward_origin", None)
    if origin is not None:
        return getattr(origin, "chat", None), getattr(origin, "sender_user", None)
    return getattr(message, "forward_from_chat", None), getattr(message, "forward_from", None)


@app.on_message(filters.private & filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_handler(client: Client, message: Message):
    target_id = None
    if message.reply_to_message:
        _, fwd_user = get_forward_info(message.reply_to_message)
        if fwd_user:
            target_id = fwd_user.id

    if target_id is None:
        parts = message.text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[1])
            except ValueError:
                return await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> User ID harus berupa angka.")

    if not target_id:
        return await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Format: <code>/addadmin &lt;USER_ID&gt;</code>")

    admins = get_admins()
    if target_id in admins:
        return await safe_reply(message, f"<emoji id={AnimEmoji.INFO}>ℹ️</emoji> User <code>{target_id}</code> sudah jadi admin.")

    admins.append(target_id)
    save_admins(admins)
    await safe_reply(message, f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> User ID <code>{target_id}</code> resmi jadi admin.")


@app.on_message(filters.private & filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_handler(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Format: <code>/deladmin &lt;USER_ID&gt;</code>")

    try:
        target_id = int(parts[1])
    except ValueError:
        return await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> User ID harus berupa angka.")

    if target_id == OWNER_ID:
        return await safe_reply(message, f"<emoji id={AnimEmoji.DILARANG}>🚫</emoji> Owner utama tidak dapat dihapus.")

    admins = get_admins()
    if target_id not in admins:
        return await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> User <code>{target_id}</code> tidak ada di daftar admin.")

    admins.remove(target_id)
    save_admins(admins)
    await safe_reply(message, f"<emoji id={AnimEmoji.SAMPAH}>🗑</emoji> Akses admin <code>{target_id}</code> dicabut.")


@app.on_message(filters.private & filters.command("listadmin") & filters.user(OWNER_ID))
async def list_admin_handler(client: Client, message: Message):
    text = f"<emoji id={AnimEmoji.CHAT}>💬</emoji> <b>Daftar Admin Bot:</b>\n\n"
    for uid in get_admins():
        role = "Owner" if uid == OWNER_ID else "Admin"
        text += f"• <code>{uid}</code> <i>({role})</i>\n"
    await safe_reply(message, text)


# ================= DETEKSI ID FORWARD =================
@app.on_message(filters.private & filters.forwarded & is_bot_admin)
async def detect_forward(client: Client, message: Message):
    fwd_chat, fwd_user = get_forward_info(message)
    if fwd_chat and fwd_chat.type == ChatType.CHANNEL:
        await safe_reply(
            message,
            f"<emoji id={AnimEmoji.MEGAPHONE}>📣</emoji> <b>Channel:</b> <b>{esc(fwd_chat.title)}</b> (<code>{fwd_chat.id}</code>)"
        )
    elif fwd_user:
        await safe_reply(
            message,
            f"<emoji id={AnimEmoji.CHAT}>💬</emoji> <b>Pengguna:</b> <b>{esc(fwd_user.first_name)}</b> (<code>{fwd_user.id}</code>)"
        )


# ================= ATUR TOMBOL BIASA (/setbutton) =================
@app.on_message(filters.private & filters.command("setbutton") & is_bot_admin)
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in command_text(message).splitlines() if line.strip()]
    first_line_parts = lines[0].split() if lines else []

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await safe_reply(
            message,
            f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> <b>Format Cukup Teks &amp; Link Saja (Emoji Otomatis Ditanam):</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "Website Resmi - https://contoh.com\n"
            "Admin CS 1 - https://t.me/admin1 | Admin CS 2 - https://t.me/admin2\n"
            "Join VIP - https://t.me/channel</code>"
        )

    chat_key = parse_channel_id(first_line_parts[1])
    if chat_key is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> ID channel harus berupa angka.")

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
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Format salah! Gunakan pemisah: <code> - </code>")

    await save_after_preview(
        message,
        chat_key,
        button_grid,
        f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <b>Tombol Berhasil Disimpan &amp; Emoji Animasi Tertanam!</b>\nChannel: <code>{chat_key}</code>\n\nPratinjau:",
    )


# ================= ATUR WEBAPP POP-UP (/setweb) =================
@app.on_message(filters.private & filters.command("setweb") & is_bot_admin)
async def set_webapp_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in command_text(message).splitlines() if line.strip()]
    first_line = lines[0] if lines else ""
    parts = first_line.split()

    if len(parts) < 2 or len(lines) < 2:
        return await safe_reply(
            message,
            f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> <b>Format /setweb:</b>\n\n"
            "<code>/setweb -100xxxxxxxxxx [JUDUL | SUBTITLE | BADGE | URL_BACKGROUND]\n"
            "Join VIP - https://t.me/channel\n"
            "Akses Bot - https://t.me/bot</code>"
        )

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> ID channel harus berupa angka.")

    custom_title = "✦ PILIHAN AKSES VIP ✦"
    custom_subtitle = "Silakan pilih menu layanan di bawah ini:"
    custom_badge = "OFFICIAL PORTAL"
    custom_bg = ""

    match = re.search(r"\[(.*?)\]", first_line)
    if match:
        header_data = [h.strip() for h in match.group(1).split("|")]
        if len(header_data) >= 1 and header_data[0]:
            custom_title = header_data[0]
        if len(header_data) >= 2 and header_data[1]:
            custom_subtitle = header_data[1]
        if len(header_data) >= 3 and header_data[2]:
            custom_badge = header_data[2]
        if len(header_data) >= 4 and header_data[3]:
            custom_bg = clean_url(header_data[3])

    webapp_items = []
    for line in lines[1:]:
        if " - " in line:
            name, link = line.split(" - ", 1)
            name = name.strip()
            link = clean_url(link)
            if name and is_valid_url(link):
                webapp_items.append({"text": name, "url": link})

    if not webapp_items:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Format salah! Gunakan pemisah <code> - </code>.")

    temporary = False
    image_msg = find_image_message(message)
    if image_msg:
        status_msg = await safe_reply(message, f"<emoji id={AnimEmoji.JAM_PASIR}>⏳</emoji> <i>Mengunggah background...</i>")
        try:
            custom_bg, temporary = await upload_message_image(image_msg)
        except Exception as e:
            return await safe_edit(status_msg, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> Foto gagal diunggah: <code>{esc(e)}</code>")
        await status_msg.delete()

    payload = {
        "title": custom_title,
        "subtitle": custom_subtitle,
        "badge": custom_badge,
        "background": custom_bg,
        "items": webapp_items,
    }

    bg_info = f"<code>{esc(custom_bg)}</code>" if custom_bg else "<i>(Bawaan)</i>"
    text = (
        f"<emoji id={AnimEmoji.CENTANG}>✅</emoji> <b>Tampilan WebApp Berhasil Disimpan!</b>\n\n"
        f"• <b>Badge:</b> <code>{esc(custom_badge)}</code>\n"
        f"• <b>Judul:</b> <code>{esc(custom_title)}</code>\n"
        f"• <b>Subjudul:</b> <code>{esc(custom_subtitle)}</code>\n"
        f"• <b>Background:</b> {bg_info}\n"
        f"• <b>Channel:</b> <code>{chat_key}</code>\n\n"
        "Pratinjau tombol channel:"
    )
    if temporary:
        text += TEMP_WARNING

    await save_after_preview(message, chat_key, webapp_grid(payload), text)


# ================= CEK TOMBOL =================
@app.on_message(filters.private & filters.command("cekbutton") & is_bot_admin)
async def check_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await safe_reply(message, "Ketik: <code>/cekbutton &lt;ID_CHANNEL&gt;</code>")

    chat_key = parse_channel_id(args[1])
    if chat_key is None:
        return await safe_reply(message, f"<emoji id={AnimEmoji.SILANG}>❌</emoji> ID Channel harus berupa angka.")

    grid = get_all_data().get(chat_key)
    if not grid:
        return await safe_reply(message, f"<emoji id={AnimEmoji.INFO}>ℹ️️</emoji> Belum ada tombol untuk channel <code>{chat_key}</code>.")

    text = f"<emoji id={AnimEmoji.BERLIAN}>💎</emoji> <b>Tombol aktif channel</b> <code>{chat_key}</code>:"
    payload = payload_from_grid(grid)
    if payload is not None:
        bg = payload.get("background")
        text += "\n🖼 Background: " + (f"<code>{esc(bg)}</code>" if bg else "<i>(Bawaan)</i>")

    try:
        markup = build_markup(grid)
        await safe_reply(message, text, reply_markup=markup)
    except Exception as e:
        await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Tombol ditolak Telegram: <code>{esc(e)}</code>")


# ================= HAPUS TOMBOL =================
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
        await safe_reply(message, f"<emoji id={AnimEmoji.SAMPAH}>🗑</emoji> Tombol channel <code>{esc(ch_id)}</code> berhasil dihapus.")
    else:
        await safe_reply(message, f"<emoji id={AnimEmoji.PERINGATAN}>⚠️</emoji> Channel <code>{esc(ch_id)}</code> tidak ditemukan.")


# ================= DAFTAR CHANNEL =================
@app.on_message(filters.private & filters.command("listchannel") & is_bot_admin)
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await safe_reply(message, f"<emoji id={AnimEmoji.INFO}>ℹ️</emoji> Belum ada channel terdaftar.")

    text = f"<emoji id={AnimEmoji.MEGAPHONE}>📣</emoji> <b>Channel dengan Tombol Aktif:</b>\n\n"
    for ch_id, grid in data.items():
        payload = payload_from_grid(grid)
        kind = "WebApp" if payload else "tombol biasa"
        text += f"• <code>{esc(ch_id)}</code> — <i>{kind}</i>\n"
    await safe_reply(message, text)


# ================= AUTO ATTACH CHANNEL VIA USERBOT & FALLBACK =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    cid = message.chat.id
    mid = message.id
    logging.info(f"📢 Pesan baru masuk di channel ID: {cid} (Pesan ID: {mid})")

    if message.service or message.reply_markup:
        return

    markup = get_channel_markup(cid)
    if not markup:
        logging.warning(f"⚠️ ID Channel {cid} tidak ditemukan di database channel_buttons.json!")
        return

    success = False

    # 1. Prioritaskan Userbot Premium agar custom animated emoji hidup
    if user_client:
        try:
            await user_client.edit_message_reply_markup(
                chat_id=cid,
                message_id=mid,
                reply_markup=markup
            )
            success = True
            logging.info(f"✅ Sukses pasang tombol animasi via Userbot di channel {cid}")
        except MessageNotModified:
            success = True
        except FloodWait as flood:
            await asyncio.sleep(flood.value)
            try:
                await user_client.edit_message_reply_markup(chat_id=cid, message_id=mid, reply_markup=markup)
                success = True
            except Exception:
                pass
        except Exception as u_err:
            logging.error(f"❌ Userbot gagal edit markup di channel {cid}: {u_err} (Mencoba fallback via BotFather...)")

    # 2. Fallback cadangan: Gunakan BotFather jika userbot gagal/belum join
    if not success:
        try:
            await client.edit_message_reply_markup(
                chat_id=cid,
                message_id=mid,
                reply_markup=markup
            )
            logging.info(f"✅ Sukses pasang tombol via BotFather (Fallback) di channel {cid}")
        except MessageNotModified:
            pass
        except Exception as b_err:
            logging.error(f"❌ BotFather juga gagal edit markup di channel {cid}: {b_err}")


# ================= MAIN RUNNER =================
async def main():
    await app.start()
    logging.info("Bot Father Client aktif.")

    if user_client:
        await user_client.start()
        logging.info("Userbot Bridge Premium Client aktif & siap memasang tombol ber-emoji.")

    await idle()

    if user_client:
        await user_client.stop()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
