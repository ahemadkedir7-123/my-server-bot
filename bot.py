
import io
import os
import re
import socket
import logging
import threading
from urllib.parse import quote

import requests
import telebot
from telebot import types
from flask import Flask
from PIL import Image, ImageDraw, ImageFont, ImageOps

TOKEN = "8788982436:AAFTXTcXdwxUkR36DmzV8hGSiOMm-Ok28AM"
bot = telebot.TeleBot(TOKEN)
    
ADMIN_LINK = os.getenv("ADMIN_LINK", "https://t.me/Shemsadin_vip")
REQUIRED_CHANNELS = [
    "@Nur_Tunnel_free_ethiopian",
    "@freeinternat10",
]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("netx")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
session = requests.Session()
session.headers.update({"User-Agent": "NetX-Tools-Pro/1.0"})
app = Flask(__name__)

def normalize_domain(raw):
    if not raw:
        return None
    value = raw.strip().lower()
    value = re.sub(r"^https?://", "", value)
    value = value.split("/")[0].split("?")[0].split("#")[0]
    value = value.split(":")[0].rstrip(".")
    if len(value) > 253 or "." not in value:
        return None
    labels = value.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return None
        if not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label
        ):
            return None
    if not re.fullmatch(r"[a-z]{2,63}", labels[-1]):
        return None
    return value

def esc(value):
    value = str(value if value is not None else "N/A")
    return (value.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))

def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ("creator", "administrator", "member"):
                return False
        except Exception:
            log.exception("Membership check failed: %s", channel)
            return False
    return True

def keyboard():
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, row_width=2
    )
    markup.add(
        types.KeyboardButton("🌐 Subdomain Finder"),
        types.KeyboardButton("📡 Web Host Scanner"),
        types.KeyboardButton("📁 Bulk Domain Checker (.txt)"),
        types.KeyboardButton("🔍 DNS Lookup"),
        types.KeyboardButton("🔍 Domain & IP Recon"),
        types.KeyboardButton("🖼️ Image Info & Editor"),
        types.KeyboardButton("📢 PROMOTION MARKET"),
        types.KeyboardButton("🆘 Help / How to Use"),
    )
    return markup

def require_membership(message):
    if check_subscription(message.from_user.id):
        return True
    markup = types.InlineKeyboardMarkup()
    for channel in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(
            f"Join {channel}",
            url=f"https://t.me/{channel.lstrip('@')}"
        ))
    markup.add(types.InlineKeyboardButton(
        "✅ Check membership", callback_data="check_sub"
    ))
    bot.send_message(
        message.chat.id,
        "⚠️ ቦቱን ለመጠቀም ሁለቱንም ቻናሎች ይቀላቀሉ።",
        reply_markup=markup
    )
    return False

def ask_domain(message, prompt, callback):
    msg = bot.send_message(message.chat.id, prompt)
    bot.register_next_step_handler(msg, callback)

@bot.message_handler(commands=["start", "menu"])
def start(message):
    if not require_membership(message):
        return
    bot.send_message(
        message.chat.id,
        "🛡️ <b>NetX Tools Pro</b>\n\n"
        "ከታች ያለውን ሜኑ ይምረጡ።",
        reply_markup=keyboard()
    )

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_callback(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "Membership confirmed!")
        try:
            bot.delete_message(
                call.message.chat.id, call.message.message_id
            )
        except Exception:
            pass
        bot.send_message(
            call.message.chat.id,
            "✅ አባልነት ተረጋግጧል።",
            reply_markup=keyboard()
        )
    else:
        bot.answer_callback_query(
            call.id,
            "ሁለቱንም ቻናሎች ይቀላቀሉ።",
            show_alert=True
        )

@bot.message_handler(
    func=lambda m: bool(m.text) and not m.text.startswith("/")
)
def menu_handler(message):
    if not require_membership(message):
        return

    text = message.text.strip()
    if text == "🌐 Subdomain Finder":
        ask_domain(
            message, "Domain ይላኩ (ለምሳሌ example.com):",
            subdomain_handler
        )
    elif text == "📡 Web Host Scanner":
        ask_domain(
            message, "ለመፈተሽ ፈቃድ ያለዎትን domain ይላኩ:",
            host_scan_handler
        )
    elif text == "🔍 DNS Lookup":
        ask_domain(message, "Domain ይላኩ:", dns_handler)
    elif text == "🔍 Domain & IP Recon":
        ask_domain(message, "Domain ወይም IP ይላኩ:", recon_handler)
    elif text == "📁 Bulk Domain Checker (.txt)":
        bot.send_message(
            message.chat.id,
            "አንድ domain በአንድ መስመር የያዘ .txt ፋይል ይላኩ።"
        )
    elif text == "🖼️ Image Info & Editor":
        bot.send_message(
            message.chat.id,
            "Photo ይላኩ። Caption ካካተቱ በምስሉ ላይ ይጨመራል።"
        )
    elif text == "📢 PROMOTION MARKET":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            "Contact Admin", url=ADMIN_LINK
        ))
        bot.send_message(
            message.chat.id, "Promotion / support:",
            reply_markup=markup
        )
    elif text == "🆘 Help / How to Use":
        bot.send_message(
            message.chat.id,
            "<b>Help</b>\n"
            "• Subdomain Finder: public certificate records.\n"
            "• DNS Lookup: DNS resolution.\n"
            "• Host Scanner: basic HTTP/HTTPS check.\n"
            "• Bulk Checker: send a .txt file.\n"
            "• Image: send a photo with optional caption."
        )
    else:
        bot.send_message(
            message.chat.id, "ከሜኑ ውስጥ አንዱን ይምረጡ።",
            reply_markup=keyboard()
        )

