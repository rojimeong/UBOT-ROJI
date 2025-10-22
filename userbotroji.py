# ===============================================================
# IMPOR LIBRARY
# ===============================================================
import os
import io
import json
import asyncio
import re
import yt_dlp
import platform # DITAMBAHKAN
from datetime import datetime
from telethon import TelegramClient, events, __version__ as telethon_version # DITAMBAHKAN
from telethon.tl.types import DocumentAttributeFilename, DocumentAttributeAudio, User, Channel
# ===============================================================
# KONFIGURASI & INISIALISASI CLIENT
# ===============================================================
# Ambil kredensial dari Replit Secrets
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
SESSION_NAME = os.environ.get("SESSION_NAME")
OSINT_BOT = "nifetisebot"

# --- DOWNLOADER & OCR ---
DOWNLOADER_BOT = "TIKTOKDOWNLOADROBOT"
OCR_BOT = "imgtotext_MBSbot"

TARGET_CHAT_IDS = [
    -1002731630127,  #
    -1003029142793,   #
]

AUTHORIZED_USERS_DEL = [
    1860051928, # USER ID Tele
]

# DAFTAR KATA TOXIC
TOXIC_WORDS = {
    "goblok", "goblog","goblik", "goblig", "tolol", "tulil", "gendeng", "gendheng", "asu", "ASSSSSSSSSSHHHHHHU", "asshole", "asw", "ashu", "asshhuu", "lahnjing", "jing", "su", "anj", "anjg", "anjing", "ancok", "cok", "c0k", "kontol", "kntl", "kintil", "k1nt1l", "k0nt0l", "knt0l", "dancok", "lahcok", "bangsat", "bangsad", "wanjing", "wanjg", "wanj", "wancok", "gatel", "gathel", "ghatel", "dancik", "kont", "kontl", "k0ntl", "kntol", "mmk", "bgst", "bgsd", "kimak", "jnck", "memek", "dongo", "ngntod", "ngentod", "ngentot", "ngentd", "ngtd", "njing", "puki", "babi", "gwendeng", "kerek", "bajingan", "badjingan", "jingan", "djingan", "janc", "janco", "jancu", "jncik", "jnc0k", "jnc1k", "j4ncok", "j4ncuk", "j4nc1k", "j4nc0k", "j4ncik", "anjink", "anj1nk", "anj1ng", "anjingk", "anj1ngk", "celeng", "ashu",
    "iclik", "congok", "ngwe", "ngewe", "fak", "fuck", "bangst", "bangsd", "edan", "bitch", "jancok", "janc0k", "jancuk", "on ol", "picek", "jangkrik", "jangkrick", "juangkrik", "juangkrick", "jngkrek", "jangkrek", "hangkrik", "damput", "jamput", "edyan", "edyian", "edian", "jampoet", "juamput", "juampoet", "taek", "jurig", "belis", "bokep", "bkp", "bokp", "jaran", "hangkrek", "anjeng", "anjengm", "anjengs", "wanjeng", "jembut", "jembot", "jembhut", "jembud", "jembod", "jancik"
}

LOG_FILE = "chat_log.txt"

# Membuat objek 'client'
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
start_time = datetime.now() # DITAMBAHKAN: Mencatat waktu start bot

# ===============================================================
# BAGIAN 3: FUNGSI BANTUAN & SEMUA FUNGSI BOT
# ===============================================================

