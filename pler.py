import asyncio
import json
import logging
import os

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# ================= KONFIGURASI BOT =================
API_ID = 1634450
API_HASH = "1a42e816cae8d86e71a4c466bba19b8c"
BOT_TOKEN = "8862325911:AAFZxAdv0K9jTaBQYillPQCbZdYQu-V67-Q"
OWNER_ID = 1492743978

DATA_FILE = "buttons_data.json"

# Inisialisasi file konfigurasi jika belum ada
if not os.path.exists(DATA_FILE):
    default_data = [
        [{"text": "🌐 Kunjungi Web", "url": "https://google.com"}],
        [{"text": "💬 Hubungi Admin", "url": "https://t.me/durov"}]
    ]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(default_data, f, indent=4)


def load_buttons() -> InlineKeyboardMarkup:
    """Membaca susunan baris dan tombol dari file JSON."""
    if not os.path.exists(DATA_FILE):
        return None
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            return None

        keyboard = []
        for row in data:
            row_buttons = []
            for item in row:
                row_buttons.append(InlineKeyboardButton(item["text"], url=item["url"]))
            keyboard.append(row_buttons)

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


# ================= COMMAND /START =================
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("👋 Halo! Bot ini digunakan untuk mengelola tombol channel secara otomatis.")

    text = (
        f"Halo **{message.from_user.first_name}**! 👋\n\n"
        "Kamu terdaftar sebagai **Owner** bot ini.\n\n"
        "**Perintah yang tersedia:**\n"
        "• `/setbutton` - Mengatur susunan tombol baru\n"
        "• `/cekbutton` - Melihat susunan tombol yang saat ini aktif\n"
        "• `/delbutton` - Menghapus semua tombol yang tersimpan\n\n"
        "**Contoh cara set tombol (dukung baris ke samping):**\n"
        "`/setbutton\n"
        "Website - https://google.com\n"
        "Admin 1 - https://t.me/admin1 | Admin 2 - https://t.me/admin2\n"
        "Channel - https://t.me/channel`\n\n"
        "*(Gunakan simbol `|` untuk meletakkan tombol sejajar ke samping)*"
    )
    await message.reply_text(text)


# ================= ATUR BUTTON LEWAT BOT =================
@app.on_message(filters.command("setbutton") & filters.private & filters.user(OWNER_ID))
async def set_buttons_handler(client: Client, message: Message):
    lines = message.text.split("\n")[1:]

    if not lines:
        return await message.reply_text(
            "⚠️ **Format salah!**\n\n"
            "Contoh penggunaan:\n"
            "`/setbutton\n"
            "🌐 Website - https://contoh.com\n"
            "💬 Admin 1 - https://t.me/admin1 | 💬 Admin 2 - https://t.me/admin2`\n\n"
            "Gunakan ` - ` sebagai pemisah teks & URL, dan `|` jika ingin tombol berada di baris yang sama."
        )

    keyboard_structure = []
    for line in lines:
        row_segments = line.split("|")
        row_buttons = []
        for segment in row_segments:
            if " - " in segment:
                parts = segment.split(" - ", 1)
                btn_text = parts[0].strip()
                btn_url = parts[1].strip()

                if not btn_url.startswith("http://") and not btn_url.startswith("https://"):
                    btn_url = "https://" + btn_url

                row_buttons.append({"text": btn_text, "url": btn_url})

        if row_buttons:
            keyboard_structure.append(row_buttons)

    if not keyboard_structure:
        return await message.reply_text(
            "❌ Tidak ada tombol yang valid terbaca. Pastikan ada pemisah ` - ` antara teks dan URL."
        )

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(keyboard_structure, f, indent=4)

    preview_markup = load_buttons()
    await message.reply_text(
        "✅ **Tombol berhasil diperbarui!**\nBerikut pratinjau tombol barunya:",
        reply_markup=preview_markup,
    )


# ================= CEK BUTTON SAAT INI =================
@app.on_message(filters.command("cekbutton") & filters.private & filters.user(OWNER_ID))
async def check_buttons_handler(client: Client, message: Message):
    markup = load_buttons()
    if markup:
        await message.reply_text(
            "📌 **Tombol yang saat ini aktif:**", reply_markup=markup
        )
    else:
        await message.reply_text("Belum ada tombol tersimpan.")


# ================= HAPUS BUTTON =================
@app.on_message(filters.command("delbutton") & filters.private & filters.user(OWNER_ID))
async def delete_buttons_handler(client: Client, message: Message):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    await message.reply_text("🗑️ **Semua tombol berhasil dihapus.** Postingan channel baru tidak akan diberi tombol sampai kamu mengatur tombol baru via `/setbutton`.")


# ================= AUTO ATTACH BUTTON DI CHANNEL =================
@app.on_message(filters.channel)
async def auto_button_channel(client: Client, message: Message):
    # Lewati jika pesan sudah punya tombol inline
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
        logging.error(f"Gagal menambahkan tombol ke pesan {message.id}: {e}")


if __name__ == "__main__":
    print("Bot Pengatur Tombol Channel Aktif...")
    app.run()
