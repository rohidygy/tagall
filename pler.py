import asyncio
import json
import logging
import os
import urllib.parse

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# ================= KONFIGURASI BOT =================
API_ID = 1634450
API_HASH = "1a42e816cae8d86e71a4c466bba19b8c"
BOT_TOKEN = "8862325911:AAFZxAdv0K9jTaBQYillPQCbZdYQu-V67-Q"
OWNER_ID = 1492743978

# Link GitHub Pages milikmu
BASE_WEBAPP_URL = "https://rohidygy.github.io/tagall/"

DATA_FILE = "channel_buttons.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)


def get_all_data() -> dict:
    """Membaca file data tombol channel."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Gagal membaca data file: {e}")
        return {}


def save_all_data(data: dict):
    """Menyimpan data tombol ke file JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_channel_markup(chat_id: int) -> InlineKeyboardMarkup:
    """Mengambil tombol khusus untuk channel tertentu."""
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
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("👋 Bot ini aktif untuk mengelola tombol channel.")

    text = (
        f"Halo **{message.from_user.first_name}**! 👋\n\n"
        "**Cara Setting Tombol Warna Per-Channel:**\n\n"
        "1️⃣ Teruskan (forward) pesan dari channel ke bot ini untuk mendapatkan ID Channel.\n\n"
        "2️⃣ Kirim format perintah:\n"
        "`/setbutton -100xxxxxxxxxx\n"
        "🔥 Gabung Channel VIP - https://t.me/galerinakalwebsite\n"
        "💎 Beli Kode Akses - https://t.me/telegalerinakal_bot\n"
        "💬 Admin 1 (Online) - https://t.me/amiragalerinakal\n"
        "⚡ Admin 2 (Online) - https://t.me/officialgalerinakal`\n\n"
        "3️⃣ Perintah lainnya:\n"
        "• `/cekbutton -100xxxxxxxxxx` (Cek tombol channel)\n"
        "• `/delbutton -100xxxxxxxxxx` (Hapus tombol channel)\n"
        "• `/listchannel` (Lihat daftar channel aktif)"
    )
    await message.reply_text(text)


# ================= DETEKSI ID VIA FORWARD =================
@app.on_message(filters.forwarded & filters.private & filters.user(OWNER_ID))
async def detect_channel_id(client: Client, message: Message):
    if message.forward_from_chat and message.forward_from_chat.type.name == "CHANNEL":
        ch = message.forward_from_chat
        await message.reply_text(
            f"📢 **Channel Terdeteksi:**\n"
            f"• Nama: **{ch.title}**\n"
            f"• ID: `{ch.id}`\n\n"
            f"Gunakan ID ini untuk mengatur tombol:\n"
            f"`/setbutton {ch.id}`"
        )


# ================= ATUR BUTTON PER-CHANNEL =================
@app.on_message(filters.command("setbutton") & filters.private & filters.user(OWNER_ID))
async def set_buttons_handler(client: Client, message: Message):
    parts = message.text.split("\n", 1)
    header = parts[0].strip().split()

    if len(header) < 2 or len(parts) < 2:
        return await message.reply_text(
            "⚠️ **Format salah!**\n\n"
            "Contoh:\n"
            "`/setbutton -100xxxxxxxxxx\n"
            "Channel VIP - https://t.me/channel\n"
            "Beli Akses - https://t.me/bot\n"
            "Admin - https://t.me/admin`"
        )

    channel_id_str = header[1]
    lines = parts[1].strip().split("\n")

    webapp_items = []
    for line in lines:
        if " - " in line:
            btn_text, btn_url = line.split(" - ", 1)
            btn_url = btn_url.strip()
            if not btn_url.startswith("http://") and not btn_url.startswith("https://"):
                btn_url = "https://" + btn_url
            webapp_items.append({"text": btn_text.strip(), "url": btn_url})

    if not webapp_items:
        return await message.reply_text("❌ Tidak ada tombol yang valid. Gunakan pemisah ` - `.")

    # Encode list tombol menjadi hash URL untuk dibaca GitHub Pages
    encoded_json = urllib.parse.quote(json.dumps(webapp_items))
    final_webapp_link = f"{BASE_WEBAPP_URL}#{encoded_json}"

    # Tombol utama yang menempel di postingan channel
    button_structure = [
        [{"text": "✨ ʙᴜᴋᴀ ᴍᴇɴᴜ ᴠɪᴘ ✨", "url": final_webapp_link}]
    ]

    data = get_all_data()
    data[channel_id_str] = button_structure
    save_all_data(data)

    preview_markup = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Menu warna berhasil disimpan untuk Channel:** `{channel_id_str}`\n\nPratinjau tombol di channel:",
        reply_markup=preview_markup,
    )


# ================= CEK BUTTON CHANNEL =================
@app.on_message(filters.command("cekbutton") & filters.private & filters.user(OWNER_ID))
async def check_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("Ketik: `/cekbutton <ID_CHANNEL>`")

    ch_id = args[1]
    try:
        markup = get_channel_markup(int(ch_id))
        if markup:
            await message.reply_text(f"📌 **Tombol aktif channel** `{ch_id}`:", reply_markup=markup)
        else:
            await message.reply_text(f"Belum ada tombol tersimpan untuk channel `{ch_id}`.")
    except ValueError:
        await message.reply_text("ID Channel harus berupa angka.")


# ================= HAPUS BUTTON CHANNEL =================
@app.on_message(filters.command("delbutton") & filters.private & filters.user(OWNER_ID))
async def delete_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("Ketik: `/delbutton <ID_CHANNEL>`")

    ch_id = args[1]
    data = get_all_data()

    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await message.reply_text(f"🗑️ Tombol untuk channel `{ch_id}` berhasil dihapus.")
    else:
        await message.reply_text(f"Channel `{ch_id}` tidak memiliki konfigurasi tombol.")


# ================= DAFTAR CHANNEL =================
@app.on_message(filters.command("listchannel") & filters.private & filters.user(OWNER_ID))
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await message.reply_text("Belum ada channel yang terdaftar.")

    text = "📋 **Daftar ID Channel yang Terpasang Tombol:**\n\n"
    for ch_id in data.keys():
        text += f"• `{ch_id}`\n"
    await message.reply_text(text)


# ================= AUTO ATTACH BUTTON DI CHANNEL =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    if message.reply_markup:
        return

    current_markup = get_channel_markup(message.chat.id)
    if not current_markup:
        return

    try:
        await message.edit_reply_markup(reply_markup=current_markup)
        logging.info(f"Tombol dipasang di channel {message.chat.id} (Pesan ID: {message.id})")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(reply_markup=current_markup)
    except MessageNotModified:
        pass
    except Exception as e:
        logging.error(f"Gagal menempelkan tombol di pesan {message.id}: {e}")


if __name__ == "__main__":
    print("Bot Pengatur Tombol Per-Channel Aktif...")
    app.run()