# --- Fungsi Pencatatan Log ---
def log_to_file(log_message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {log_message}\n")

# --- FUNGSI BARU: Pencatatan Log ke Konsol ---
async def log_to_console(event, feature, status, details=""):
    """Fungsi untuk mencatat log aksi ke konsol secara live dengan format baru."""
    try:
        # Baris 1: Info Pengguna
        sender = await event.get_sender()
        user_info = f"👤 @{sender.username or sender.first_name} ({sender.id})"
        print(user_info)

        # Baris 2: Detail Aksi
        if feature == "Toxic Word":
            details_line = f"   ╰─ Toxic: {details} | Status: ({status})"
        else:
            details_line = f"   ╰─ Feature: {feature} | Status: ({status})"
        print(details_line)
        print()  # Tambahkan baris kosong sebagai pemisah

    except Exception:
        # Fallback jika gagal mendapatkan info user (mis. di channel anonim)
        print(f"Aksi '{feature}' terjadi | Status: {status}\n")

# --- FUNGSI BANTUAN UNTUK UPTIME ---
def format_uptime(start_time):
    """Fungsi untuk memformat durasi uptime bot."""
    uptime_delta = datetime.now() - start_time
    total_seconds = int(uptime_delta.total_seconds())
    if total_seconds < 1:
        return "Baru saja dimulai"

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0: parts.append(f"{days} hari")
    if hours > 0: parts.append(f"{hours} jam")
    if minutes > 0: parts.append(f"{minutes} menit")
    if seconds > 0: parts.append(f"{seconds} detik")

    return ", ".join(parts)


# --- Fitur /s.tik (Universal Downloader) ---
@client.on(events.NewMessage(pattern=r"^[./]s\.tik (.+)"))
async def handler_stik(event):
    link = event.pattern_match.group(1)
    status_message = await event.reply("`mendownload media...`", silent=True)
    try:
        is_first_reply = True
        async with client.conversation(DOWNLOADER_BOT, timeout=300) as conv:
            await conv.send_message(link)
            while True:
                try:
                    response = await conv.get_response(timeout=20)
                    reply_to_id = event.id if is_first_reply else None
                    is_first_reply = False
                    await client.send_file(event.chat_id, file=response.media, caption=response.text, reply_to=reply_to_id, silent=True)
                except asyncio.TimeoutError:
                    break
        await status_message.delete()
        await log_to_console(event, "Downloader", "Success")
    except Exception as e:
        await status_message.edit(f"**❌ Terjadi Kesalahan:**\n`{str(e)}`")
        await log_to_console(event, "Downloader", "Failed")

# --- Fitur /itt (Image to Text / OCR) ---
@client.on(events.NewMessage(pattern=r"^[./]itt$"))
async def handler_itt(event):
    if not (event.is_private or event.chat_id in TARGET_CHAT_IDS):
        return
    reply_message = await event.get_reply_message()
    if not (reply_message and reply_message.photo):
        await event.reply("`Balas sebuah gambar dengan perintah /itt`", silent=True)
        return
    status_message = await event.reply("`🔎 Memproses gambar...`", silent=True)
    try:
        async with client.conversation(OCR_BOT, timeout=120) as conv:
            await conv.send_file(reply_message.photo)
            all_responses = []
            while True:
                try:
                    response = await conv.get_response(timeout=12)
                    all_responses.append(response)
                except asyncio.TimeoutError:
                    break
            final_text = None
            if all_responses:
                text_responses = [res.text for res in all_responses if res.text]
                if text_responses:
                    final_text = max(text_responses, key=len)
            if final_text:
                await client.send_message(
                    event.chat_id,
                    f"**✍️ Image to teks:**\n\n{final_text}",
                    reply_to=event.id,
                    silent=True
                )
                await status_message.delete()
                await log_to_console(event, "/itt", "Success")
            else:
                await status_message.edit("`❌ Gagal mendapatkan balasan teks dari bot OCR.`")
                await log_to_console(event, "OCR", "Failed", "No text from OCR bot")
    except Exception as e:
        await status_message.edit(f"**❌ Terjadi Kesalahan:**\n`{str(e)}`")
        await log_to_console(event, "OCR", "Failed")


# --- Fitur /del (Hapus Pesan untuk User Terpilih) ---
@client.on(events.NewMessage(pattern=r"^[./]del$"))
async def handler_del_message(event):
    if not event.is_group:
        await event.reply("`❌ Perintah ini hanya bisa digunakan di grup.`", silent=True)
        return
    if event.sender_id not in AUTHORIZED_USERS_DEL:
        await event.reply("`❌ Tidak memiliki izin...`", silent=True)
        return
    reply_message = await event.get_reply_message()
    if not reply_message:
        await event.reply("`reply pesam dengan perintah /del.`", silent=True)
        return
    countdown = 1
    delete_status_message = await event.reply(
        f"**🗑️ Delete messages...**\n"
        f"pesan akan dihapus dalam `[{countdown}]`...",
        silent=True
    )
    try:
        for i in range(countdown - 1, 0, -1):
            await asyncio.sleep(1)
            await delete_status_message.edit(
                f"**🗑️ Delete messages...**\n"
                f"pesan akan dihapus dalam `[{i}]`..."
            )
        await asyncio.sleep(1)
        await reply_message.delete()
        await event.delete()
        await delete_status_message.edit("`✅ message deleted successfully`")
        await asyncio.sleep(1)
        await delete_status_message.delete()
        await log_to_console(event, "Delete message", "Success")
    except Exception as e:
        await delete_status_message.edit(f"**❌ Failed to delete message!**\nPastikan userbot memiliki izin admin untuk menghapus pesan.\n\n`Error: {e}`")
        await log_to_console(event, "Delete message", "Failed")


# --- Fitur /menu ---
@client.on(events.NewMessage(pattern=r"^[./]menu$"))
async def handler_menu(event):
    menu_text = (
        "**Rozybot Utility Menu**\n\n"
        "Halo! aku userbot (gratisan bjir):\n"
        "**Menu:**\n"
        "`- /alltag` : Mention manusia\n"
        "`- /cekdata [query]` : Cek data bocor\n"
        "`- /play [judul/link]` : Download yt untuk musik\n"
        "`- /s.tik [link]` : Download media (yt,tt,ig,pin)\n"
        "`- /itt` : Konversi gambar ke teks (reply gambar)\n"
        "**Notepad Pribadi:**\n"
        "`- /addnote [judul]` : Simpan catatan (reply pesan)\n"
        "`- /notes` : Lihat semua catatanmu\n"
        "`- /note [judul]` : Ambil isi catatan\n"
        "`- /delnote [judul]` : Hapus catatan\n\n"
    )
    await event.reply(menu_text, silent=True)
    await log_to_console(event, "Menu", "Success")

# --- Fitur Debugging: /ping --- (FUNGSI INI DIGANTI TOTAL)
@client.on(events.NewMessage(pattern=r"^[./]ping$"))
async def handler_ping(event):
    """Menampilkan dashboard status bot."""
    # 1. Mengukur latensi
    ping_start = datetime.now()
    ping_message = await event.reply("`Pinging...`", silent=True)
    ping_end = datetime.now()
    latency_ms = round((ping_end - ping_start).total_seconds() * 1000, 2)

    # 2. Mengumpulkan informasi lain
    user_id = event.sender_id
    dc_id = client.session.dc_id
    uptime = format_uptime(start_time)
    python_ver = platform.python_version()

    # 3. Membuat teks dashboard
    dashboard_text = (
        "**📡 Pinging...**\n\n"
        f"**⚡ Latency:** `{latency_ms} ms`\n"
        f"**🛰️ Data Center:** `DC {dc_id}`\n"
        f"**⏳ Uptime:** `{uptime}`\n"
        f"**👤 User ID:** `{user_id}`\n\n"
        "--- **Server Info** ---\n"
        f"**🐍 Python:** `{python_ver}`\n"
        f"**📦 Telethon:** `{telethon_version}`"
    )

    # 4. Mengedit pesan dan mencatat log
    await ping_message.edit(dashboard_text)
    await log_to_console(event, "Ping", "Success")

# --- Fitur Deteksi Pesan Toxic (DENGAN LOGGING) ---
@client.on(events.NewMessage())
async def handler_toxic_message(event):
    if event.chat_id not in TARGET_CHAT_IDS or not event.text:
        return

    message_text = event.text.lower()
    detected_word = None
    for toxic_word in TOXIC_WORDS:
        pattern = r'\b' + re.escape(toxic_word) + r'+\b'
        if re.search(pattern, message_text):
            detected_word = toxic_word
            break

    if detected_word:
        try:
            sender = await event.get_sender()
            chat = await event.get_chat()
            chat_title = chat.title if isinstance(chat, (Channel)) else "Private Chat"
            log_message = (
                f"[TOXIC DETECTED] User: {sender.first_name} (@{sender.username or 'NoUsername'}) | "
                f"Chat: {chat_title} | "
                f"Message: \"{event.text}\""
            )
            log_to_file(log_message)
            countdown = 3
            reply_message = await event.reply(
                f"**⚠️ TOXICITY DETECTED! ⚠️**\n"
                f"Pesan akan dihapus dalam `[{countdown}]`...",
                silent=True
            )
            for i in range(countdown - 1, 0, -1):
                await asyncio.sleep(1)
                await reply_message.edit(
                    f"**⚠️ TOXICITY DETECTED! ⚠️**\n"
                    f"Pesan akan dihapus dalam `[{i}]`..."
                )
            await asyncio.sleep(1)
            await event.delete()
            await reply_message.edit("**✅ TOXIC MESSAGE DELETED ✅**")
            await log_to_console(event, "Toxic Word", "Deleted", details=detected_word)
        except Exception as e:
            await event.reply(f"**❌ Gagal menghapus pesan!**\nPastikan aku adalah admin di grup ini.\n\n`Error: {e}`", silent=True)
            await log_to_console(event, "Toxic Word", "Failed to Delete", details=detected_word)


# --- Fitur Notepad (PRIBADI UNTUK SETIAP PENGGUNA) ---
NOTES_FILE = "notes.json"
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}
def save_notes(data):
    with open(NOTES_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)

