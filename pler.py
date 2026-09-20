import asyncio
import html
import json
import logging
import os
import re
import sys
import urllib.parse
from typing import Optional, Tuple

import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ================= KONFIGURASI BOT =================
# Rahasia (API_HASH, BOT_TOKEN, dst.) TIDAK ditulis di kode lagi.
# Isi lewat environment variable atau file `.env` di folder yang sama:
#   API_ID=123456
#   API_HASH=xxxxxxxx
#   BOT_TOKEN=123:ABC
#   OWNER_ID=1492743978        (opsional)
#   IMGBB_KEY=xxxxxxxx         (opsional, agar foto tersimpan PERMANEN & lebih stabil)
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
        sys.exit(
            f"❌ Variabel {name} belum diisi (environment variable atau file .env)."
        )
    return value


API_ID = int(_require_env("API_ID"))
API_HASH = _require_env("API_HASH")
BOT_TOKEN = _require_env("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID", "1492743978"))  # Super Admin / Pemilik Utama
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
    """Escape teks dinamis agar aman dipakai di pesan HTML."""
    return html.escape(str(value))


def command_text(message: Message) -> str:
    """Teks perintah, baik dari pesan biasa maupun caption foto."""
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
    # Tulis ke file sementara lalu ganti (atomic) supaya data tidak rusak
    # kalau bot mati di tengah proses menyimpan.
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


# ================= HELPER URL & CHANNEL =================
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def clean_url(raw_url: str) -> str:
    url = raw_url.strip().replace(" ", "")
    if not _SCHEME_RE.match(url):  # skema lain (mis. tg://) dibiarkan apa adanya
        url = "https://" + url
    return url


def is_valid_url(url: str) -> bool:
    return url.startswith("tg://") or "." in url


def parse_channel_id(raw: str) -> Optional[str]:
    """Pastikan ID channel berupa angka, kembalikan dalam bentuk string ternormalisasi."""
    try:
        return str(int(raw.strip()))
    except (ValueError, AttributeError):
        return None


def build_markup(grid: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(item["text"], url=item["url"]) for item in row]
            for row in grid
        ]
    )


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
    return [[{"text": WEBAPP_BUTTON_TEXT, "url": build_webapp_link(payload)}]]


async def save_after_preview(
    message: Message, chat_key: str, grid: list, text: str
) -> bool:
    """Kirim pratinjau dulu; hanya simpan kalau Telegram menerima tombolnya.
    (Sebelumnya tombol yang ditolak Telegram tetap tersimpan dan merusak auto-attach.)
    """
    try:
        await message.reply_text(text, reply_markup=build_markup(grid))
    except Exception as e:
        await message.reply_text(
            "⚠️ <b>Tidak disimpan</b> — Telegram menolak tombol ini:\n"
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
    """Upload gambar. Return (direct_url, sementara?)."""
    with open(file_path, "rb") as f:
        content = f.read()
    filename = os.path.basename(file_path)

    providers = []
    if IMGBB_KEY:
        providers.append(("ImgBB", _upload_imgbb, False))
    providers.append(("Catbox", _upload_catbox, False))
    providers.append(("tmpfiles", _upload_tmpfiles, True))  # file hilang ±60 menit

    errors = []
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(
        headers=UPLOAD_HEADERS, timeout=timeout
    ) as session:
        for name, func, temporary in providers:
            try:
                return await func(session, content, filename), temporary
            except Exception as err:
                logging.warning(f"Upload ke {name} gagal: {err}")
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
    """Foto bisa dikirim bersama caption perintah, atau perintah membalas sebuah foto."""
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
    "\n\n⚠️ <i>Foto ini diunggah ke server sementara (tmpfiles) dan akan hilang "
    "sekitar 60 menit. Isi <code>IMGBB_KEY</code> di file .env agar foto permanen.</i>"
)


