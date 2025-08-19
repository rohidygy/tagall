from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import API_HASH, API_ID, TOKEN

app = Client("LuciferVIP", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

TEXT_START = """<blockquote expandable>
 Hai {} 👋 Selamat datang di bot {}🎉

Bot ini dibuat khusus untuk memudahkan kamu bergabung ke website kami yang berisi:

📱 Ribuan koleksi video rare exclusive berkualitas
🔥 Update video terbaru setiap hari
⚡️ Akses cepat dan mudah
💥 Nonton Puas Tanpa Iklan

Silakan gunakan tombol di bawah untuk mengakses website kami! 🚀
</blockquote>"""

IMG_URL = "https://files.catbox.moe/tdeh91.jpg"


@app.on_message(filters.command("start"))
async def start_handler(client, message):
    return await message.reply_photo(
        IMG_URL,
        caption=TEXT_START.format(message.from_user.mention, client.me.mention),
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
        TEXT_START.format(message.from_user.mention, client.me.mention),
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
