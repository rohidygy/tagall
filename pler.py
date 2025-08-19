import asyncio
import logging
import random

from telethon import Button, TelegramClient, events
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import (ChannelParticipantAdmin,
                               ChannelParticipantCreator)

from config import API_HASH, API_ID, TOKEN

logging.basicConfig(
    level=logging.INFO, format="%(name)s - [%(levelname)s] - %(message)s"
)
LOGGER = logging.getLogger(__name__)

api_id = API_ID
api_hash = API_HASH
bot_token = TOKEN
kntl = TelegramClient("kynan", api_id, api_hash).start(bot_token=bot_token)


spam_chats = []

emoji = "😀 😃 😄 😁 😆 😅 😂 🤣 😭 😗 😙 😚 😘 🥰 😍 🤩 🥳 🤗 🙃 🙂 ☺️ 😊 😏 😌 😉 🤭 😶 😐 😑 😔 😋 😛 😝 😜 🤪 🤔 🤨 🧐 🙄 😒 😤 😠 🤬 ☹️ 🙁 😕 😟 🥺 😳 😬 🤐 🤫 😰 😨 😧 😦 😮 😯 😲 😱 🤯 😢 😥 😓 😞 😖 😣 😩 😫 🤤 🥱 😴 😪 🌛 🌜 🌚 🌝 🎲 🧩 ♟ 🎯 🎳 🎭💕 💞 💓 💗 💖 ❤️‍🔥 💔 🤎 🤍 🖤 ❤️ 🧡 💛 💚 💙 💜 💘 💝 🐵 🦁 🐯 🐱 🐶 🐺 🐻 🐨 🐼 🐹 🐭 🐰 🦊 🦝 🐮 🐷 🐽 🐗 🦓 🦄 🐴 🐸 🐲 🦎 🐉 🦖 🦕 🐢 🐊 🐍 🐁 🐀 🐇 🐈 🐩 🐕 🦮 🐕‍🦺 🐅 🐆 🐎 🐖 🐄 🐂 🐃 🐏 🐑 🐐 🦌 🦙 🦥 🦘 🐘 🦏 🦛 🦒 🐒 🦍 🦧 🐪 🐫 🐿️ 🦨 🦡 🦔 🦦 🦇 🐓 🐔 🐣 🐤 🐥 🐦 🦉 🦅 🦜 🕊️ 🦢 🦩 🦚 🦃 🦆 🐧 🦈 🐬 🐋 🐳 🐟 🐠 🐡 🦐 🦞 🦀 🦑 🐙 🦪 🦂 🕷️ 🦋 🐞 🐝 🦟 🦗 🐜 🐌 🐚 🕸️ 🐛 🐾 🌞 🤢 🤮 🤧 🤒 🍓 🍒 🍎 🍉 🍑 🍊 🥭 🍍 🍌 🌶 🍇 🥝 🍐 🍏 🍈 🍋 🍄 🥕 🍠 🧅 🌽 🥦 🥒 🥬 🥑 🥯 🥖 🥐 🍞 🥜 🌰 🥔 🧄 🍆 🧇 🥞 🥚 🧀 🥓 🥩 🍗 🍖 🥙 🌯 🌮 🍕 🍟 🥨 🥪 🌭 🍔 🧆 🥘 🍝 🥫 🥣 🥗 🍲 🍛 🍜 🍢 🥟 🍱 🍚 🥡 🍤 🍣 🦞 🦪 🍘 🍡 🥠 🥮 🍧 🍨".split(
    " "
)

