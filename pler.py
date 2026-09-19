import asyncio
import json
import logging
import os

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# ================= KONFIGURASI BOT =================
API_ID = 1634450  # Ganti dengan API ID kamu
API_HASH = "1a42e816cae8d86e71a4c466bba19b8c"  # Ganti dengan API Hash kamu
BOT_TOKEN = "8862325911:AAFZxAdv0K9jTaBQYillPQCbZdYQu-V67-Q"
OWNER_ID = 1492743978  # Ganti dengan User ID Telegram kamu (cek via @userinfobot)

DATA_FILE = "buttons_data.json"

# Inisialisasi file konfigurasi jika belum ada
if not os.path.exists(DATA_FILE):
    default_data = [
        {"text": "🌐 Kunjungi Web", "url": "https://google.com"},
        {"text": "💬 Hubungi Admin", "url": "https://t.me/durov"},
    ]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, indent=4)


def load_buttons() -> InlineKeyboardMarkup:
    """Membaca daftar tombol dari file JSON dan mengubahnya ke markup."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        keyboard = []
        for item in data:
            keyboard.append([InlineKeyboardButton(item["text"], url=item["url"])])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"Gagal memuat tombol: {e}")
        return None


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)


# ================= ATUR BUTTON LEWAT BOT =================
@app.on_message(filters.command("setbutton") & filters.private & filters.user(OWNER_ID))
async def set_buttons_handler(client: Client, message: Message):
    """
    Format penggunaan:
    /setbutton
    Nama Tombol 1 - https://link1.com
    Nama Tombol 2 - https://link2.com
    """
    lines = message.text.split("\n")[1:]

    if not lines:
        return await message.reply_text(
            "⚠️ **Format salah!**\n\n"
            "Kirim perintah seperti contoh berikut:\n"
            "`/setbutton\n"
            "🌐 Website Kami - https://contoh.com\n"
            "💬 Hubungi Admin - https://t.me/username_kamu`"
        )

    new_buttons = []
    for line in lines:
        if " - " in line:
            parts = line.split(" - ", 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()

            if not btn_url.startswith("http"):
                btn_url = "https://" + btn_url

            new_buttons.append({"text": btn_text, "url": btn_url})

    if not new_buttons:
        return await message.reply_text(
            "❌ Tidak ada tombol yang valid terbaca. Pastikan ada pemisah ` - `."
        )

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_buttons, f, indent=4)

    preview_markup = load_buttons()
    await message.reply_text(
        "✅ **Tombol berhasil diperbarui!**\nBerikut preview tombol barunya:",
        reply_markup=preview_markup,
    )


@app.on_message(filters.command("cekbutton") & filters.private & filters.user(OWNER_ID))
async def check_buttons_handler(client: Client, message: Message):
    markup = load_buttons()
    if markup:
        await message.reply_text(
            "📌 **Tombol yang saat ini aktif:**", reply_markup=markup
        )
    else:
        await message.reply_text("Belum ada tombol tersimpan.")


# ================= AUTO ATTACH BUTTON DI CHANNEL =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    if message.reply_markup:
        return

    current_markup = load_buttons()
    if not current_markup:
        return

    try:
        await message.edit_reply_markup(reply_markup=current_markup)
        logging.info(f"Tombol dipasang ke postingan ID {message.id}")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_reply_markup(reply_markup=current_markup)
    except MessageNotModified:
        pass
    except Exception as e:
        logging.error(f"Gagal menambahkan tombol: {e}")


if __name__ == "__main__":
    print("Bot Pengatur Tombol Channel Aktif...")
    app.run()
