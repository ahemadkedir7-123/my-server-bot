
import os
import io
import re
import socket
import logging
import threading
import ipaddress
from urllib.parse import urlparse

import requests
import telebot
from telebot import types
from flask import Flask
from PIL import Image, ImageDraw

# ==================================================
# 1. CONFIGURATION
# ==================================================

TOKEN = "8788982436:AAFTXTcXdwxUkR36DmzV8hGSiOMm-Ok28AM"
bot = telebot.TeleBot(TOKEN)

ADMIN_LINK = "https://t.me/Shemsadin_vip"

REQUIRED_CHANNELS = [
    "@Nur_Tunnel_free_ethiopian",
    "@freeinternat10",
]

CONNECT_TIMEOUT = 15
SUBDOMAIN_READ_TIMEOUT = 120
HTTP_READ_TIMEOUT = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("netx")

bot = telebot.TeleBot(TOKEN, threaded=True)
app = Flask(__name__)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "NetXToolsBot/1.0"
})

# ==================================================
# 2. COMMON HELPERS
# ==================================================

def normalize_domain(value):
    """Validate and normalize a domain name."""
    if not value:
        return None

    value = value.strip().lower().rstrip(".")

    if "://" in value:
        value = urlparse(value).hostname or ""

    if "/" in value:
        value = value.split("/", 1)[0]

    if ":" in value:
        # Do not accept host:port as a domain.
        return None

    if len(value) > 253:
        return None

    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    labels = value.split(".")

    if len(labels) < 2:
        return None

    for label in labels:
        if (
            not label
            or len(label) > 63
            or not re.fullmatch(r"[a-z0-9-]+", label)
            or label.startswith("-")
            or label.endswith("-")
        ):
            return None

    return value


def normalize_target(value):
    """Accept a domain or an IP address."""
    if not value:
        return None

    value = value.strip()

    if "://" in value:
        value = urlparse(value).hostname or ""

    value = value.split("/", 1)[0]

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return normalize_domain(value)


def safe_edit(chat_id, message_id, text):
    try:
        bot.edit_message_text(
            text,
            chat_id,
            message_id
        )
    except Exception:
        log.exception("Could not edit Telegram message")


def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(
                channel,
                user_id
            )

            if member.status not in (
                "creator",
                "administrator",
                "member"
            ):
                return False

        except Exception:
            log.exception(
                "Subscription check failed: %s",
                channel
            )
            return False

    return True


def get_new_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    markup.add(
        types.KeyboardButton("🌐 Subdomain Finder"),
        types.KeyboardButton("📡 Web Host Scanner"),
        types.KeyboardButton("📁 Bulk Bug Host Checker (.txt)"),
        types.KeyboardButton("🔍 DNS Lookup"),
        types.KeyboardButton("🔍 Domain & IP Recon"),
        types.KeyboardButton("🖼️ Image Info & Editor"),
        types.KeyboardButton("📢 PROMOTION MARKET"),
        types.KeyboardButton("🆘 Help / How to Use"),
    )

    return markup


def ask_for_domain(chat_id, prompt, callback):
    msg = bot.send_message(chat_id, prompt)
    bot.register_next_step_handler(msg, callback)


