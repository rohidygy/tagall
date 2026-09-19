import re

@app.on_message(filters.private & filters.command("setweb") & filters.user(OWNER_ID))
async def set_webapp_buttons_handler(client: Client, message: Message):
    lines = [line.strip() for line in message.text.splitlines() if line.strip()]
    first_line = lines[0]
    
    # Ambil ID Channel
    parts = first_line.split()
    if len(parts) < 2 or len(lines) < 2:
        return await message.reply_text(
            "⚠️ **Format /setweb:**\n\n"
            "`/setweb -100xxxxxxxxxx [JUDUL | Subjudul | BADGE]\n"
            "🔥 Join VIP - https://t.me/channel\n"
            "💬 Admin 1 - https://t.me/admin1`\n\n"
            "*Catatan: Judul dalam tanda kurung siku `[...]` bersifat opsional.*"
        )

    channel_id_str = parts[1]

    # Parsing Judul Kustom jika ada tanda [...]
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
        return await message.reply_text("❌ Format salah! Gunakan pemisah ` - ` pada tiap link tombol.")

    # Susun paket data (Judul + Daftar Tombol)
    payload = {
        "title": custom_title,
        "subtitle": custom_subtitle,
        "badge": custom_badge,
        "items": webapp_items
    }

    # Encode ke parameter URL hash
    encoded_json = urllib.parse.quote(json.dumps(payload))
    final_webapp_link = f"{BASE_WEBAPP_URL}#{encoded_json}"

    # Tombol yang ditempel ke postingan channel
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
        f"• **Channel:** `{channel_id_str}`",
        reply_markup=preview
    )