def subdomain_handler(message):
    domain = normalize_domain(message.text or "")
    if not domain:
        bot.send_message(message.chat.id, "⚠️ ትክክለኛ domain ይላኩ።")
        return

    status = bot.send_message(
        message.chat.id,
        f"🔎 <code>{esc(domain)}</code> በመፈለግ ላይ..."
    )
    try:
        response = session.get(
            "https://crt.sh/",
            params={"q": f"%.{domain}", "output": "json"},
            timeout=(5, 20)
        )
        
        if response.status_code != 200:
            log.warning(
                "crt.sh returned HTTP %s for %s",
                response.status_code,
                domain
            )
            found = set()
        else:
            data = response.json()
            found = set()

            for item in data if isinstance(data, list) else []:
                for name in str(
                    item.get("name_value", "")
                ).splitlines():
                    name = name.strip().lower().lstrip("*.")
                    if (
                        name == domain
                        or name.endswith("." + domain)
                    ):
                        if normalize_domain(name):
                            found.add(name)


        for item in data if isinstance(data, list) else []:
            for name in str(item.get("name_value", "")).splitlines():
                name = name.strip().lower().lstrip("*.")
                if name == domain or name.endswith("." + domain):
                    if normalize_domain(name):
                        found.add(name)

        if not found:
            bot.edit_message_text(
                f"⚠️ <code>{esc(domain)}</code> ላይ ውጤት አልተገኘም።",
                message.chat.id, status.message_id
            )
            return

        output = io.BytesIO(
            "\n".join(sorted(found)).encode("utf-8")
        )
        output.name = f"{domain}_subdomains.txt"

        try:
            bot.delete_message(
                message.chat.id, status.message_id
            )
        except Exception:
            pass

        bot.send_document(
            message.chat.id, output,
            caption=(
                f"✅ <b>Subdomain results</b>\n"
                f"Domain: <code>{esc(domain)}</code>\n"
                f"Count: <b>{len(found)}</b>\n"
                "Records do not guarantee that hosts are active."
            )
        )
    except Exception:
        log.exception("Subdomain lookup failed for %s", domain)
        try:
            bot.edit_message_text(
                "❌ ፍለጋው አልተሳካም። Render Logs ይመልከቱ።",
                message.chat.id, status.message_id
            )
        except Exception:
            pass

def dns_handler(message):
    domain = normalize_domain(message.text or "")
    if not domain:
        bot.send_message(message.chat.id, "⚠️ ትክክለኛ domain ይላኩ።")
        return
    try:
        records = socket.getaddrinfo(
            domain, None, type=socket.SOCK_STREAM
        )
        ips = sorted({item[4][0] for item in records})
        bot.send_message(
            message.chat.id,
            f"🔍 <b>DNS result</b>\n"
            f"Domain: <code>{esc(domain)}</code>\n"
            + "\n".join(f"• <code>{esc(ip)}</code>" for ip in ips[:20])
        )
    except Exception:
        log.exception("DNS lookup failed")
        bot.send_message(message.chat.id, "❌ DNS lookup አልተሳካም።")

def recon_handler(message):
    raw = (message.text or "").strip()
    try:
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", raw):
            ip = raw
        else:
            domain = normalize_domain(raw)
            if not domain:
                raise ValueError("Invalid domain or IP")
            ip = socket.gethostbyname(domain)

        result = session.get(
            f"http://ip-api.com/json/{quote(ip)}",
            timeout=(5, 10)
        ).json()
        if result.get("status") != "success":
            raise ValueError("IP information unavailable")

        bot.send_message(
            message.chat.id,
            f"🔍 <b>IP information</b>\n"
            f"Target: <code>{esc(raw)}</code>\n"
            f"IP: <code>{esc(ip)}</code>\n"
            f"Country: {esc(result.get('country'))}\n"
            f"City: {esc(result.get('city'))}\n"
            f"ISP: {esc(result.get('isp'))}"
        )
    except Exception:
        log.exception("Recon failed")
        bot.send_message(message.chat.id, "❌ መረጃውን ማግኘት አልተቻለም።")

