import asyncio
import json
import logging
import os
import re
import sys

from pyrogram_styled import Client, filters, idle
from pyrogram_styled.enums import ParseMode
from pyrogram_styled.errors import FloodWait, MessageNotModified
from pyrogram_styled.raw import functions, types
from pyrogram_styled.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                                   Message)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ================= DAFTAR CUSTOM EMOJI & WARNA =================
class AnimEmoji:
    API: int = 5420315771991497307  # 🔥
    BERLIAN: int = 5471952986970267163  # 💎
    PETIR: int = 5431449001532594346  # ⚡️
    ROKET: int = 5445284980978621387  # 🚀
    TAUTAN: int = 5375129357373165375  # 🔗
    CHAT: int = 5465300082628763143  # 💬


AUTO_PRESETS = [
    (AnimEmoji.API, "danger"),  # Merah (LIVE NYA DISINI)
    (AnimEmoji.BERLIAN, "primary"),  # Putih / Biru (VVIP NYA DISINI)
    (AnimEmoji.PETIR, "success"),  # Hijau
    (AnimEmoji.ROKET, "primary"),
]


# ================= KONFIGURASI ENV =================
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

DATA_FILE = os.path.join(BASE_DIR, "channel_buttons.json")

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
    return (
        data.get(raw)
        or data.get(f"-100{clean}")
        or data.get(f"-{clean}")
        or data.get(clean)
    )


# ================= PEMBENTUK RAW MTPROTO KEYBOARD =================
def build_raw_mtproto_markup(grid: list) -> types.ReplyInlineMarkup:
    raw_rows = []
    for r_idx, row in enumerate(grid):
        btn_cols = []
        for c_idx, item in enumerate(row):
            text = item.get("text", "").strip()
            url = item.get("url", "").strip()
            preset = AUTO_PRESETS[(r_idx + c_idx) % len(AUTO_PRESETS)]

            emoji_id = int(item.get("emoji_id") or preset[0])
            style_name = str(item.get("style") or preset[1]).lower()

            # Buat struktur style MTProto resmi Telegram
            btn_style = types.KeyboardButtonStyle(
                bg_primary=(style_name == "primary"),
                bg_danger=(style_name == "danger"),
                bg_success=(style_name == "success"),
                icon=emoji_id,
            )

            btn = types.KeyboardButtonUrl(text=text, url=url, style=btn_style)
            btn_cols.append(btn)
        raw_rows.append(types.KeyboardButtonRow(buttons=btn_cols))
    return types.ReplyInlineMarkup(rows=raw_rows)


def build_preview_markup(grid: list) -> InlineKeyboardMarkup:
    rows = []
    for r_idx, row in enumerate(grid):
        btn_row = []
        for c_idx, item in enumerate(row):
            text = item.get("text", "").strip()
            url = item.get("url", "").strip()
            btn_row.append(InlineKeyboardButton(text=text, url=url))
        rows.append(btn_row)
    return InlineKeyboardMarkup(rows)