# ==================================================
# 3. START AND SUBSCRIPTION
# ==================================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id

    if not check_subscription(message.from_user.id):
        markup = types.InlineKeyboardMarkup()

        for channel in REQUIRED_CHANNELS:
            markup.add(
                types.InlineKeyboardButton(
                    f"Join {channel}",
                    url=f"https://t.me/{channel[1:]}"
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "✅ Check Subscription",
                callback_data="check_sub"
            )
        )

        bot.send_message(
            chat_id,
            "⚠️ ቦቱን ለመጠቀም ከታች ያሉትን "
            "ቻናሎች ተቀላቀል።\n\n"
            "ከተቀላቀልክ በኋላ Check Subscription ጫን።",
            reply_markup=markup
        )
        return

    bot.send_message(
        chat_id,
        "🛡️ NetX Tools Pro Bot\n\n"
        "እንኳን ደህና መጣህ!\n"
        "ከታች ያለውን ሜኑ ተጠቀም።",
        reply_markup=get_new_reply_keyboard()
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "check_sub"
)
def callback_check_sub(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if check_subscription(user_id):
        bot.answer_callback_query(
            call.id,
            "Subscription verified!"
        )

        try:
            bot.delete_message(
                chat_id,
                call.message.message_id
            )
        except Exception:
            pass

        bot.send_message(
            chat_id,
            "✅ ማረጋገጫው ተሳክቷል!",
            reply_markup=get_new_reply_keyboard()
        )
    else:
        bot.answer_callback_query(
            call.id,
            "እባክህ ሁለቱንም ቻናሎች ተቀላቀል።",
            show_alert=True
        )


# ==================================================
# 4. MAIN MENU
# ==================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: True
)
def handle_menu_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    if text.startswith("/"):
        return

    if not check_subscription(message.from_user.id):
        send_welcome(message)
        return

    if text == "🌐 Subdomain Finder":
        ask_for_domain(
            chat_id,
            "🌐 Subdomain Finder\n\n"
            "የሚፈትሹትን domain ላክ።\n"
            "ምሳሌ: example.com",
            process_super_subdomain
        )

    elif text == "📡 Web Host Scanner":
        ask_for_domain(
            chat_id,
            "📡 Web Host Scanner\n\n"
            "የራስህን ወይም የፈቃድ ያለህበትን "
            "domain ላክ።",
            process_web_scanner_pro
        )

    elif text == "📁 Bulk Bug Host Checker (.txt)":
        bot.send_message(
            chat_id,
            "📁 የራስህን ወይም የተፈቀደልህን "
            "ዶሜይኖች የያዘ .txt ፋይል ላክ።"
        )

    elif text == "🔍 DNS Lookup":
        ask_for_domain(
            chat_id,
            "🔍 DNS Lookup\n\nDomain ወይም IP ላክ።",
            process_dns_lookup
        )

    elif text == "🔍 Domain & IP Recon":
        ask_for_domain(
            chat_id,
            "🔍 Domain & IP Recon\n\nDomain ወይም IP ላክ።",
            process_ip_recon
        )

    elif text == "🖼️ Image Info & Editor":
        bot.send_message(
            chat_id,
            "🖼️ ምስል ላክ።\n"
            "የምስሉን መረጃ እንድንመለከት "
            "ያለ Caption ላክ።\n"
            "ጽሑፍ ለመጨመር Caption አያይዝ።"
        )

    elif text == "📢 PROMOTION MARKET":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "Contact Admin",
                url=ADMIN_LINK
            )
        )
        bot.send_message(
            chat_id,
            "📢 Promotion Market\n"
            "አስተዳዳሪን ለማነጋገር ከታች ጫን።",
            reply_markup=markup
        )

    elif text == "🆘 Help / How to Use":
        bot.send_message(
            chat_id,
            "🆘 NetX Tools Help\n\n"
            "🌐 Subdomain Finder: የሕዝብ DNS "
            "እና certificate መዝገቦችን ይፈልጋል።\n"
            "📡 Web Host Scanner: የHTTP ምላሽን "
            "ይፈትሻል።\n"
            "📁 Bulk Checker: .txt ፋይል ይቀበላል።\n"
            "🔍 DNS Lookup: IP መረጃ ያሳያል።\n"
            "🖼️ Image Editor: ምስል መረጃ እና "
            "Caption ያሳያል።"
        )

    else:
        bot.send_message(
            chat_id,
            "ከታች ካለው ሜኑ አንዱን ምረጥ።",
            reply_markup=get_new_reply_keyboard()
        )


# ==================================================
# 5. SUBDOMAIN FINDER
# ==================================================

def fetch_crtsh(domain):
    found = set()

    response = SESSION.get(
        "https://crt.sh/",
        params={
            "q": f"%.{domain}",
            "output": "json"
        },
        timeout=(
            CONNECT_TIMEOUT,
            SUBDOMAIN_READ_TIMEOUT
        )
    )

    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list):
        return found

    for record in data:
        raw_names = str(
            record.get("name_value", "")
        ).splitlines()

        for raw in raw_names:
            raw = raw.strip().lower()

            if raw.startswith("*."):
                raw = raw[2:]

            name = normalize_domain(raw)

            if name and (
                name == domain
                or name.endswith("." + domain)
            ):
                found.add(name)

    return found