def host_scan_handler(message):
    domain = normalize_domain(message.text or "")
    if not domain:
        bot.send_message(message.chat.id, "⚠️ ትክክለኛ domain ይላኩ።")
        return

    results = []
    for scheme in ("https", "http"):
        try:
            response = session.get(
                f"{scheme}://{domain}/",
                timeout=(5, 10),
                allow_redirects=True
            )
            results.append(
                f"• {scheme.upper()}: HTTP {response.status_code}; "
                f"Server: {esc(response.headers.get('Server', 'unknown'))}"
            )
        except requests.RequestException:
            results.append(f"• {scheme.upper()}: unavailable")

    bot.send_message(
        message.chat.id,
        f"📡 <b>Basic host check</b>\n"
        f"Domain: <code>{esc(domain)}</code>\n"
        + "\n".join(results)
        + "\nHTTP status alone does not identify a VPN/bypass host."
    )

@bot.message_handler(content_types=["document"])
def document_handler(message):
    if not require_membership(message):
        return

    document = message.document
    if not document.file_name or not document.file_name.lower().endswith(".txt"):
        bot.send_message(message.chat.id, "⚠️ .txt ፋይል ብቻ ይላኩ።")
        return
    if document.file_size and document.file_size > 1_000_000:
        bot.send_message(message.chat.id, "⚠️ ፋይሉ ከ1 MB በታች ይሁን።")
        return

    status = bot.send_message(message.chat.id, "⏳ ፋይሉ እየተፈተሸ ነው...")
    
    try:
        response = session.get(
            "https://crt.sh/",
            params={"q": f"%.{domain}", "output": "json"},
            timeout=(10, 60)
        )
        response.raise_for_status()
        data = response.json()
        found = set()

        for item in data if isinstance(data, list) else []:
            for name in str(item.get("name_value", "")).splitlines():
                name = name.strip().lower().lstrip("*.")
                if name == domain or name.endswith("." + domain):
                    if normalize_domain(name):
                        found.add(name)

    except requests.exceptions.Timeout:
        log.warning("crt.sh timed out for %s", domain)
        found = set()

    except requests.RequestException:
        log.exception("crt.sh request failed")
        found = set()

    except ValueError:
        log.exception("crt.sh returned invalid JSON")
        found = set()

        output = io.BytesIO(
            ("DOMAIN\tIP\tHTTP_STATUS\n" + "\n".join(lines)).encode()
        )
        output.name = "domain_check_report.txt"
        try:
            bot.delete_message(message.chat.id, status.message_id)
        except Exception:
            pass
        bot.send_document(
            message.chat.id, output,
            caption=f"✅ Checked {len(domains)} domains."
        )
    except Exception:
        log.exception("Document processing failed")
        bot.send_message(message.chat.id, "❌ ፋይሉን ማንበብ አልተቻለም።")

@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    if not require_membership(message):
        return
    try:
        info = bot.get_file(message.photo[-1].file_id)
        raw = bot.download_file(info.file_path)
        image = Image.open(io.BytesIO(raw))
        width, height = image.size
        image_format = image.format or "Unknown"
        caption = (message.caption or "").strip()

        if not caption:
            bot.send_message(
                message.chat.id,
                f"🖼️ <b>Image information</b>\n"
                f"Resolution: <code>{width}x{height}</code>\n"
                f"Format: <code>{esc(image_format)}</code>\n"
                f"Size: <code>{len(raw)/1024:.1f} KB</code>"
            )
            return

        image = ImageOps.exif_transpose(image).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        max_width = max(100, image.width - 24)
        words, lines, current = caption.split(), [], ""

        for word in words:
            trial = f"{current} {word}".strip()
            if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_height = 18
        box_height = min(image.height, len(lines) * line_height + 20)
        draw.rectangle(
            (0, image.height-box_height, image.width, image.height),
            fill=(0, 0, 0)
        )
        y = image.height - box_height + 10
        for line in lines:
            if y + line_height > image.height:
                break
            draw.text((12, y), line, fill=(255, 255, 255), font=font)
            y += line_height

        output = io.BytesIO()
        image.save(output, format="JPEG", quality=92)
        output.seek(0)
        output.name = "edited_image.jpg"
        bot.send_photo(
            message.chat.id, output,
            caption=f"🖼️ Edited image\nResolution: {width}x{height}"
        )
    except Exception:
        log.exception("Photo processing failed")
        bot.send_message(message.chat.id, "❌ ምስሉን ማስኬድ አልተቻለም።")

@app.get("/")
def home():
    return "NetX Tools Pro Bot is running.", 200

@app.get("/health")
def health():
    return {"status": "ok"}, 200

def run_flask():
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log.info("NetX Tools Pro bot starting")
    bot.infinity_polling(
        skip_pending=True, timeout=30, long_polling_timeout=30
    )