# ================= COMMAND /SETBUTTON =================
@app.on_message(filters.private & filters.command("setbutton") & filters.user(OWNER_ID))
async def set_button_cmd(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_parts = lines[0].split()
    if len(first_parts) < 2 or len(lines) < 2:
        return await message.reply(
            "⚠️ <b>Format Penggunaan:</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "LIVE NYA DISINI - https://link1.com\n"
            "VVIP NYA DISINI - https://link2.com</code>\n\n"
            "<i>(Tombol otomatis berwarna & ber-emoji animasi resmi)</i>"
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

                # Preset otomatis: Baris 1 Merah (Api), Baris 2 Biru/Putih (Berlian)
                preset = AUTO_PRESETS[(r_idx + c_idx) % len(AUTO_PRESETS)]
                row.append(
                    {"text": txt, "url": url, "emoji_id": preset[0], "style": preset[1]}
                )
        if row:
            grid.append(row)

    if not grid:
        return await message.reply("❌ Format salah! Gunakan pemisah: <code> - </code>")

    data = get_all_data()
    data[chat_key] = grid
    save_all_data(data)

    await message.reply(
        f"✅ <b>Tombol Berhasil Disimpan &amp; Siap Diinjeksi!</b>\n"
        f"Channel: <code>{chat_key}</code>\n\nPratinjau:",
        reply_markup=build_preview_markup(grid),
    )


@app.on_message(filters.private & filters.command("cekbutton") & filters.user(OWNER_ID))
async def cek_button_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Ketik: <code>/cekbutton &lt;ID_CHANNEL&gt;</code>")

    ch_key = args[1].strip()
    grid = get_channel_grid(int(ch_key)) if ch_key.lstrip("-").isdigit() else None
    if not grid:
        return await message.reply(
            f"ℹ️ Belum ada tombol untuk channel <code>{ch_key}</code>."
        )

    await message.reply(
        f"💎 <b>Tombol aktif channel</b> <code>{ch_key}</code>:",
        reply_markup=build_preview_markup(grid),
    )


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


@app.on_message(
    filters.private & filters.command(["update", "gitpull"]) & filters.user(OWNER_ID)
)
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
        await msg.edit(
            f"⭐️ <b>Git Output:</b>\n<code>{output}</code>\n\n<i>Restarting...</i>"
        )
        await asyncio.sleep(1.5)
        restart_process()
    except Exception as e:
        await msg.edit(f"❌ Gagal update: <code>{e}</code>")


@app.on_message(filters.private & filters.command("restart") & filters.user(OWNER_ID))
async def restart_cmd(client: Client, message: Message):
    await message.reply("⚡️ <b>Memulai ulang bot...</b>")
    await asyncio.sleep(1)
    restart_process()


# ================= INJEKSI LANGSUNG MTPROTO KE CHANNEL =================
_PROCESSED_MSGS = set()


@app.on_message(filters.channel)
async def auto_channel_post_handler(client: Client, message: Message):
    if not message or getattr(message, "empty", False) or message.service:
        return

    cid = message.chat.id
    mid = message.id
    key_event = f"{cid}_{mid}"

    if key_event in _PROCESSED_MSGS:
        return
    _PROCESSED_MSGS.add(key_event)

    grid = get_channel_grid(cid)
    if not grid:
        return

    print(f"\n[EVENT] Postingan terdeteksi! Channel: {cid} | Msg ID: {mid}")
    await asyncio.sleep(0.5)

    try:
        # Panggil langsung fungsi MTProto EditMessage dengan tipe KeyboardButtonStyle
        peer = await client.resolve_peer(cid)
        raw_markup = build_raw_mtproto_markup(grid)

        await client.invoke(
            functions.messages.EditMessage(peer=peer, id=mid, reply_markup=raw_markup)
        )
        print(
            f"🔥 [SUCCESS] Tombol Berwarna & Custom Emoji BERGERAK Berhasil Diinjeksi di ID {mid}!"
        )
    except FloodWait as f:
        await asyncio.sleep(f.value)
        try:
            peer = await client.resolve_peer(cid)
            raw_markup = build_raw_mtproto_markup(grid)
            await client.invoke(
                functions.messages.EditMessage(
                    peer=peer, id=mid, reply_markup=raw_markup
                )
            )
            print(
                f"🔥 [SUCCESS] Tombol Berhasil Diinjeksi setelah FloodWait di ID {mid}!"
            )
        except Exception as retry_err:
            print(f"❌ Gagal pasang setelah FloodWait: {retry_err}")
    except MessageNotModified:
        pass
    except Exception as e:
        print(f"❌ Gagal injeksi MTProto: {e}")


# ================= MAIN RUNNER =================
async def main():
    await app.start()
    logging.info("Bot Channel Button Manager (MTProto Layer 229) Aktif.")
    await idle()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