@client.on(events.NewMessage(pattern=r"^[./]addnote (.+)"))
async def add_note_handler(event):
    user_id = str(event.sender_id)
    title = event.pattern_match.group(1).strip()
    reply = await event.get_reply_message()
    if reply and reply.text:
        notes = load_notes()
        if user_id not in notes: notes[user_id] = {}
        notes[user_id][title] = reply.text
        save_notes(notes)
        await event.reply(f"**✅ Catatan disimpan:** `/note {title}`", silent=True)
        await log_to_console(event, "addnote", "Success")
    else:
        await event.reply("**❌ Gagal!** Reply sebuah pesan teks.", silent=True)
        await log_to_console(event, "addnote", "Failed")

@client.on(events.NewMessage(pattern=r"^[./]notes$"))
async def list_notes_handler(event):
    user_id = str(event.sender_id)
    notes = load_notes()
    if user_id not in notes or not notes[user_id]:
        await event.reply("**ℹ️ Kamu belum punya catatan.**", silent=True)
        await log_to_console(event, "notes", "Empty")
        return
    msg = "**🗒️ Daftar Catatanmu:**\n\n"
    for title in notes[user_id]: msg += f"- `{title}`\n"
    await event.reply(msg, silent=True)
    await log_to_console(event, "notes", "Success")