# ================= COMMAND /START =================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id
    admins = get_admins()

    if user_id not in admins:
        return await message.reply_text(
            "👋 Bot ini aktif untuk mengelola tombol channel."
        )

    is_owner = user_id == OWNER_ID
    role_text = "👑 <b>Owner Utama</b>" if is_owner else "🛠 <b>Admin Terdaftar</b>"

    text = (
        f"Halo <b>{esc(message.from_user.first_name)}</b>! ({role_text})\n\n"
        "<b>Perintah Pengaturan Tombol:</b>\n"
        "• <code>/setbutton &lt;ID_CH&gt;</code> → Tombol link biasa di channel\n"
        "• <code>/setweb &lt;ID_CH&gt; [JUDUL | SUBTITLE | BADGE | BG_URL]</code> → Mini App WebApp\n"
        "• Kirim <b>foto</b> dengan caption <code>/setweb ...</code> (atau balas foto dengan "
        "<code>/setweb ...</code>) → foto otomatis jadi background\n"
        "• <code>/setfoto &lt;ID_CH&gt;</code> + foto → Ganti foto background WebApp yang sudah ada\n"
        "• <code>/delfoto &lt;ID_CH&gt;</code> → Hapus foto background WebApp\n"
        "• <code>/setimg</code> + foto → Upload foto jadi link saja\n"
        "• <code>/cekbutton &lt;ID_CH&gt;</code> → Cek tombol channel\n"
        "• <code>/delbutton &lt;ID_CH&gt;</code> → Hapus tombol channel\n"
        "• <code>/listchannel</code> → Daftar channel aktif\n\n"
        "💡 <i>Teruskan (forward) pesan dari channel ke bot untuk mendapatkan ID.</i>"
    )

    if is_owner:
        text += (
            "\n\n<b>Perintah Khusus Owner:</b>\n"
            "• <code>/update</code> → Git pull &amp; otomatis restart\n"
            "• <code>/restart</code> → Restart bot langsung dari chat\n"
            "• <code>/addadmin &lt;USER_ID&gt;</code> → Tambah hak akses admin\n"
            "• <code>/deladmin &lt;USER_ID&gt;</code> → Cabut hak akses admin\n"
            "• <code>/listadmin</code> → Daftar semua admin"
        )

    await message.reply_text(text)


# ================= UPLOAD GAMBAR (/setimg) =================
@app.on_message(filters.private & filters.command("setimg") & is_bot_admin)
async def set_image_handler(client: Client, message: Message):
    image_msg = find_image_message(message)
    if not image_msg:
        return await message.reply_text(
            "⚠️ <b>Cara Penggunaan:</b>\n"
            "• Kirim foto dengan caption <code>/setimg</code>, atau\n"
            "• Balas (reply) foto dengan <code>/setimg</code>."
        )

    status_msg = await message.reply_text(
        "⏳ <i>Sedang memproses dan mengunggah gambar...</i>"
    )
    try:
        direct_url, temporary = await upload_message_image(image_msg)
        text = (
            "✅ <b>Gambar Berhasil Diunggah!</b>\n\n"
            f"🔗 <b>Direct URL:</b>\n<code>{esc(direct_url)}</code>\n\n"
            "💡 <b>Format Pakai di /setweb:</b>\n"
            f"<code>/setweb &lt;ID_CH&gt; [JUDUL | SUBTITLE | BADGE | {esc(direct_url)}]</code>\n\n"
            "Atau lebih mudah: kirim foto dengan caption <code>/setweb ...</code> / <code>/setfoto ...</code>."
        )
        if temporary:
            text += TEMP_WARNING
        await status_msg.edit_text(text)
    except Exception as e:
        await status_msg.edit_text(f"❌ Gagal memproses gambar: <code>{esc(e)}</code>")


