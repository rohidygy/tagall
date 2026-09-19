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

# Link GitHub Pages kamu
BASE_WEBAPP_URL = "https://rohidygy.github.io/tagall/"

DATA_FILE = "channel_buttons.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)


def get_all_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Gagal membaca data: {e}")
        return {}


def save_all_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


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
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("👋 Bot aktif untuk mengelola channel.")

    text = (
        f"Halo **{message.from_user.first_name}**! 👋\n\n"
        "**Daftar Perintah Terpisah:**\n\n"
        "1️⃣ **`/setbutton <ID_CH>`**\n"
        "Atur tombol biasa di channel (bisa sejajar pakai `|`).\n\n"
        "2️⃣ **`/setweb <ID_CH>`**\n"
        "Atur menu daftar link untuk pop-up **WebApp Berwarna**.\n\n"
        "3️⃣ **Perintah Manajemen:**\n"
        "• `/cekbutton <ID_CH>` $\\rightarrow$ Cek tombol aktif\n"
        "• `/delbutton <ID_CH>` $\\rightarrow$ Hapus tombol channel\n"
        "• `/listchannel` $\\rightarrow$ Daftar channel aktif\n\n"
        "💡 *Teruskan (forward) pesan dari channel ke bot ini untuk deteksi ID.*"
    )
    await message.reply_text(text)


# ================= DETEKSI ID CHANNEL VIA FORWARD =================
@app.on_message(filters.private & filters.forwarded & filters.user(OWNER_ID))
async def detect_channel_id(client: Client, message: Message):
    if message.forward_from_chat and message.forward_from_chat.type.name == "CHANNEL":
        ch = message.forward_from_chat
        await message.reply_text(
            f"📢 **Channel Terdeteksi:**\n"
            f"• Nama: **{ch.title}**\n"
            f"• ID: `{ch.id}`"
        )


# ================= 1. SET BUTTON BIASA DI POSTINGAN CHANNEL =================
@app.on_message(filters.private & filters.command("setbutton") & filters.user(OWNER_ID))
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line_parts = lines[0].split()

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setbutton (Tombol Biasa):**\n\n"
            "`/setbutton -100xxxxxxxxxx\n"
            "🌐 Website - https://contoh.com\n"
            "💬 Admin 1 - https://t.me/admin1 | 💬 Admin 2 - https://t.me/admin2\n"
            "📢 Join Channel - https://t.me/channel`"
        )

    channel_id_str = first_line_parts[1]
    btn_lines = lines[1:]

    button_grid = []
    for line in btn_lines:
        row = []
        raw_buttons = line.split("|")
        for btn in raw_buttons:
            if " - " in btn:
                text, url = btn.split(" - ", 1)
                url = url.strip()
                if not url.startswith("http://") and not url.startswith("https://"):
                    url = "https://" + url
                row.append({"text": text.strip(), "url": url})
        if row:
            button_grid.append(row)

    if not button_grid:
        return await message.reply_text(
            "❌ Tidak ada tombol yang valid. Gunakan pemisah ` - `."
        )

    data = get_all_data()
    data[channel_id_str] = button_grid
    save_all_data(data)

    preview = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Tombol Channel Biasa Disimpan:** `{channel_id_str}`\n\nPratinjau:",
        reply_markup=preview,
    )


# ================= 2. SET WEBAPP POP-UP BERWARNA =================
@app.on_message(filters.private & filters.command("setweb") & filters.user(OWNER_ID))
async def set_webapp_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line_parts = lines[0].split()

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setweb (WebApp Warna-Warni):**\n\n"
            "`/setweb -100xxxxxxxxxx\n"
            "🔥 Join VIP - https://t.me/channelvip\n"
            "💎 Akses Bot - https://t.me/telegalerinakal_bot\n"
            "💬 Admin 1 - https://t.me/amiragalerinakal\n"
            "⚡ Admin 2 - https://t.me/officialgalerinakal`"
        )

    channel_id_str = first_line_parts[1]
    btn_lines = lines[1:]

    webapp_items = []
    for line in btn_lines:
        if " - " in line:
            name, link = line.split(" - ", 1)
            link = link.strip()
            if not link.startswith("http://") and not link.startswith("https://"):
                link = "https://" + link
            webapp_items.append({"text": name.strip(), "url": link})

    if not webapp_items:
        return await message.reply_text("❌ Format salah! Gunakan pemisah ` - `.")

    # Encode list tombol menjadi hash URL untuk GitHub Pages
    encoded_json = urllib.parse.quote(json.dumps(webapp_items))
    final_webapp_link = f"{BASE_WEBAPP_URL}#{encoded_json}"

    # Tombol pembuka WebApp yang menempel di postingan channel
    button_structure = [[{"text": "✨ ʙᴜᴋᴀ ᴍᴇɴᴜ ᴠɪᴘ ✨", "url": final_webapp_link}]]

    data = get_all_data()
    data[channel_id_str] = button_structure
    save_all_data(data)

    preview = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Menu WebApp Warna Disimpan untuk Channel:** `{channel_id_str}`\n\nPratinjau tombol channel:",
        reply_markup=preview,
    )


# ================= CEK BUTTON =================
@app.on_message(filters.private & filters.command("cekbutton") & filters.user(OWNER_ID))
async def check_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("Ketik: `/cekbutton <ID_CHANNEL>`")

    ch_id = args[1]
    try:
        markup = get_channel_markup(int(ch_id))
        if markup:
            await message.reply_text(
                f"📌 **Tombol aktif channel** `{ch_id}`:", reply_markup=markup
            )
        else:
            await message.reply_text(f"Belum ada tombol untuk channel `{ch_id}`.")
    except ValueError:
        await message.reply_text("ID Channel harus berupa angka.")


# ================= HAPUS BUTTON =================
@app.on_message(filters.private & filters.command("delbutton") & filters.user(OWNER_ID))
async def delete_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("Ketik: `/delbutton <ID_CHANNEL>`")

    ch_id = args[1]
    data = get_all_data()

    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await message.reply_text(f"🗑️ Tombol channel `{ch_id}` berhasil dihapus.")
    else:
        await message.reply_text(f"Channel `{ch_id}` tidak ditemukan di konfigurasi.")


# ================= LIST CHANNEL =================
@app.on_message(
    filters.private & filters.command("listchannel") & filters.user(OWNER_ID)
)
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await message.reply_text("Belum ada channel terdaftar.")

    text = "📋 **Channel dengan Tombol Aktif:**\n\n"
    for ch_id in data.keys():
        text += f"• `{ch_id}`\n"
    await message.reply_text(text)


# ================= AUTO ATTACH KE POSTINGAN CHANNEL =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    if message.reply_markup:
        return

    markup = get_channel_markup(message.chat.id)
    if not markup:
        return

    try:
        await message.edit_reply_markup(reply_markup=markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(reply_markup=markup)
    except (MessageNotModified, Exception):
        pass


if __name__ == "__main__":
    print("Bot Pengatur Tombol Aktif...")
    app.run()