@client.on(events.NewMessage(pattern=r"^[./]note (.+)"))
async def get_note_handler(event):
    user_id = str(event.sender_id)
    title = event.pattern_match.group(1).strip()
    notes = load_notes()
    if user_id in notes and title in notes[user_id]:
        await event.reply(f"**📝 Catatan: `{title}`**\n\n{notes[user_id][title]}", silent=True)
        await log_to_console(event, "/note", "Success")
    else:
        await event.reply(f"**❌ Catatan `{title}` tidak ditemukan!**", silent=True)
        await log_to_console(event, "/note", "Failed")

@client.on(events.NewMessage(pattern=r"^[./]delnote (.+)"))
async def delete_note_handler(event):
    user_id = str(event.sender_id)
    title = event.pattern_match.group(1).strip()
    notes = load_notes()
    if user_id in notes and title in notes[user_id]:
        del notes[user_id][title]
        save_notes(notes)
        await event.reply(f"**🗑️ Catatan `{title}` berhasil dihapus!**", silent=True)
        await log_to_console(event, "Delnote", "Success")
    else:
        await event.reply(f"**❌ Catatan `{title}` tidak ditemukan!**", silent=True)
        await log_to_console(event, "Delnote", "Failed")

# --- Fitur Play Music (LOGIKA DIPERBAIKI) ---
@client.on(events.NewMessage(pattern=r"^[./]play (.+)"))
async def handler_play(event):
    query = event.pattern_match.group(1)
    status_message = await event.reply("`[ 1/4 ]` **🔎 Mencari lagu...**")
    final_filename = None
    try:
        ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'outtmpl': 'downloaded_song.%(ext)s', 'default_search': 'ytsearch', 'noplaylist': True}
        await status_message.edit("`[ 2/4 ]` **📥 Mendownload audio...**")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, query, download=False)
            ydl.download([query])
            final_filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
        if not os.path.exists(final_filename): raise FileNotFoundError("File tidak ditemukan.")
        file_size_mb = os.path.getsize(final_filename) / (1024 * 1024)
        if file_size_mb > 48:
            await status_message.edit(f"**❌ Gagal:** Ukuran file (`{file_size_mb:.2f} MB`) terlalu besar."); return
        await status_message.edit(f"`[ 3/4 ]` **📤 Mengunggah...** (`{file_size_mb:.2f} MB`)")
        title, duration, performer = info.get('title', 'Unknown'), int(info.get('duration', 0)), info.get('uploader', 'Unknown')
        await client.send_file(
            event.chat_id,
            file=final_filename,
            reply_to=event.id,
            caption=f"**🎵 Judul:** `{title}`",
            attributes=[DocumentAttributeAudio(duration=duration, title=title, performer=performer)],
            silent=True
        )
        sender = await event.get_sender()
        chat = await event.get_chat()
        chat_title = chat.title if hasattr(chat, 'title') else "Private Chat"
        log_message = (
            f"[PLAY MUSIC] User: {sender.first_name} (@{sender.username or 'NoUsername'}) | "
            f"Chat: {chat_title} | "
            f"Song: \"{title}\""
        )
        log_to_file(log_message)
        await status_message.edit("`[ 4/4 ]` **✅ Berhasil terkirim!**")
        await asyncio.sleep(4)
        await status_message.delete()
        await log_to_console(event, "play music", "Success")
    except Exception as e:
        await status_message.edit(f"**❌ Terjadi Kesalahan:**\n`{str(e)}`")
        await log_to_console(event, "play music", "Failed")
    finally:
        if final_filename and os.path.exists(final_filename): os.remove(final_filename)