# ================= SET FOTO BACKGROUND WEBAPP (/setfoto, /delfoto) =================
@app.on_message(filters.private & filters.command("setfoto") & is_bot_admin)
async def set_photo_handler(client: Client, message: Message):
    parts = command_text(message).split()
    image_msg = find_image_message(message)

    if len(parts) < 2 or not image_msg:
        return await message.reply_text(
            "⚠️ <b>Cara Penggunaan /setfoto:</b>\n"
            "• Kirim foto dengan caption <code>/setfoto -100xxxxxxxxxx</code>, atau\n"
            "• Balas (reply) foto dengan <code>/setfoto -100xxxxxxxxxx</code>\n\n"
            "<i>Mengganti foto background pada tampilan WebApp channel yang sudah dibuat "
            "dengan /setweb.</i>"
        )

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await message.reply_text(
            "❌ ID channel harus berupa angka, contoh: <code>-1001234567890</code>"
        )

    payload = payload_from_grid(get_all_data().get(chat_key))
    if payload is None:
        return await message.reply_text(
            f"❌ Channel <code>{chat_key}</code> belum punya tampilan WebApp.\n"
            "Buat dulu dengan <code>/setweb</code> (boleh sekalian sertakan foto)."
        )

    status_msg = await message.reply_text("⏳ <i>Mengunggah foto...</i>")
    try:
        bg_url, temporary = await upload_message_image(image_msg)
    except Exception as e:
        return await status_msg.edit_text(
            f"❌ Foto gagal diunggah: <code>{esc(e)}</code>"
        )
    await status_msg.delete()

    payload["background"] = bg_url
    text = (
        "✅ <b>Foto Background Berhasil Diganti!</b>\n\n"
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
        return await message.reply_text(
            "Ketik: <code>/delfoto &lt;ID_CHANNEL&gt;</code>"
        )

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await message.reply_text("❌ ID channel harus berupa angka.")

    payload = payload_from_grid(get_all_data().get(chat_key))
    if payload is None:
        return await message.reply_text(
            f"❌ Channel <code>{chat_key}</code> belum punya tampilan WebApp."
        )

    payload["background"] = ""
    await save_after_preview(
        message,
        chat_key,
        webapp_grid(payload),
        f"🗑️ Foto background channel <code>{chat_key}</code> dihapus (kembali ke bawaan).",
    )


# ================= FITUR GIT PULL & RESTART (OWNER ONLY) =================
def restart_process():
    os.execl(sys.executable, sys.executable, *sys.argv)


@app.on_message(filters.private & filters.command("update") & filters.user(OWNER_ID))
async def git_pull_handler(client: Client, message: Message):
    msg = await message.reply_text("🔄 <b>Menjalankan git pull...</b>")
    try:
        # Async supaya bot tidak "membeku" selama git pull berjalan.
        proc = await asyncio.create_subprocess_exec(
            "git",
            "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=BASE_DIR,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            return await msg.edit_text("❌ <b>git pull timeout (30 detik).</b>")

        output = (
            stdout.decode(errors="replace") + stderr.decode(errors="replace")
        ).strip()
        hasil = esc(output[-3000:]) if output else "Tidak ada perubahan."

        if proc.returncode != 0:
            return await msg.edit_text(
                f"❌ <b>git pull gagal:</b>\n<pre>{hasil}</pre>\n\nBot tidak di-restart."
            )

        await msg.edit_text(
            f"📦 <b>Hasil Git Pull:</b>\n<pre>{hasil}</pre>\n\n♻️ <i>Memulai ulang bot...</i>"
        )
        await asyncio.sleep(1.5)
        restart_process()
    except Exception as e:
        await msg.edit_text(f"❌ <b>Gagal update/restart:</b>\n<code>{esc(e)}</code>")


@app.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_bot_handler(client: Client, message: Message):
    await message.reply_text("♻️ <b>Memulai ulang bot... Tunggu beberapa detik.</b>")
    await asyncio.sleep(1)
    restart_process()


# ================= MANAJEMEN AKSES ADMIN (OWNER ONLY) =================
def get_forward_info(message: Message):
    """Return (chat_asal, user_asal). Kompatibel dengan Pyrogram lama & versi baru
    yang memakai forward_origin."""
    origin = getattr(message, "forward_origin", None)
    if origin is not None:
        return getattr(origin, "chat", None), getattr(origin, "sender_user", None)
    return getattr(message, "forward_from_chat", None), getattr(
        message, "forward_from", None
    )


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
                return await message.reply_text("⚠️ User ID harus berupa angka.")

    if not target_id:
        return await message.reply_text(
            "⚠️ Format: <code>/addadmin &lt;USER_ID&gt;</code>"
        )

    admins = get_admins()
    if target_id in admins:
        return await message.reply_text(
            f"Pengguna <code>{target_id}</code> sudah menjadi admin."
        )

    admins.append(target_id)
    save_admins(admins)
    await message.reply_text(
        f"✅ User ID <code>{target_id}</code> berhasil diberi akses admin."
    )


@app.on_message(filters.private & filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_handler(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text(
            "⚠️ Format: <code>/deladmin &lt;USER_ID&gt;</code>"
        )

    try:
        target_id = int(parts[1])
    except ValueError:
        return await message.reply_text("⚠️ User ID harus berupa angka.")

    if target_id == OWNER_ID:
        return await message.reply_text("❌ Owner utama tidak dapat dihapus.")

    admins = get_admins()
    if target_id not in admins:
        return await message.reply_text(
            f"User ID <code>{target_id}</code> tidak ada di daftar admin."
        )

    admins.remove(target_id)
    save_admins(admins)
    await message.reply_text(
        f"🗑️ Akses untuk <code>{target_id}</code> berhasil dicabut."
    )


@app.on_message(filters.private & filters.command("listadmin") & filters.user(OWNER_ID))
async def list_admin_handler(client: Client, message: Message):
    text = "👥 <b>Daftar Admin Bot:</b>\n\n"
    for uid in get_admins():
        if uid == OWNER_ID:
            text += f"• <code>{uid}</code> 👑 <i>(Owner)</i>\n"
        else:
            text += f"• <code>{uid}</code> 🛠 <i>(Admin)</i>\n"
    await message.reply_text(text)


# ================= DETEKSI ID FORWARD =================
@app.on_message(filters.private & filters.forwarded & is_bot_admin)
async def detect_forward(client: Client, message: Message):
    fwd_chat, fwd_user = get_forward_info(message)

    if fwd_chat and fwd_chat.type == ChatType.CHANNEL:
        await message.reply_text(
            "📢 <b>Channel Terdeteksi:</b>\n"
            f"• Nama: <b>{esc(fwd_chat.title)}</b>\n"
            f"• ID: <code>{fwd_chat.id}</code>"
        )
    elif fwd_user:
        await message.reply_text(
            "👤 <b>Pengguna Terdeteksi:</b>\n"
            f"• Nama: <b>{esc(fwd_user.first_name)}</b>\n"
            f"• ID: <code>{fwd_user.id}</code>"
        )


# ================= ATUR TOMBOL BIASA (/setbutton) =================
@app.on_message(filters.private & filters.command("setbutton") & is_bot_admin)
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [
        line.strip() for line in command_text(message).splitlines() if line.strip()
    ]
    first_line_parts = lines[0].split() if lines else []

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ <b>Format /setbutton:</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "🌐 Website - https://contoh.com\n"
            "💬 Admin 1 - https://t.me/admin1 | 💬 Admin 2 - https://t.me/admin2\n"
            "⚡ Join VIP - https://t.me/channel</code>"
        )

    chat_key = parse_channel_id(first_line_parts[1])
    if chat_key is None:
        return await message.reply_text(
            "❌ ID channel harus berupa angka, contoh: <code>-1001234567890</code>"
        )

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
        return await message.reply_text(
            "❌ Format salah! Pastikan menggunakan pemisah spasi strip spasi: <code> - </code>"
        )

    await save_after_preview(
        message,
        chat_key,
        button_grid,
        f"✅ <b>Tombol Channel Biasa Berhasil Disimpan!</b>\nChannel: <code>{chat_key}</code>\n\nPratinjau:",
    )


# ================= ATUR WEBAPP POP-UP (/setweb) =================
@app.on_message(filters.private & filters.command("setweb") & is_bot_admin)
async def set_webapp_buttons_handler(client: Client, message: Message):
    lines = [
        line.strip() for line in command_text(message).splitlines() if line.strip()
    ]
    first_line = lines[0] if lines else ""
    parts = first_line.split()

    if len(parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ <b>Format /setweb:</b>\n\n"
            "<code>/setweb -100xxxxxxxxxx [JUDUL | SUBTITLE | BADGE | URL_BACKGROUND]\n"
            "🔥 Join VIP - https://t.me/channel\n"
            "💎 Akses Bot - https://t.me/bot\n"
            "💬 Admin - https://t.me/admin</code>\n\n"
            "<i>Catatan:\n"
            "• URL_BACKGROUND bersifat opsional.\n"
            "• Mau pakai foto langsung? Kirim foto dengan caption format di atas, "
            "atau balas foto dengan perintah tersebut.</i>"
        )

    chat_key = parse_channel_id(parts[1])
    if chat_key is None:
        return await message.reply_text(
            "❌ ID channel harus berupa angka, contoh: <code>-1001234567890</code>"
        )

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
        return await message.reply_text(
            "❌ Format salah! Gunakan pemisah <code> - </code>."
        )

    # Foto yang dikirim/di-reply MENGGANTIKAN URL background manual.
    temporary = False
    image_msg = find_image_message(message)
    if image_msg:
        status_msg = await message.reply_text("⏳ <i>Mengunggah foto background...</i>")
        try:
            custom_bg, temporary = await upload_message_image(image_msg)
        except Exception as e:
            return await status_msg.edit_text(
                f"❌ Foto gagal diunggah, pengaturan <b>tidak disimpan</b>:\n<code>{esc(e)}</code>"
            )
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
        "✅ <b>Tampilan WebApp Berhasil Disimpan!</b>\n\n"
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
        return await message.reply_text(
            "Ketik: <code>/cekbutton &lt;ID_CHANNEL&gt;</code>"
        )

    chat_key = parse_channel_id(args[1])
    if chat_key is None:
        return await message.reply_text("ID Channel harus berupa angka.")

    grid = get_all_data().get(chat_key)
    if not grid:
        return await message.reply_text(
            f"Belum ada tombol untuk channel <code>{chat_key}</code>."
        )

    text = f"📌 <b>Tombol aktif channel</b> <code>{chat_key}</code>:"
    payload = payload_from_grid(grid)
    if payload is not None:
        bg = payload.get("background")
        text += "\n🖼 Background: " + (
            f"<code>{esc(bg)}</code>" if bg else "<i>(Bawaan)</i>"
        )

    try:
        await message.reply_text(text, reply_markup=build_markup(grid))
    except Exception as e:
        await message.reply_text(
            f"⚠️ Tombol tersimpan tapi ditolak Telegram:\n<code>{esc(e)}</code>"
        )


# ================= HAPUS TOMBOL =================
@app.on_message(filters.private & filters.command("delbutton") & is_bot_admin)
async def delete_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text(
            "Ketik: <code>/delbutton &lt;ID_CHANNEL&gt;</code>"
        )

    ch_id = parse_channel_id(args[1]) or args[1]
    data = get_all_data()

    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await message.reply_text(
            f"🗑️ Tombol channel <code>{esc(ch_id)}</code> berhasil dihapus."
        )
    else:
        await message.reply_text(f"Channel <code>{esc(ch_id)}</code> tidak ditemukan.")


# ================= DAFTAR CHANNEL =================
@app.on_message(filters.private & filters.command("listchannel") & is_bot_admin)
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await message.reply_text("Belum ada channel terdaftar.")

    text = "📋 <b>Channel dengan Tombol Aktif:</b>\n\n"
    for ch_id, grid in data.items():
        payload = payload_from_grid(grid)
        if payload is None:
            kind = "tombol biasa"
        elif payload.get("background"):
            kind = "WebApp 🖼"
        else:
            kind = "WebApp"
        text += f"• <code>{esc(ch_id)}</code> — <i>{kind}</i>\n"
    await message.reply_text(text)


# ================= AUTO ATTACH CHANNEL =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    logging.info(
        f"Pesan baru masuk di channel ID: {message.chat.id} (Pesan ID: {message.id})"
    )

    if message.service or message.reply_markup:
        return

    markup = get_channel_markup(message.chat.id)
    if not markup:
        logging.warning(
            f"ID Channel {message.chat.id} tidak ditemukan di database tombol!"
        )
        return

    try:
        try:
            await message.edit_reply_markup(reply_markup=markup)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.edit_reply_markup(reply_markup=markup)
        logging.info(f"✅ Berhasil pasang tombol di channel {message.chat.id}")
    except MessageNotModified:
        pass
    except Exception as e:
        logging.error(f"❌ Gagal edit markup di channel {message.chat.id}: {e}")


if __name__ == "__main__":
    print("Bot Pengatur Tombol Aktif...")
    app.run()
