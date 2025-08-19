from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_HASH, API_ID, TOKEN

app = Client("LuciferVIP", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

TEXT_START = """<blockquote expandable>
☘️ᴋᴇᴜɴᴛᴜɴɢᴀɴ ʙᴇʀʟᴀɴɢɢᴀɴᴀɴ ᴋᴏᴅᴇ ᴀᴋsᴇs ᴅɪ ᴡᴇʙsɪᴛᴇ ɢᴀʟᴇʀɪ ɴᴀᴋᴀʟ

☘️ᴛᴇʀᴜᴘᴅᴀᴛᴇ sᴇᴛɪᴀᴘ ʜᴀʀɪ ᴅᴀɴ ᴛᴇʀʙᴀʀᴜ, ʙᴜᴋᴀɴ ʙᴀʜᴀɴ ʟᴀᴍᴀ ᴀᴛᴀᴜ sᴜᴅᴀʜ ʙᴀsɪ 

☘️ᴀᴋsᴇs ᴛɪᴋᴛᴏᴋ 18+ sᴇᴘᴜᴀsᴀɴʏᴀ

☘️ᴘʀᴇᴍɪᴜᴍ ᴋᴏɴᴛᴇɴ

☘️ʙɪsᴀ ᴀᴋsᴇs sᴇᴍᴜᴀ ᴠɪᴅᴇᴏ ᴠᴠɪᴘ ʏᴀɴɢ ᴀᴅᴀ ᴅɪ ᴡᴇʙsɪᴛᴇ, ᴋᴏʟᴇᴋsɪ ᴘʀɪʙᴀᴅɪ, ᴛᴀʟᴇɴᴛ ɢɴ, ᴋᴏɴᴛᴇɴ ᴇxʟᴜsɪᴠᴇ ᴅʟʟ

☘️ᴍᴇɴᴅᴀᴘᴀᴛᴋᴀɴ ᴄʜᴀɴɴᴇʟ ᴘᴇʀᴍᴀɴᴇɴᴛ ᴀsᴜᴘᴀɴ/ᴘʀɪᴠɪᴇᴡ sᴜᴘᴀʏᴀ ᴛᴀᴜ ɪɴғᴏ ᴜᴘᴅᴀᴛᴇ ᴠɪᴅᴇᴏ ᴛᴇʀʙᴀʀᴜ ᴅɪ ᴡᴇʙsɪᴛᴇ

☘️sᴀʟᴅᴏ ʏᴀɴɢ ᴛᴀᴅɪ sᴜᴅᴀʜ ʙᴀʏᴀʀ/ʙᴇʀʟᴀɴɢɢᴀɴᴀɴ ʙɪsᴀ ᴅɪ ᴍᴀɪɴᴋᴀɴ ᴊᴀᴅɪ ᴛɪᴅᴀᴋ ʜᴀɴɢᴜs

☘️ᴛɪᴅᴀᴋ ʙɪsᴀ ᴅɪ ᴀᴋsᴇs ᴏʟᴇʜ ᴏʀᴀɴɢ ʟᴀɪɴ ᴊᴀᴅɪ ᴋᴏᴅᴇ ᴀᴋsᴇs ʙᴇʀsɪғᴀᴛ ᴘʀɪᴠᴀᴛᴇ 

☘️ᴋᴏɴᴛᴇɴ ᴛᴇᴛᴀᴘ ᴜᴛᴜʜ ᴀᴛᴀᴜ ᴛɪᴅᴀᴋ ʜɪʟᴀɴɢ ᴅᴀɴ ᴀᴍᴀɴ, ᴛɪɴɢɢᴀʟ ᴛᴀɴʏᴀᴋᴀɴ ᴋᴇᴘᴀᴅᴀ ᴀᴅᴍɪɴ ʀᴇsᴍɪ
</blockquote>"""

IMG_URL= "https://files.catbox.moe/tdeh91.jpg"

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    return await message.reply_photo(
        IMG_URL,
        TEXT_START,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Channel", url="t.me/galerinakalwebsite")],
                [
                    InlineKeyboardButton(
                        "Live Chat Galeri Nakal", url="t.me/telegalerinakal_bot"
                    )
                ],
                [
                    InlineKeyboardButton("Admin 1", url="t.me/amiragalerinakal"),
                    InlineKeyboardButton("Admin 2", url="t.me/officialgalerinakal"),
                ],
                [
                    InlineKeyboardButton(
                        "KODE AKSES 5 HARI", callback_data="payment24"
                    ),
                    InlineKeyboardButton(
                        "KODE AKSES 10 HARI", callback_data="payment12"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "KODE AKSES 14 HARI", callback_data="payment6"
                    ),
                    InlineKeyboardButton(
                        "VCS TALENT GALERI NAKAL", callback_data="payment3"
                    ),
                ],
            ]
        ),
    )