def fetch_hackertarget(domain):
    found = set()

    response = SESSION.get(
        "https://api.hackertarget.com/hostsearch/",
        params={"q": domain},
        timeout=(CONNECT_TIMEOUT, 60)
    )

    response.raise_for_status()
    body = response.text.strip()

    if "api count exceeded" in body.lower():
        raise RuntimeError("HackerTarget API limit reached")

    if "error" in body.lower() and "," not in body:
        raise RuntimeError(body[:200])

    for line in body.splitlines():
        parts = line.split(",")

        if not parts:
            continue

        name = normalize_domain(parts[0])

        if name and (
            name == domain
            or name.endswith("." + domain)
        ):
            found.add(name)

    return found


def get_subdomains(domain):
    found = set()
    errors = []

    sources = [
        ("crt.sh", fetch_crtsh),
        ("HackerTarget", fetch_hackertarget),
    ]

    for source_name, source_func in sources:
        try:
            log.info(
                "Subdomain source started: %s / %s",
                source_name,
                domain
            )

            results = source_func(domain)
            found.update(results)

            log.info(
                "%s returned %s records",
                source_name,
                len(results)
            )

        except requests.Timeout:
            log.warning("%s timed out", source_name)
            errors.append(f"{source_name}: timeout")

        except Exception as exc:
            log.exception("%s failed", source_name)
            errors.append(
                f"{source_name}: {type(exc).__name__}"
            )

    return sorted(found), errors


def process_super_subdomain(message):
    chat_id = message.chat.id

    if not message.text:
        bot.send_message(chat_id, "⚠️ Domain ላክ።")
        return

    domain = normalize_domain(message.text)

    if not domain:
        bot.send_message(
            chat_id,
            "❌ Domain ትክክል አይደለም።\n"
            "ምሳሌ: example.com"
        )
        return

    processing = bot.send_message(
        chat_id,
        f"🔎 {domain} እየተፈለገ ነው።\n"
        "የሕዝብ መረጃ ምንጮች እየተፈተሹ ናቸው። "
        "እባክህ ጠብቅ።"
    )

    process_subdomain_direct(
        chat_id,
        domain,
        processing.message_id
    )


def process_subdomain_direct(chat_id, query, msg_id):
    domain = normalize_domain(query)

    if not domain:
        safe_edit(
            chat_id,
            msg_id,
            "❌ Domain ትክክል አይደለም።"
        )
        return

    try:
        subdomains, errors = get_subdomains(domain)

        if not subdomains:
            error_text = "\n".join(errors[:3])

            safe_edit(
                chat_id,
                msg_id,
                "⚠️ ምንም ውጤት አልተገኘም።\n"
                + (
                    error_text
                    or "የሕዝብ ምንጮቹ ውጤት አልመለሱም።"
                )
            )
            return

        file_content = "\n".join(subdomains)

        file_obj = io.BytesIO(
            file_content.encode("utf-8")
        )
        file_obj.name = f"{domain}_subdomains.txt"

        caption = (
            "✅ Subdomain results\n"
            f"Domain: {domain}\n"
            f"Count: {len(subdomains)}\n"
            "Records do not guarantee that hosts are active."
        )

        if errors:
            caption += (
                "\n⚠️ Some sources failed; results may be incomplete."
            )

        try:
            bot.delete_message(chat_id, msg_id)
        except Exception:
            pass

        bot.send_document(
            chat_id,
            file_obj,
            caption=caption
        )

    except Exception:
        log.exception(
            "Subdomain handler failed for %s",
            domain
        )

        safe_edit(
            chat_id,
            msg_id,
            "❌ ፍለጋው አልተሳካም። "
            "Render Logs ይመልከቱ።"
        )


# ==================================================
# 6. DNS LOOKUP
# ==================================================

