import asyncio
import json
import logging
import os
import re

import aiohttp
from pyrogram_styled import Client, filters, idle
from pyrogram_styled.enums import ParseMode
from pyrogram_styled.types import Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ================= LOAD ENV =================
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
STYLES = ("danger", "primary", "success")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Client(
    "channel_button_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)


# ================= BOT API LANGSUNG =================
async def bot_api(method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    async with aiohttp.ClientSession() as s:
        async with s.post(url, json=payload) as r:
            return await r.json()


def build_markup(grid: list) -> dict:
    """Ubah grid JSON -> reply_markup Bot API (warna + emoji premium)."""
    rows = []
    for row in grid:
        btns = []
        for item in row:
            b = {
                "text": item["text"],
                "url": item["url"],
                "style": item.get("style", "primary"),
            }
            if item.get("emoji_id"):
                b["icon_custom_emoji_id"] = str(item["emoji_id"])
            btns.append(b)
        rows.append(btns)
    return {"inline_keyboard": rows}


# ================= DATABASE =================
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


# ================= /setbutton =================
# Format tiap baris:  TEKS | URL | EMOJI_ID | STYLE
# EMOJI_ID & STYLE opsional. STYLE: danger (merah), primary (biru), success (hijau)
@app.on_message(filters.private & filters.command("setbutton") & filters.user(OWNER_ID))
async def set_button_cmd(client: Client, message: Message):
    lines = [l.strip() for l in message.text.splitlines() if l.strip()]
    first = lines[0].split()
    if len(first) < 2 or len(lines) < 2:
        return await message.reply(
            "⚠️ <b>Format:</b>\n\n"
            "<code>/setbutton -100xxxxxxxxxx\n"
            "LIVE NYA DISINI | https://link1.com | 5368324170671202286 | danger\n"
            "VVIP NYA DISINI | https://link2.com | 5368324170671202286 | primary</code>\n\n"
            "Emoji ID & style boleh dikosongkan.\n"
            "Untuk dapat Emoji ID: kirim emoji premium ke bot ini."
        )

    chat_key = first[1].strip()
    grid = []
    for r_idx, line in enumerate(lines[1:]):
        p = [x.strip() for x in line.split("|")]
        if len(p) < 2:
            continue
        text, url = p[0], p[1]
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", url):
            url = "https://" + url
        emoji_id = p[2] if len(p) > 2 and p[2].isdigit() else ""
        style = p[3] if len(p) > 3 and p[3] in STYLES else STYLES[min(r_idx, 1)]
        grid.append([{"text": text, "url": url, "style": style, "emoji_id": emoji_id}])

    if not grid:
        return await message.reply("❌ Format salah! Pisahkan dengan <code> | </code>")

    data = get_all_data()
    data[chat_key] = grid
    save_all_data(data)

    res = await bot_api(
        "sendMessage",
        {
            "chat_id": message.chat.id,
            "text": f"✅ Tombol disimpan untuk <code>{chat_key}</code>\nPratinjau:",
            "parse_mode": "HTML",
            "reply_markup": build_markup(grid),
        },
    )
    if not res.get("ok"):
        await message.reply(f"❌ Gagal pratinjau: <code>{res.get('description')}</code>")


# ================= AMBIL EMOJI ID =================
@app.on_message(filters.private & filters.user(OWNER_ID) & ~filters.command(["setbutton", "post"]))
async def get_emoji_id(client: Client, message: Message):
    ents = message.entities or message.caption_entities or []
    ids = [e.custom_emoji_id for e in ents if getattr(e, "custom_emoji_id", None)]
    if ids:
        await message.reply(
            "🆔 <b>Emoji ID:</b>\n" + "\n".join(f"<code>{i}</code>" for i in ids)
        )


# ================= /post (manual dari bot) =================
@app.on_message(filters.private & filters.command("post") & filters.user(OWNER_ID))
async def post_to_channel_cmd(client: Client, message: Message):
    args = message.text.split(None, 2)
    reply = message.reply_to_message
    if len(args) < 2 or not args[1].lstrip("-").isdigit():
        return await message.reply(
            "⚠️ Balas pesan dengan <code>/post -100xxxxxxxxxx</code> "
            "atau <code>/post -100xxxxxxxxxx teks</code>"
        )
    target = int(args[1])
    grid = get_channel_grid(target)
    if not grid:
        return await message.reply("❌ Belum ada tombol untuk channel ini.")

    markup = build_markup(grid)
    if reply:
        res = await bot_api(
            "copyMessage",
            {
                "chat_id": target,
                "from_chat_id": reply.chat.id,
                "message_id": reply.id,
                "reply_markup": markup,
            },
        )
    elif len(args) >= 3:
        res = await bot_api(
            "sendMessage",
            {"chat_id": target, "text": args[2], "reply_markup": markup},
        )
    else:
        return await message.reply("❌ Balas pesan atau sertakan teks.")

    if res.get("ok"):
        await message.reply("🔥 Terkirim dengan tombol.")
    else:
        await message.reply(f"❌ Gagal: <code>{res.get('description')}</code>")


# ================= AUTO PASANG TOMBOL SAAT POST DI CHANNEL =================
_PROCESSED = set()


@app.on_message(filters.channel)
async def auto_channel_post_handler(client: Client, message: Message):
    if not message or getattr(message, "empty", False) or message.service:
        return

    key = f"{message.chat.id}_{message.id}"
    if key in _PROCESSED:
        return
    _PROCESSED.add(key)

    grid = get_channel_grid(message.chat.id)
    if not grid:
        return

    await asyncio.sleep(0.5)
    payload = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "reply_markup": build_markup(grid),
    }
    res = await bot_api("editMessageReplyMarkup", payload)

    if not res.get("ok"):
        wait = (res.get("parameters") or {}).get("retry_after")
        if wait:
            await asyncio.sleep(wait)
            res = await bot_api("editMessageReplyMarkup", payload)
    if res.get("ok"):
        logging.info(f"✅ Tombol terpasang di ID {message.id}")
    else:
        logging.error(f"❌ Gagal pasang tombol: {res.get('description')}")


# ================= RUNNER =================
async def main():
    await app.start()
    logging.info("Bot Channel Button Manager Aktif.")
    await idle()
    await app.stop()


if __name__ == "__main__":
    app.run(main())
