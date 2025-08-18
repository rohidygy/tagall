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


@kntl.on(events.NewMessage(pattern="^/start$"))
async def start_handler(event):
    helptext = "**Ada 2 Mode Tag All Cok, Kalo /tagall emot sange + nama user. kalo /all itu random emote tanpa nama user.**"
    await event.reply(
        helptext,
        link_preview=False,
        buttons=[
            [Button.url("Owner", "t.me/kagebunshiiin")],
            [
                Button.url("Support", "t.me/suportkage"),
                Button.url("Channel", "t.me/kagestore69"),
            ],
            [
                Button.inline("VIP 24 JAM", b"payment24"),
                Button.inline("VIP 12 JAM", b"payment12"),
            ],
            [
                Button.inline("VIP 6 JAM", b"payment6"),
                Button.inline("VIP 3 JAM", b"payment3"),
            ],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment24"))
async def payment24_callback(event):
    text = (
        "💎 **VIP 24 JAM:**\n\n"
        "💵 **Harga:** `Rp. 100.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🪙 **Dana:** `081234567890`\n"
        "🏧 **BCA:** `999000028`\n"
        "👤 Atas Nama: **Dana**"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/kagebunshiiin")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment12"))
async def payment12_callback(event):
    text = (
        "💎 **VIP 12 JAM:**\n\n"
        "💵 **Harga:** `Rp. 80.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🪙 **Dana:** `081234567890`\n"
        "🏧 **BCA:** `999000028`\n"
        "👤 Atas Nama: **Dana**"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/kagebunshiiin")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment6"))
async def payment6_callback(event):
    text = (
        "💎 **VIP 6 JAM:**\n\n"
        "💵 **Harga:** `Rp. 50.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🪙 **Dana:** `081234567890`\n"
        "🏧 **BCA:** `999000028`\n"
        "👤 Atas Nama: **Dana**"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/kagebunshiiin")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"payment3"))
async def payment3_callback(event):
    text = (
        "💎 **VIP 12 JAM:**\n\n"
        "💵 **Harga:** `Rp. 35.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🪙 **Dana:** `081234567890`\n"
        "🏧 **BCA:** `999000028`\n"
        "👤 Atas Nama: **Dana**"
    )

    await event.edit(
        text,
        buttons=[
            [Button.url("Konfirmasi Pembayaran", "t.me/kagebunshiiin")],
            [Button.inline("Kembali", b"back_to_menu")],
        ],
    )


@kntl.on(events.CallbackQuery(data=b"back_to_menu"))
async def back_to_menu(event):
    helptext = "**Ada 2 Mode Tag All Cok, Kalo /tagall emot sange + nama user. kalo /all itu random emote tanpa nama user.**"
    await event.edit(
        helptext,
        buttons=[
            [Button.url("Owner", "t.me/kagebunshiiin")],
            [
                Button.url("Support", "t.me/suportkage"),
                Button.url("Channel", "t.me/kagestore69"),
            ],
            [
                Button.inline("VIP 24 JAM", b"payment24"),
                Button.inline("VIP 12 JAM", b"payment12"),
            ],
            [
                Button.inline("VIP 6 JAM", b"payment6"),
                Button.inline("VIP 3 JAM", b"payment3"),
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
