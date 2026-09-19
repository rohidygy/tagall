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
OWNER_ID = 1492743978  # Super Admin / Pemilik Utama

BASE_WEBAPP_URL = "https://rohidygy.github.io/tagall/"

DATA_FILE = "channel_buttons.json"
ADMINS_FILE = "bot_admins.json"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_manager", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
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
    """Mengambil daftar ID admin terdaftar."""
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
    """Menyimpan daftar admin ke file JSON."""
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=4)


# Filter kustom: memeriksa apakah pengguna adalah Owner atau Admin terdaftar
def check_is_admin(_, __, message: Message):
    return message.from_user and (message.from_user.id in get_admins())


is_bot_admin = filters.create(check_is_admin)


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
        return await message.reply_text(
            "👋 Bot ini aktif untuk mengelola tombol channel."
        )

    is_owner = user_id == OWNER_ID
    role_text = "👑 **Owner Utama**" if is_owner else "🛠 **Admin Terdaftar**"

    text = (
        f"Halo **{message.from_user.first_name}**! ({role_text})\n\n"
        "**Perintah Tombol Channel:**\n"
        "• `/setbutton <ID_CH>` $\\rightarrow$ Atur tombol link biasa\n"
        "• `/setweb <ID_CH> [JUDUL | SUBTITLE | BADGE]` $\\rightarrow$ Atur WebApp warna\n"
        "• `/cekbutton <ID_CH>` $\\rightarrow$ Cek tombol aktif channel\n"
        "• `/delbutton <ID_CH>` $\\rightarrow$ Hapus tombol channel\n"
        "• `/listchannel` $\\rightarrow$ Daftar channel yang terpasang\n\n"
        "💡 *Teruskan (forward) pesan dari channel ke sini untuk cek ID Channel.*"
    )

    if is_owner:
        text += (
            "\n\n**Perintah Khusus Owner:**\n"
            "• `/addadmin <USER_ID>` $\\rightarrow$ Berikan akses setting ke orang lain\n"
            "• `/deladmin <USER_ID>` $\\rightarrow$ Cabut akses orang lain\n"
            "• `/listadmin` $\\rightarrow$ Lihat daftar semua admin"
        )

    await message.reply_text(text)


# ================= MANAJEMEN AKSES ADMIN (OWNER ONLY) =================
@app.on_message(filters.private & filters.command("addadmin") & filters.user(OWNER_ID))
async def add_admin_handler(client: Client, message: Message):
    target_id = None

    if message.reply_to_message and message.reply_to_message.forward_from:
        target_id = message.reply_to_message.forward_from.id
    else:
        parts = message.text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[1])
            except ValueError:
                return await message.reply_text("⚠️ User ID harus berupa angka.")

    if not target_id:
        return await message.reply_text(
            "⚠️ **Format:** `/addadmin <USER_ID>`\n"
            "Atau balas (reply) pesan forward dari orang tersebut dengan `/addadmin`."
        )

    admins = get_admins()
    if target_id in admins:
        return await message.reply_text(
            f"Pengguna `{target_id}` sudah memiliki akses admin."
        )

    admins.append(target_id)
    save_admins(admins)
    await message.reply_text(
        f"✅ User ID `{target_id}` berhasil diberikan akses admin bot!"
    )