@app.on_callback_query(filters.regex("payment24"))
async def payment24_callback(client, callback_query):
    text = (
        "💎 **KODE AKSES 5 HARI**\n\n"
        "💵 **Harga:** `Rp 25.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )
    return await callback_query.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Konfirmasi Pembayaran", url="t.me/telegalerinakal_bot"
                    )
                ],
                [InlineKeyboardButton("Kembali", callback_data="back_to_menu")],
            ]
        ),
    )


@app.on_callback_query(filters.regex("payment12"))
async def payment12_callback(client, callback_query):
    text = (
        "💎 **KODE AKSES 10 HARI**\n\n"
        "💵 **Harga:** `Rp 50.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )
    return await callback_query.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Konfirmasi Pembayaran", url="t.me/telegalerinakal_bot"
                    )
                ],
                [InlineKeyboardButton("Kembali", callback_data="back_to_menu")],
            ]
        ),
    )


@app.on_callback_query(filters.regex("payment6"))
async def payment6_callback(client, callback_query):
    text = (
        "💎 **KODE AKSES 14 HARI**\n\n"
        "💵 **Harga:** `Rp 100.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )
    return await callback_query.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Konfirmasi Pembayaran", url="t.me/telegalerinakal_bot"
                    )
                ],
                [InlineKeyboardButton("Kembali", callback_data="back_to_menu")],
            ]
        ),
    )


@app.on_callback_query(filters.regex("payment3"))
async def payment3_callback(client, callback_query):
    text = (
        "💎 **VCS TALENT GALERI NAKAL**\n\n"
        "💵 **Harga:** `Rp 100.000`\n\n"
        "💳 **Silahkan lakukan pembayaran melalui akses berikut:**\n\n"
        "🏧 **BCA:** `8520330721` A/n M STEAPHEN\n"
        "🏧 **BRI:** `011201106024509` A/n NICHOLAS\n"
        "🏧 **BNI:** `188-652-0309` A/n YOSE RIZAL\n\n"
        "KLIK ADMIN GALERY NAKAL UNTUK TANYA TALENT VCS READY\n"
    )
    return await callback_query.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Konfirmasi Pembayaran", url="t.me/telegalerinakal_bot"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "ADMIN GALERY NAKAL", url="t.me/amiragalerinakal"
                    )
                ],
                [InlineKeyboardButton("Kembali", callback_data="back_to_menu")],
            ]
        ),
    )


@app.on_callback_query(filters.regex("back_to_menu"))
async def back_to_menu(client, callback_query):
    return await callback_query.message.edit(
        TEXT_START,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Channel", url="t.me/galerinakalwebsite")],
                [
                    InlineKeyboardButton(
                        "Live Chat Galeri Nakal", url="t.me/telegalerinakal_bot"
                    )
                ],
                [
                    InlineKeyboardButton("Admin 1", url="t.me/amiragalerinakal"),
                    InlineKeyboardButton("Admin 2", url="t.me/officialgalerinakal"),
                ],
                [
                    InlineKeyboardButton(
                        "KODE AKSES 5 HARI", callback_data="payment24"
                    ),
                    InlineKeyboardButton(
                        "KODE AKSES 10 HARI", callback_data="payment12"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "KODE AKSES 14 HARI", callback_data="payment6"
                    ),
                    InlineKeyboardButton(
                        "VCS TALENT GALERI NAKAL", callback_data="payment3"
                    ),
                ],
            ]
        ),
    )


print("BOT AKTIF KONTOL")
app.run()