TEXT_START = """☘️ᴋᴇᴜɴᴛᴜɴɢᴀɴ ʙᴇʀʟᴀɴɢɢᴀɴᴀɴ ᴋᴏᴅᴇ ᴀᴋsᴇs ᴅɪ ᴡᴇʙsɪᴛᴇ ɢᴀʟᴇʀɪ ɴᴀᴋᴀʟ

☘️ᴛᴇʀᴜᴘᴅᴀᴛᴇ sᴇᴛɪᴀᴘ ʜᴀʀɪ ᴅᴀɴ ᴛᴇʀʙᴀʀᴜ, ʙᴜᴋᴀɴ ʙᴀʜᴀɴ ʟᴀᴍᴀ ᴀᴛᴀᴜ sᴜᴅᴀʜ ʙᴀsɪ 

☘️ᴀᴋsᴇs ᴛɪᴋᴛᴏᴋ 18+ sᴇᴘᴜᴀsᴀɴʏᴀ

☘️ᴘʀᴇᴍɪᴜᴍ ᴋᴏɴᴛᴇɴ

☘️ʙɪsᴀ ᴀᴋsᴇs sᴇᴍᴜᴀ ᴠɪᴅᴇᴏ ᴠᴠɪᴘ ʏᴀɴɢ ᴀᴅᴀ ᴅɪ ᴡᴇʙsɪᴛᴇ, ᴋᴏʟᴇᴋsɪ ᴘʀɪʙᴀᴅɪ, ᴛᴀʟᴇɴᴛ ɢɴ, ᴋᴏɴᴛᴇɴ ᴇxʟᴜsɪᴠᴇ ᴅʟʟ

☘️ᴍᴇɴᴅᴀᴘᴀᴛᴋᴀɴ ᴄʜᴀɴɴᴇʟ ᴘᴇʀᴍᴀɴᴇɴᴛ ᴀsᴜᴘᴀɴ/ᴘʀɪᴠɪᴇᴡ sᴜᴘᴀʏᴀ ᴛᴀᴜ ɪɴғᴏ ᴜᴘᴅᴀᴛᴇ ᴠɪᴅᴇᴏ ᴛᴇʀʙᴀʀᴜ ᴅɪ ᴡᴇʙsɪᴛᴇ

☘️sᴀʟᴅᴏ ʏᴀɴɢ ᴛᴀᴅɪ sᴜᴅᴀʜ ʙᴀʏᴀʀ/ʙᴇʀʟᴀɴɢɢᴀɴᴀɴ ʙɪsᴀ ᴅɪ ᴍᴀɪɴᴋᴀɴ ᴊᴀᴅɪ ᴛɪᴅᴀᴋ ʜᴀɴɢᴜs

☘️ᴛɪᴅᴀᴋ ʙɪsᴀ ᴅɪ ᴀᴋsᴇs ᴏʟᴇʜ ᴏʀᴀɴɢ ʟᴀɪɴ ᴊᴀᴅɪ ᴋᴏᴅᴇ ᴀᴋsᴇs ʙᴇʀsɪғᴀᴛ ᴘʀɪᴠᴀᴛᴇ ( ᴄᴜᴍᴀɴ ʟᴜ ᴅᴏᴀɴɢ ʏᴀɴɢ ʙɪsᴀ ᴀᴋsᴇs ᴏʀᴀɴɢ ʟᴀɪɴ ɢᴀʙɪsᴀ)

☘️ᴋᴏɴᴛᴇɴ ᴛᴇᴛᴀᴘ ᴜᴛᴜʜ ᴀᴛᴀᴜ ᴛɪᴅᴀᴋ ʜɪʟᴀɴɢ ᴅᴀɴ ᴀᴍᴀɴ, ᴛɪɴɢɢᴀʟ ᴛᴀɴʏᴀᴋᴀɴ ᴋᴇᴘᴀᴅᴀ ᴀᴅᴍɪɴ ʀᴇsᴍɪ"""


@kntl.on(events.NewMessage(pattern="^/start$"))
async def start_handler(event):
    await event.reply(
        TEXT_START,
        link_preview=False,
        buttons=[
            [Button.url("Channel", "t.me/galerinakalwebsite")],
            [Button.url("Live Chat Galeri Nakal", "t.me/telegalerinakal_bot")],
            [
                Button.url("Admin 1", "t.me/amiragalerinakal"),
                Button.url("Admin 2", "t.me/officialgalerinakal"),
            ],
            [
                Button.inline("KODE AKSES 5 HARI", b"payment24"),
                Button.inline("KODE AKSES 10 HARI", b"payment12"),
            ],
            [
                Button.inline("KODE AKSES 14 HARI", b"payment6"),
                Button.inline("VCS TALENT GALERI NAKAL", b"payment3"),
            ],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment24"))
async def payment24_callback(event):
    text = (
        "💎 **KODE AKSES 5 HARI**\n\n"
        "💵 **Harga:** `Rp 25.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/telegalerinakal_bot")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment12"))
async def payment12_callback(event):
    text = (
        "💎 **KODE AKSES 10 HARI**\n\n"
        "💵 **Harga:** `Rp 50.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/telegalerinakal_bot")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment6"))
async def payment6_callback(event):
    text = (
        "💎 **KODE AKSES 14 HARI**\n\n"
        "💵 **Harga:** `Rp 100.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/telegalerinakal_bot")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment3"))
async def payment3_callback(event):
    text = (
        "💎 **VCS TALENT GALERI NAKAL**\n\n"
        "💵 **Harga:** `Rp 100.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/telegalerinakal_bot")],
            [Button.url("ADMIN GALERY NAKAL", "t.me/amiragalerinakal")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"back_to_menu"))