@app.on_message(filters.private & filters.command("deladmin") & filters.user(OWNER_ID))
async def del_admin_handler(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("⚠️ **Format:** `/deladmin <USER_ID>`")

    try:
        target_id = int(parts[1])
    except ValueError:
        return await message.reply_text("⚠️ User ID harus berupa angka.")

    if target_id == OWNER_ID:
        return await message.reply_text("❌ Owner utama tidak bisa dihapus.")

    admins = get_admins()
    if target_id not in admins:
        return await message.reply_text(
            f"User ID `{target_id}` tidak ditemukan di daftar admin."
        )

    admins.remove(target_id)
    save_admins(admins)
    await message.reply_text(
        f"🗑️ Akses admin untuk User ID `{target_id}` berhasil dicabut."
    )


@app.on_message(filters.private & filters.command("listadmin") & filters.user(OWNER_ID))
async def list_admin_handler(client: Client, message: Message):
    admins = get_admins()
    text = "👥 **Daftar Pengguna yang Punya Akses Bot:**\n\n"
    for uid in admins:
        if uid == OWNER_ID:
            text += f"• `{uid}` 👑 *(Owner Utama)*\n"
        else:
            text += f"• `{uid}` 🛠 *(Admin Tambahan)*\n"
    await message.reply_text(text)


# ================= DETEKSI ID FORWARD =================
@app.on_message(filters.private & filters.forwarded & is_bot_admin)
async def detect_forward(client: Client, message: Message):
    if message.forward_from_chat and message.forward_from_chat.type.name == "CHANNEL":
        ch = message.forward_from_chat
        await message.reply_text(
            f"📢 **Channel Terdeteksi:**\n"
            f"• Nama: **{ch.title}**\n"
            f"• ID: `{ch.id}`"
        )
    elif message.forward_from:
        u = message.forward_from
        await message.reply_text(
            f"👤 **Pengguna Terdeteksi:**\n"
            f"• Nama: **{u.first_name}**\n"
            f"• ID: `{u.id}`\n\n"
            f"Ketik `/addadmin {u.id}` untuk memberi akses."
        )


# ================= ATUR TOMBOL BIASA (/setbutton) =================
@app.on_message(filters.private & filters.command("setbutton") & is_bot_admin)
async def set_normal_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line_parts = lines[0].split()

    if len(first_line_parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setbutton (Tombol Biasa):**\n\n"
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
        return await message.reply_text("❌ Format salah! Gunakan pemisah ` - `.")

    data = get_all_data()
    data[channel_id_str] = button_grid
    save_all_data(data)

    preview = get_channel_markup(int(channel_id_str))
    await message.reply_text(
        f"✅ **Tombol Channel Biasa Berhasil Disimpan!**\nChannel: `{channel_id_str}`\n\nPratinjau:",
        reply_markup=preview,
    )


# ================= ATUR WEBAPP DINAMIS (/setweb) =================
@app.on_message(filters.private & filters.command("setweb") & is_bot_admin)
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
            "*Catatan: Tanda kurung siku `[...]` opsional.*"
        )

    channel_id_str = parts[1]

    custom_title = "✦ PILIHAN AKSES VIP ✦"
    custom_subtitle = "Silakan pilih menu layanan di bawah ini:"
    custom_badge = "OFFICIAL PORTAL"

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
        return await message.reply_text(
            "❌ Format salah! Gunakan pemisah ` - ` pada setiap baris menu."
        )

    payload = {
        "title": custom_title,
        "subtitle": custom_subtitle,
        "badge": custom_badge,
        "items": webapp_items,
    }

    encoded_json = urllib.parse.quote(json.dumps(payload))
    final_webapp_link = f"{BASE_WEBAPP_URL}#{encoded_json}"

    button_structure = [[{"text": "✨ ʙᴜᴋᴀ ᴍᴇɴᴜ ᴠɪᴘ ✨", "url": final_webapp_link}]]

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
        reply_markup=preview,
    )


# ================= CEK TOMBOL AKTIF =================
@app.on_message(filters.private & filters.command("cekbutton") & is_bot_admin)
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
            await message.reply_text(
                f"Belum ada tombol tersimpan untuk channel `{ch_id}`."
            )
    except ValueError:
        await message.reply_text("ID Channel harus berupa angka.")


# ================= HAPUS TOMBOL =================
@app.on_message(filters.private & filters.command("delbutton") & is_bot_admin)
async def delete_buttons_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply_text("Ketik: `/delbutton <ID_CHANNEL>`")

    ch_id = args[1]
    data = get_all_data()

    if ch_id in data:
        del data[ch_id]
        save_all_data(data)
        await message.reply_text(
            f"🗑️ Konfigurasi tombol channel `{ch_id}` berhasil dihapus."
        )
    else:
        await message.reply_text(f"Channel `{ch_id}` tidak ditemukan di daftar.")


# ================= DAFTAR CHANNEL AKTIF =================
@app.on_message(filters.private & filters.command("listchannel") & is_bot_admin)
async def list_channel_handler(client: Client, message: Message):
    data = get_all_data()
    if not data:
        return await message.reply_text("Belum ada channel terdaftar.")

    text = "📋 **Daftar ID Channel yang Terpasang Tombol:**\n\n"
    for ch_id in data.keys():
        text += f"• `{ch_id}`\n"
    await message.reply_text(text)


# ================= AUTO ATTACH TOMBOL DI CHANNEL =================
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