def process_dns_lookup(message):
    chat_id = message.chat.id
    target = normalize_target(message.text or "")

    if not target:
        bot.send_message(chat_id, "❌ Domain/IP ትክክል አይደለም።")
        return

    try:
        ip = socket.gethostbyname(target)

        result = SESSION.get(
            f"http://ip-api.com/json/{ip}",
            params={
                "fields": "status,message,country,city,isp,as,query"
            },
            timeout=(CONNECT_TIMEOUT, HTTP_READ_TIMEOUT)
        ).json()

        bot.send_message(
            chat_id,
            "🔍 DNS LOOKUP RESULT\n\n"
            f"Domain/IP: {target}\n"
            f"Resolved IP: {ip}\n"
            f"Country: {result.get('country', 'N/A')}\n"
            f"City: {result.get('city', 'N/A')}\n"
            f"ISP: {result.get('isp', 'N/A')}\n"
            f"ASN: {result.get('as', 'N/A')}"
        )

    except Exception:
        log.exception("DNS lookup failed")
        bot.send_message(
            chat_id,
            "❌ DNS Lookup አልተሳካም። "
            "Domain/IP እንደገና ፈትሽ።"
        )


# ==================================================
# 7. WEB HOST SCANNER
# ==================================================

def process_web_scanner_pro(message):
    chat_id = message.chat.id
    domain = normalize_domain(message.text or "")

    if not domain:
        bot.send_message(chat_id, "❌ Domain ትክክል አይደለም።")
        return

    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        bot.send_message(chat_id, "❌ Domain ሊፈታ አልቻለም።")
        return

    processing = bot.send_message(
        chat_id,
        f"🔎 {domain} እየተፈተሸ ነው..."
    )

    results = []

    # Only check standard public web ports.
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}/"

        try:
            response = SESSION.get(
                url,
                timeout=(CONNECT_TIMEOUT, HTTP_READ_TIMEOUT),
                allow_redirects=True,
                stream=True
            )

            results.append(
                f"{scheme.upper()}: HTTP "
                f"{response.status_code} | "
                f"Server: {response.headers.get('Server', 'Unknown')}"
            )
            response.close()

        except requests.RequestException as exc:
            results.append(
                f"{scheme.upper()}: unavailable "
                f"({type(exc).__name__})"
            )

    safe_edit(
        chat_id,
        processing.message_id,
        "📡 WEB HOST SCAN\n\n"
        f"Domain: {domain}\n"
        f"IP: {ip}\n\n"
        + "\n".join(results)
        + "\n\nHTTP response does not establish VPN or tunnel compatibility."
    )


# ==================================================
# 8. DOMAIN AND IP RECON
# ==================================================

def process_ip_recon(message):
    chat_id = message.chat.id
    target = normalize_target(message.text or "")

    if not target:
        bot.send_message(chat_id, "❌ Domain/IP ትክክል አይደለም።")
        return

    try:
        ip = socket.gethostbyname(target)

        result = SESSION.get(
            f"http://ip-api.com/json/{ip}",
            params={
                "fields": "status,country,city,isp,query"
            },
            timeout=(CONNECT_TIMEOUT, HTTP_READ_TIMEOUT)
        ).json()

        bot.send_message(
            chat_id,
            "🔍 DOMAIN & IP RECON\n\n"
            f"Target: {target}\n"
            f"IP: {ip}\n"
            f"Country: {result.get('country', 'N/A')}\n"
            f"City: {result.get('city', 'N/A')}\n"
            f"ISP: {result.get('isp', 'N/A')}"
        )

    except Exception:
        log.exception("IP recon failed")
        bot.send_message(
            chat_id,
            "❌ መረጃውን ማግኘት አልተቻለም።"
        )


# ==================================================
# 9. BULK DOMAIN CHECKER
# ==================================================