async def back_to_menu(event):
    await event.edit(
        TEXT_START,
        buttons=[
            [Button.url("Channel", "t.me/galerinakalwebsite")],
            [Button.url("Live Chat Galeri Nakal", "t.me/telegalerinakal_bot")],
            [
                Button.url("Admin 1", "t.me/amiragalerinakal"),
                Button.url("Admin 2", "t.me/officialgalerinakal"),
            ],
            [
                Button.inline("KODE AKSES 5 HARI", b"payment24"),
                Button.inline("KODE AKSES 10 HARI", b"payment12"),
            ],
            [
                Button.inline("KODE AKSES 14 HARI", b"payment6"),
                Button.inline("VCS TALENT GALERI NAKAL", b"payment3"),
            ],
        ],
    )


@kntl.on(events.NewMessage(pattern="^/tagall ?(.*)"))
async def mentionall(event):
    chat_id = event.chat_id
    if event.is_private:
        return await event.respond("**Jangan private bego**")

    is_admin = False
    try:
        partici_ = await kntl(GetParticipantRequest(event.chat_id, event.sender_id))
    except UserNotParticipantError:
        is_admin = False
    else:
        if isinstance(
            partici_.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)
        ):
            is_admin = True
    if not is_admin:
        return await event.respond("**Lu bukan admin anjeng**")

    if event.pattern_match.group(1) and event.is_reply:
        return await event.respond("**Minimal kasih pesan anjeng!!**")
    elif event.pattern_match.group(1):
        mode = "teks"
        msg = event.pattern_match.group(1)
    elif event.is_reply:
        mode = "balas"
        msg = await event.get_reply_message()
        if msg is None:
            return await event.respond("**Si anjeng dibilang kasih pesan !!**")
    else:
        return await event.respond("**Si anjeng dibilang kasih pesan !!**")

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in kntl.iter_participants(chat_id):
        if not chat_id or chat_id not in spam_chats:
            break
        usrnum += 1
        usrtxt += f"🥵 [{usr.first_name}](tg://user?id={usr.id})\n"
        if usrnum == 5:
            if mode == "teks":
                txt = f"{usrtxt}\n\n{msg}"
                await kntl.send_message(chat_id, txt)
            elif mode == "balas":
                await msg.reply(usrtxt)
            await asyncio.sleep(2)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except Exception:
        pass


@kntl.on(events.NewMessage(pattern="^/cancel$"))
async def cancel_spam(event):
    if not event.chat_id or event.chat_id not in spam_chats:
        return await event.respond("**Bego orang gak ada tag all**")
    else:
        try:
            spam_chats.remove(event.chat_id)
        except Exception:
            pass
        return await event.respond("**Iya Anjeng Nih Gua Stop.**")


@kntl.on(events.NewMessage(pattern="^/all ?(.*)"))
async def mentionalls(event):
    chat_id = event.chat_id
    if event.is_private:
        return await event.respond("**Jangan private bego**")

    is_admin = False
    try:
        partici_ = await kntl(GetParticipantRequest(event.chat_id, event.sender_id))
    except UserNotParticipantError:
        is_admin = False
    else:
        if isinstance(
            partici_.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)
        ):
            is_admin = True
    if not is_admin:
        return await event.respond("**Lu bukan admin anjeng**")

    if event.pattern_match.group(1) and event.is_reply:
        return await event.respond("**Minimal kasih pesan anjeng!!**")
    elif event.pattern_match.group(1):
        mode = "teks"
        msg = event.pattern_match.group(1)
    elif event.is_reply:
        mode = "balas"
        msg = await event.get_reply_message()
        if msg is None:
            return await event.respond("**Si anjeng dibilang kasih pesan !!**")
    else:
        return await event.respond("**Si anjeng dibilang kasih pesan !!**")

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""
    async for usr in kntl.iter_participants(chat_id):
        if not chat_id or chat_id not in spam_chats:
            break
        usrnum += 1
        usrtxt += f"[{random.choice(emoji)}](tg://user?id={usr.id})"
        if usrnum == 5:
            if mode == "teks":
                txt = f"{usrtxt}\n\n{msg}"
                await kntl.send_message(chat_id, txt)
            elif mode == "balas":
                await msg.reply(usrtxt)
            await asyncio.sleep(2)
            usrnum = 0
            usrtxt = ""
    try:
        spam_chats.remove(chat_id)
    except Exception:
        pass


print("BOT AKTIF KONTOL")
kntl.run_until_disconnected()

