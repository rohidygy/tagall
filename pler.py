import asyncio
import json
import logging
import os
import re
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
    "channel_button_manager",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)


def get_all_data() -> dict:
    """Membaca konfigurasi tombol dari file JSON."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Gagal membaca database: {e}")
        return {}


def save_all_data(data: dict):
    """Menyimpan konfigurasi tombol ke file JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_channel_markup(chat_id: int):
    """Menghasilkan InlineKeyboardMarkup untuk ID channel tertentu."""
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


# ================= MENU BANTUAN /START =================
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("👋 Bot aktif untuk mengelola tombol channel.")

    text = (
        f"Halo **{message.from_user.first_name}**! 👋\n\n"
        "**Pilihan Pengaturan Tombol Channel:**\n\n"
        "1️⃣ **Tombol Chat Biasa (`/setbutton`):**\n"
        "Gunakan ini jika ingin tombol link biasa di postingan channel (bisa bersebelahan pakai `|`).\n\n"
        "2️⃣ **Pop-up WebApp Berwarna (`/setweb`):**\n"
        "Gunakan ini jika ingin tombol membuka pop-up menu gradasi warna di Telegram.\n"
        "Judul dan subtitle bisa diatur pakai format `[JUDUL | SUBTITLE | BADGE]`.\n\n"
        "3️⃣ **Perintah Manajemen:**\n"
        "• `/cekbutton <ID_CH>` $\\rightarrow$ Cek tombol aktif channel\n"
        "• `/delbutton <ID_CH>` $\\rightarrow$ Hapus tombol channel\n"
        "• `/listchannel` $\\rightarrow$ Daftar channel yang terpasang\n\n"
        "💡 *Teruskan (forward) pesan dari channel ke bot ini untuk mengecek ID Channel.*"
    )
    await message.reply_text(text)


# ================= DETEKSI ID VIA FORWARD =================
@app.on_message(filters.private & filters.forwarded & filters.user(OWNER_ID))
async def detect_channel_id(client: Client, message: Message):
    if message.forward_from_chat and message.forward_from_chat.type.name == "CHANNEL":
        ch = message.forward_from_chat
        await message.reply_text(
            f"📢 **Channel Terdeteksi:**\n"
            f"• Nama: **{ch.title}**\n"
            f"• ID: `{ch.id}`"
        )


# ================= 1. ATUR TOMBOL CHAT BIASA (/setbutton) =================
@app.on_message(filters.private & filters.command("setbutton") & filters.user(OWNER_ID))
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line_parts = lines[0].split()

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setbutton (Tombol Chat Biasa):**\n\n"
            "`/setbutton -100xxxxxxxxxx\n"
            "🌐 Website Resmi - https://contoh.com\n"
            "💬 Admin 1 - https://t.me/admin1 | 💬 Admin 2 - https://t.me/admin2\n"
            "⚡ Join VIP - https://t.me/channel`"
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
        return await message.reply_text("❌ Format salah! Pastikan menggunakan pemisah spasi-strip-spasi: ` - `.")

    data = get_all_data()
    data[channel_id_str] = button_grid
    save_all_data(data)

    preview = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Tombol Channel Biasa Berhasil Disimpan!**\nChannel: `{channel_id_str}`\n\nPratinjau:",
        reply_markup=preview
    )


# ================= 2. ATUR WEBAPP POP-UP BERWARNA (/setweb) =================
@app.on_message(filters.private & filters.command("setweb") & filters.user(OWNER_ID))
async def set_webapp_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line = lines[0]
    parts = first_line.split()

    if len(parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setweb (WebApp Warna Dinamis):**\n\n"
            "`/setweb -100xxxxxxxxxx [JUDUL | SUBTITLE | BADGE]\n"
            "🔥 Join VIP - https://t.me/channel\n"
            "💎 Akses Bot - https://t.me/bot\n"
            "💬 Admin - https://t.me/admin`\n\n"
            "*Catatan: Bagian dalam kurung siku `[...]` opsional.*"
        )

    channel_id_str = parts[1]

    # Nilai default judul antarmuka WebApp
    custom_title = "✦ PILIHAN AKSES VIP ✦"
    custom_subtitle = "Silakan pilih menu layanan di bawah ini:"
    custom_badge = "OFFICIAL PORTAL"

    # Mengekstrak format [Judul | Subtitle | Badge] jika ditulis
    match = re.search(r"\[(.*?)\]", first_line)
    if match:
        header_data = [h.strip() for h in match.group(1).split("|")]
        if len(header_data) >= 1 and header_data[0]:
            custom_title = header_data[0]
        if len(header_data) >= 2 and header_data[1]:
            custom_subtitle = header_data[1]
        if len(header_data) >= 3 and header_data[2]:
            custom_badge = header_data[2]

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
        return await message.reply_text("❌ Format salah! Gunakan pemisah ` - ` pada setiap baris menu.")

    # Format payload JSON
    payload = {
        "title": custom_title,
        "subtitle": custom_subtitle,
        "badge": custom_badge,
        "items": webapp_items
    }

    # Encode payload ke URL Hash GitHub Pages
    encoded_json = urllib.parse.quote(json.dumps(payload))
    final_webapp_link = f"{BASE_WEBAPP_URL}#{encoded_json}"

    # Tombol pembuka yang ditempel ke channel
    button_structure = [
        [{"text": "✨ ʙᴜᴋᴀ ᴍᴇɴᴜ ᴠɪᴘ ✨", "url": final_webapp_link}]
    ]

    data = get_all_data()
    data[channel_id_str] = button_structure
    save_all_data(data)

    preview = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Tampilan WebApp Berhasil Disimpan!**\n\n"
        f"• **Badge:** `{custom_badge}`\n"
        f"• **Judul:** `{custom_title}`\n"
        f"• **Subjudul:** `{custom_subtitle}`\n"
        f"• **Channel:** `{channel_id_str}`\n\n"
        "Pratinjau tombol channel:",
        reply_markup=preview
    )


# ================= CEK TOMBOL AKTIF =================
@app.on_message(filters.private & filters.command("cekbutton") & filters.user(OWNER_ID))
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


# ================= HAPUS TOMBOL =================
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
        await message.reply_text(f"🗑️ Konfigurasi tombol channel `{ch_id}` berhasil dihapus.")
    else:
        await message.reply_text(f"Channel `{ch_id}` tidak ditemukan di daftar.")


# ================= DAFTAR CHANNEL AKTIF =================
@app.on_message(filters.private & filters.command("listchannel") & filters.user(OWNER_ID))
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await message.reply_text("Belum ada channel terdaftar.")

    text = "📋 **Daftar ID Channel yang Terpasang Tombol:**\n\n"
    for ch_id in data.keys():
        text += f"• `{ch_id}`\n"
    await message.reply_text(text)


# ================= AUTO ATTACH TOMBOL KE POSTINGAN CHANNEL =================
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