@bot.message_handler(
    content_types=["document"]
)
def handle_document(message):
    chat_id = message.chat.id

    if not check_subscription(message.from_user.id):
        send_welcome(message)
        return

    filename = message.document.file_name or ""

    if not filename.lower().endswith(".txt"):
        bot.send_message(
            chat_id,
            "⚠️ .txt ፋይል ብቻ ላክ።"
        )
        return

    processing = bot.send_message(
        chat_id,
        "🔄 ፋይሉ እየተነበበ ነው..."
    )

    try:
        file_info = bot.get_file(
            message.document.file_id
        )
        downloaded = bot.download_file(
            file_info.file_path
        )

        if len(downloaded) > 2_000_000:
            safe_edit(
                chat_id,
                processing.message_id,
                "⚠️ ፋይሉ በጣም ትልቅ ነው።"
            )
            return

        content = downloaded.decode(
            "utf-8",
            errors="ignore"
        )

        domains = set()

        for line in content.splitlines():
            domain = normalize_domain(line)

            if domain:
                domains.add(domain)

        if not domains:
            safe_edit(
                chat_id,
                processing.message_id,
                "⚠️ ትክክለኛ domain አልተገኘም።"
            )
            return

        results = []

        for domain in sorted(domains)[:200]:
            try:
                ip = socket.gethostbyname(domain)
                response = SESSION.get(
                    f"https://{domain}/",
                    timeout=(5, 8),
                    allow_redirects=True,
                    stream=True
                )

                results.append(
                    f"{domain} | {ip} | "
                    f"HTTP {response.status_code}"
                )
                response.close()

            except Exception:
                results.append(
                    f"{domain} | unavailable"
                )

        output = io.BytesIO(
            "\n".join(results).encode("utf-8")
        )
        output.name = "domain_check_report.txt"

        try:
            bot.delete_message(
                chat_id,
                processing.message_id
            )
        except Exception:
            pass

        bot.send_document(
            chat_id,
            output,
            caption=(
                "✅ Domain check report\n"
                f"Processed: {len(results)}\n"
                "HTTP responses do not mean a host is a working bug host."
            )
        )

    except Exception:
        log.exception("Bulk checker failed")
        safe_edit(
            chat_id,
            processing.message_id,
            "❌ ፋይሉን ማንበብ አልተቻለም።"
        )


# ==================================================
# 10. IMAGE INFO AND CAPTION EDITOR
# ==================================================

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    chat_id = message.chat.id

    try:
        file_info = bot.get_file(
            message.photo[-1].file_id
        )
        downloaded = bot.download_file(
            file_info.file_path
        )

        if len(downloaded) > 10_000_000:
            bot.send_message(
                chat_id,
                "⚠️ ምስሉ በጣም ትልቅ ነው።"
            )
            return

        image = Image.open(
            io.BytesIO(downloaded)
        ).convert("RGB")

        width, height = image.size
        format_type = "JPEG"
        size_kb = round(len(downloaded) / 1024, 2)

        caption = message.caption or ""

        if caption:
            draw = ImageDraw.Draw(image)

            # Keep the caption area inside the image.
            y = max(0, height - 60)

            draw.rectangle(
                [0, y, width, height],
                fill=(0, 0, 0)
            )

            draw.text(
                (10, y + 10),
                caption[:500],
                fill=(255, 255, 255)
            )

            output = io.BytesIO()
            image.save(output, format="JPEG")
            output.seek(0)

            bot.send_photo(
                chat_id,
                output,
                caption=(
                    "✅ Image edited\n"
                    f"Resolution: {width}x{height}\n"
                    f"Original size: {size_kb} KB"
                )
            )

        else:
            bot.send_message(
                chat_id,
                "🖼️ IMAGE INFO\n\n"
                f"Resolution: {width}x{height}\n"
                f"Format: {format_type}\n"
                f"Original size: {size_kb} KB\n\n"
                "ጽሑፍ ለመጨመር ከፎቶው ጋር Caption ላክ።"
            )

    except Exception:
        log.exception("Image processing failed")
        bot.send_message(
            chat_id,
            "❌ ምስሉን ማስተካከል አልተቻለም።"
        )


# ==================================================
# 11. RENDER WEB SERVICE
# ==================================================

@app.route("/")
def home():
    return "NetX Tools Pro Bot is running!", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def run_flask():
    port = int(os.environ.get("PORT", "8080"))

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# ==================================================
# 12. START
# ==================================================

if __name__ == "__main__":
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )
    flask_thread.start()

    log.info("NetX Tools Pro Bot starting")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