# --- Fitur Cek Data & All Tag ---
@client.on(events.NewMessage(pattern=r"^[./]cekdata (.+)"))
async def handler_cekdata(event):
    query = event.pattern_match.group(1); chat = await event.get_chat()
    loading_message = await event.reply("🔎 Sedang mencari data...", silent=True); is_first = True
    try:
        async with client.conversation(OSINT_BOT, timeout=60) as conv:
            await conv.send_message(query)
            await loading_message.delete()
            while True:
                try:
                    res = await conv.get_response(timeout=3)
                    if is_first:
                        await client.send_message(chat.id, f"📡 Hasil searching dari: **{query}**\n\n{res.text}", reply_to=event.id, silent=True); is_first = False
                    else: await client.send_message(chat.id, res.text, silent=True)
                except asyncio.TimeoutError: break
    except asyncio.TimeoutError:
        await event.reply("❌ Gagal mendapat respons dari bot OSINT.", silent=True)

    if is_first:
        await event.reply("🤔 Bot OSINT tidak memberikan balasan.", silent=True)
        await log_to_console(event, "Cekdata", "Failed", "No response from bot")
    else:
        await log_to_console(event, "Cekdata", "Success")


@client.on(events.NewMessage(pattern=r"^[./]alltag$"))
async def handler_alltag(event):
    if event.is_group:
        status_message = await event.reply("`Mengumpulkan pengguna...`", silent=True)
        mentions = []
        async for user in client.iter_participants(event.chat_id):
            if not user.bot:
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        text = "👥 **mention** \n\n" + " ".join(mentions)
        await status_message.delete()
        reply_message = await event.get_reply_message()
        if reply_message:
            await reply_message.reply(text, link_preview=False)
        else:
            await event.reply(text, link_preview=False)
        await log_to_console(event, "mention", "Success")

# ===============================================================
# BAGIAN 4: MENJALANKAN BOT
# ===============================================================
def display_dashboard():
    """Menampilkan dashboard keren di konsol saat bot dimulai."""
    print("=" * 60)
    print("🚀 ROZYBOT UTILITY BERJALAN 🚀".center(60))
    print("=" * 60)
    print(f"👤 Nama Sesi: {SESSION_NAME}")
    print("\n--- 🛡️ Konfigurasi Moderasi ---")
    print(f"   monitored grup: {len(TARGET_CHAT_IDS)} grup")
    print(f"  Total Kata Toxic: {len(TOXIC_WORDS)} kata")
    print(f"  User Otorisasi /del: {len(AUTHORIZED_USERS_DEL)} pengguna")

    print("\n--- 🛠️ Fitur & Modul Aktif ---")
    print("  • Perintah: play music, downloader, OCR, cekdata, mention")
    print("  • Modul: Notepad Pribadi (/addnote, /notes, dll)")
    print("  • Pasif: Filter Anti-Toxic aktif di grup target")

    print("\n--- 🤖 Bot Eksternal yang Digunakan ---")
    print(f"  • Downloader: @{DOWNLOADER_BOT}")
    print(f"  • OCR (Image-to-Text): @{OCR_BOT}")
    print(f"  • OSINT (Cek Data): @{OSINT_BOT}")
    print("=" * 60)
    print("\n  Bot magang siap di perintah...\n" + "-"*60)

# Menjalankan dashboard dan bot
display_dashboard()
client.start()
client.run_until_disconnected()