import os
import re
import io
import time
import socket
import logging
import threading
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import requests
import telebot
from telebot import types
from flask import Flask, jsonify

# ==========================================
# CONFIGURATIONS
# ==========================================

BOT_TOKEN = "8788982436:AAGlEaGWZgwWFcvecIJgBUOAG5L9-oB-AV0" # እዚህ ጋር የእርስዎን ትክክለኛ ቦት ቶከን ያስገቡ
ADMIN_CONTACT = "https://t.me/None_Breaker"
ADMIN_ID = 6668128978

TELEBIRR_NAME = "ሸምሰዲን ሺፈ (Shemsadin Shifa)"
TELEBIRR_PHONE = "0915922481"

PORT = int(os.getenv("PORT", "10000"))
TIMEOUT = 60

SECURITY_HEADERS_LIST = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "X-Frame-Options"
]

if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError("Please configure BOT_TOKEN.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("NetXToolsPro")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 NetXToolsPro/19.0"
})

# ==========================================
# DATABASE / USER STATES
# ==========================================

user_points = {}
premium_users = {}
user_referrals = {}
referred_users = set()

# Stores selected payment plan for each user
waiting_for_tx = {}


# ==========================================
# HELPERS
# ==========================================

def clean_domain(value):
    val = (value or "").strip().lower()

    if "://" in val:
        val = urlparse(val).hostname or val.split("://")[1]

    val = val.split("/")[0].split(":")[0].rstrip(".")

    pat = (
        r"(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    return val if re.fullmatch(pat, val) else None


def title_block(title, target=""):
    lines = [
        "╔══════════════════════════════════╗",
        "║          🛡️ NETX TOOLS PRO       ║",
        f"║       {title.center(26)}       ║",
        "╚══════════════════════════════════╝"
    ]

    if target:
        lines.append(f"🎯 Target: {target}")

    lines.append(
        f"🕒 Time UTC: "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    lines.append("")
    return lines


def menu():
    k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    k.add(
        types.KeyboardButton("🌐 DNS Lookup"),
        types.KeyboardButton("🚀 Subdomain Finder"),
        types.KeyboardButton("🛠️ Advanced Pentest Tools"),
        types.KeyboardButton("🔍 Host Scanner (Bug Host)"),
        types.KeyboardButton("📦 Bulk Host Checker (Unlimited)"),
        types.KeyboardButton("💎 Get Unlimited / Premium"),
        types.KeyboardButton("👥 Referral Program"),
        types.KeyboardButton("👤 My Profile / Points"),
        types.KeyboardButton("👨‍💻 Admin Contact"),
    )

    return k


def is_premium(chat_id):
    if chat_id in premium_users:
        expiry = premium_users[chat_id]

        if expiry is None or expiry > datetime.now(timezone.utc):
            return True

        del premium_users[chat_id]

    return False


def check_and_deduct_point(chat_id):
    if is_premium(chat_id):
        return True

    current_pts = user_points.get(chat_id, 20)

    if current_pts <= 0:
        return False

    user_points[chat_id] = current_pts - 1
    return True


def ask_domain(message, callback):
    chat_id = message.chat.id

    if not is_premium(chat_id) and user_points.get(chat_id, 20) <= 0:
        bot.send_message(
            chat_id,
            "❌ የፖይንት ገደብዎ አልቋል!\n\n"
            "💎 Premium ይግዙ ወይም Referral Program ይጠቀሙ።"
        )
        return

    m = bot.send_message(
        chat_id,
        "🌐 የሚፈልጉትን ዶሜይን ያስገቡ።\n"
        "ምሳሌ: google.com"
    )

    bot.register_next_step_handler(m, callback)


def validate(message):
    d = clean_domain(message.text)

    if not d:
        bot.reply_to(
            message,
            "❌ ትክክለኛ ዶሜይን አልገባም።"
        )

    return d


def send_txt(chat_id, filename, text, caption):
    data = io.BytesIO(text.encode("utf-8"))
    data.name = filename

    bot.send_document(
        chat_id,
        data,
        caption=caption
    )


# ==========================================
# START COMMAND
# ==========================================

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    if chat_id not in user_points:
        user_points[chat_id] = 20

    args = message.text.split()

    if len(args) > 1 and args[1].startswith("REF_"):
        try:
            referrer_id = int(args[1].split("_")[1])

            if referrer_id != chat_id and chat_id not in referred_users:
                referred_users.add(chat_id)

                user_points[referrer_id] = (
                    user_points.get(referrer_id, 20) + 20
                )

                user_referrals.setdefault(
                    referrer_id, set()
                ).add(chat_id)

                try:
                    bot.send_message(
                        referrer_id,
                        "🎉 አዲስ ሰው በReferral Linkዎ ገብቷል። "
                        "+20 Points አግኝተዋል!"
                    )
                except Exception:
                    pass

        except Exception:
            pass

    bot.send_message(
        chat_id,
        "🚀 NETX TOOLS PRO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 ቀሪ Points: {user_points.get(chat_id, 20)}\n\n"
        "🌐 DNS Lookup\n"
        "🚀 Subdomain Finder\n"
        "🛠️ Security Analysis\n"
        "🔍 Host Scanner\n"
        "💎 Premium Access\n\n"
        "ፈቃድ ባለዎት ሲስተሞች ላይ ብቻ ይጠቀሙ።",
        reply_markup=menu()
    )


# ==========================================
# ADMIN APPROVAL
# ==========================================

@bot.message_handler(commands=["approve"])
def approve_month(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])

        expiry = datetime.now(timezone.utc) + timedelta(days=30)
        premium_users[uid] = expiry

        bot.reply_to(
            message,
            f"✅ User {uid} approved for 30 days."
        )

        try:
            bot.send_message(
                uid,
                "🎉 ክፍያዎ ተረጋግጧል። "
                "የ1 ወር Premium ተከፍቷል!"
            )
        except Exception:
            pass

    else:
        bot.reply_to(message, "Usage: /approve USER_ID")


@bot.message_handler(commands=["approve_year"])
def approve_year(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])

        expiry = datetime.now(timezone.utc) + timedelta(days=365)
        premium_users[uid] = expiry

        bot.reply_to(
            message,
            f"✅ User {uid} approved for 365 days."
        )

        try:
            bot.send_message(
                uid,
                "🎉 ክፍያዎ ተረጋግጧል። "
                "የ1 ዓመት Premium ተከፍቷል!"
            )
        except Exception:
            pass

    else:
        bot.reply_to(message, "Usage: /approve_year USER_ID")


@bot.message_handler(commands=["revoke"])
def revoke_user(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])
        premium_users.pop(uid, None)

        bot.reply_to(
            message,
            f"❌ User {uid} Premium revoked."
        )

    else:
        bot.reply_to(message, "Usage: /revoke USER_ID")


# ==========================================
# SUBDOMAIN FINDER
# ==========================================

def domain_ok_sub(sub, domain):
    pat = (
        r"(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    return (
        bool(re.fullmatch(pat, sub))
        and (sub == domain or sub.endswith("." + domain))
    )


def find_subdomains(domain):
    found = set()
    notes = []

    sources = [
        (
            "crt.sh",
            "https://crt.sh/",
            {"q": f"%.{domain}", "output": "json"}
        ),
        (
            "AlienVault",
            f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns",
            None
        ),
        (
            "HackerTarget",
            f"https://api.hackertarget.com/hostsearch/?q={domain}",
            None
        )
    ]

    for name, url, params in sources:
        try:
            r = session.get(
                url,
                params=params,
                timeout=20
            )

            if r.status_code != 200:
                notes.append(f"⚠️ {name}: HTTP {r.status_code}")
                continue

            if name == "crt.sh":
                for rec in r.json():
                    for raw in rec.get("name_value", "").splitlines():
                        sub = raw.strip().lower().rstrip(".")

                        if sub.startswith("*."):
                            sub = sub[2:]

                        if domain_ok_sub(sub, domain):
                            found.add(sub)

            elif name == "AlienVault":
                for record in r.json().get("passive_dns", []):
                    sub = record.get("hostname", "").strip().lower().rstrip(".")

                    if domain_ok_sub(sub, domain):
                        found.add(sub)

            elif name == "HackerTarget":
                for line in r.text.splitlines():
                    parts = line.split(",")

                    if parts:
                        sub = parts[0].strip().lower().rstrip(".")

                        if domain_ok_sub(sub, domain):
                            found.add(sub)

            notes.append(f"✅ {name}: Active")

        except Exception as e:
            notes.append(f"⚠️ {name}: {type(e).__name__}")

    return sorted(found), notes


def subdomain_handler(message):
    chat_id = message.chat.id

    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ Points አልቋል።")
        return

    d = validate(message)

    if not d:
        return

    m = bot.send_message(
        chat_id,
        f"🚀 {d} እየተመረመረ ነው..."
    )

    found, notes = find_subdomains(d)

    try:
        bot.delete_message(chat_id, m.message_id)
    except Exception:
        pass

    if not found:
        bot.send_message(chat_id, f"⚠️ {d} ላይ ውጤት አልተገኘም።")
        return

    content = "\n".join(found)

    if len(found) <= 10:
        bot.send_message(
            chat_id,
            f"📊 Total Found: {len(found)}\n\n{content}"
        )
    else:
        send_txt(
            chat_id,
            f"subdomains_{d}.txt",
            content,
            f"Subdomain Report: {d}"
        )


# ==========================================
# ADVANCED SECURITY REPORT
# ==========================================

def advanced_pentest_report(domain):
    lines = title_block("SECURITY REPORT", domain)

    url = f"https://{domain}/"

    try:
        t = time.perf_counter()

        r = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True
        )

        ms = round((time.perf_counter() - t) * 1000)

        lines += [
            f"Target Status: {r.status_code}",
            f"Response Time: {ms} ms",
            f"Final URL: {r.url[:150]}",
            f"Server: {r.headers.get('Server', 'Not Disclosed')}",
            "",
            "SECURITY HEADERS:"
        ]

        for h in SECURITY_HEADERS_LIST:
            status = "Present" if h in r.headers else "Missing"
            lines.append(f"{h}: {status}")

    except Exception as e:
        lines.append(f"Connection failed: {type(e).__name__}")

    return "\n".join(lines)


def pentest_handler(message):
    chat_id = message.chat.id

    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ Points አልቋል።")
        return

    d = validate(message)

    if not d:
        return

    report = advanced_pentest_report(d)

    send_txt(
        chat_id,
        f"security_report_{d}.txt",
        report,
        f"Security Report: {d}"
    )


# ==========================================
# HOST SCANNER
# ==========================================

def host_scanner_report(domain):
    lines = title_block("HOST SCANNER", domain)

    try:
        ips = sorted({
            x[4][0]
            for x in socket.getaddrinfo(
                domain,
                None,
                type=socket.SOCK_STREAM
            )
        })

        lines.append(f"IPs: {', '.join(ips[:3])}")

    except Exception:
        lines.append("DNS Resolution Failed")

    try:
        r = session.get(
            f"https://{domain}/",
            timeout=TIMEOUT
        )

        lines.append(f"HTTP Status: {r.status_code}")
        lines.append(f"Server: {r.headers.get('Server', 'Unknown')}")

    except Exception as e:
        lines.append(f"HTTPS failed: {type(e).__name__}")

    return "\n".join(lines)


def host_scanner_handler(message):
    chat_id = message.chat.id

    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ Points አልቋል።")
        return

    d = validate(message)

    if not d:
        return

    report = host_scanner_report(d)

    send_txt(
        chat_id,
        f"host_report_{d}.txt",
        report,
        f"Host Report: {d}"
    )


# ==========================================
# BULK HOST CHECKER
# ==========================================

def check_bulk_host(domain):
    try:
        r = session.get(
            f"https://{domain}/",
            timeout=TIMEOUT
        )

        return [
            f"🎯 {domain}",
            f"Status: {r.status_code}",
            f"Server: {r.headers.get('Server', 'Unknown')}"
        ]

    except Exception:
        return [
            f"🎯 {domain}",
            "Status: No Response"
        ]


def bulk_handler(message):
    chat_id = message.chat.id

    domains = []

    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)

            content = downloaded.decode(
                "utf-8",
                errors="ignore"
            )

        except Exception:
            bot.reply_to(message, "❌ File ማንበብ አልተቻለም።")
            return

    else:
        content = message.text or ""

    for item in content.splitlines():
        d = clean_domain(item)

        if d and d not in domains:
            domains.append(d)

    if not domains:
        bot.reply_to(message, "❌ Domain አልተገኘም።")
        return

    lines = title_block("BULK HOST REPORT")

    for d in domains[:100]:
        lines.extend(check_bulk_host(d))
        lines.append("")

    send_txt(
        chat_id,
        "bulk_host_report.txt",
        "\n".join(lines),
        "Bulk Host Report"
    )


# ==========================================
# PREMIUM PAYMENT SYSTEM
# ==========================================

@bot.callback_query_handler(
    func=lambda c: c.data in ["buy_month", "buy_year"]
)
def premium_callback(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id

    if call.data == "buy_month":
        plan_name = "1 ወር (Monthly)"
        price = "100 ETB"
        plan_code = "month"

    else:
        plan_name = "1 ዓመት (Yearly)"
        price = "400 ETB"
        plan_code = "year"

    waiting_for_tx[chat_id] = {
        "plan_name": plan_name,
        "price": price,
        "plan_code": plan_code
    }

    bot.send_message(
        chat_id,
        f"💎 የተመረጠው ፓኬጅ: {plan_name}\n"
        f"💰 ዋጋ: {price}\n\n"
        f"💳 Telebirr ቁጥር: {TELEBIRR_PHONE}\n"
        f"👤 ስም: {TELEBIRR_NAME}\n\n"
        "ክፍያውን ከፈጸሙ በኋላ ከሚከተሉት አንዱን ይላኩ:\n\n"
        "📸 Screenshot\n"
        "📁 Document\n"
        "📝 Transaction ID\n\n"
        "ለመሰረዝ /cancel ይጻፉ።"
    )


@bot.message_handler(
    content_types=["photo", "document", "text"],
    func=lambda m: m.chat.id in waiting_for_tx
)
def handle_payment_evidence(message):
    chat_id = message.chat.id

    plan = waiting_for_tx.get(chat_id)

    if not plan:
        return

    if message.content_type == "text":
        tx_code = (message.text or "").strip()

        if tx_code.lower() == "/cancel":
            waiting_for_tx.pop(chat_id, None)

            bot.reply_to(
                message,
                "❌ የክፍያ ሂደቱ ተሰርዟል።"
            )
            return

        if not tx_code:
            bot.reply_to(
                message,
                "Transaction ID ወይም Screenshot ይላኩ።"
            )
            return

        evidence = f"Transaction ID: {tx_code}"

    elif message.content_type == "photo":
        evidence = "Payment Screenshot"

    elif message.content_type == "document":
        evidence = "Payment Document"

    else:
        return

    username = message.from_user.username or "None"

    admin_caption = (
        "🔔 NEW PAYMENT SUBMISSION\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"User ID: {chat_id}\n"
        f"Username: @{username}\n"
        f"Package: {plan['plan_name']}\n"
        f"Price: {plan['price']}\n"
        f"Evidence: {evidence}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Monthly: /approve {chat_id}\n"
        f"Yearly: /approve_year {chat_id}"
    )

    try:
        if message.content_type == "photo":
            bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=admin_caption
            )

        elif message.content_type == "document":
            bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=admin_caption
            )

        else:
            bot.send_message(
                ADMIN_ID,
                admin_caption
            )

        waiting_for_tx.pop(chat_id, None)

        bot.reply_to(
            message,
            "✅ የክፍያ ማስረጃዎ ለአድሚን ተልኳል።\n"
            "አድሚኑ ካረጋገጠ በኋላ Premium ይከፈትልዎታል።"
        )

    except Exception:
        log.exception("Payment evidence forwarding failed")

        bot.reply_to(
            message,
            "❌ ማስረጃውን መላክ አልተቻለም። "
            "እንደገና ይሞክሩ።"
        )


# ==========================================
# MAIN MENU ROUTER
# ==========================================

@bot.message_handler(content_types=["text"], func=lambda m: True)
def route(message):
    text = (message.text or "").strip()
    chat_id = message.chat.id

    if text == "🌐 DNS Lookup":
        ask_domain(
            message,
            lambda m: bot.send_message(
                chat_id,
                dns_result(validate(m))[:4000]
                if validate(m) else "Invalid domain"
            )
        )

    elif text == "🚀 Subdomain Finder":
        ask_domain(message, subdomain_handler)

    elif text == "🛠️ Advanced Pentest Tools":
        ask_domain(message, pentest_handler)

    elif text == "🔍 Host Scanner (Bug Host)":
        ask_domain(message, host_scanner_handler)

    elif text == "📦 Bulk Host Checker (Unlimited)":
        p = bot.send_message(
            chat_id,
            "የDomain ዝርዝር ይላኩ ወይም TXT File ያያይዙ።"
        )

        bot.register_next_step_handler(p, bulk_handler)

    elif text == "👤 My Profile / Points":
        active = is_premium(chat_id)

        status = (
            "Premium Active"
            if active else "Free User"
        )

        points = (
            "Unlimited"
            if active else str(user_points.get(chat_id, 20))
        )

        bot.send_message(
            chat_id,
            f"👤 USER PROFILE\n"
            f"Telegram ID: {chat_id}\n"
            f"Status: {status}\n"
            f"Points: {points}"
        )

    elif text == "👥 Referral Program":
        ref_link = (
            f"https://t.me/{bot.get_me().username}"
            f"?start=REF_{chat_id}"
        )

        bot.send_message(
            chat_id,
            f"👥 REFERRAL PROGRAM\n\n"
            f"Referral Link:\n{ref_link}\n\n"
            "አዲስ ተጠቃሚ ሲገባ +20 Points ያገኛሉ።"
        )

    elif text == "💎 Get Unlimited / Premium":
        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(
                "📅 1 ወር — 100 ETB",
                callback_data="buy_month"
            ),
            types.InlineKeyboardButton(
                "📆 1 ዓመት — 400 ETB",
                callback_data="buy_year"
            )
        )

        bot.send_message(
            chat_id,
            "💎 PREMIUM ACCESS\n"
            "የሚፈልጉትን ፓኬጅ ይምረጡ።",
            reply_markup=markup
        )

    elif text == "👨‍💻 Admin Contact":
        k = types.InlineKeyboardMarkup()

        k.add(
            types.InlineKeyboardButton(
                "Contact Admin",
                url=ADMIN_CONTACT
            )
        )

        bot.send_message(
            chat_id,
            "NETX TOOLS PRO — ADMIN CONTACT",
            reply_markup=k
        )

    else:
        bot.send_message(
            chat_id,
            "እባክዎ ከምናሌው አንዱን ይምረጡ።",
            reply_markup=menu()
        )


# ==========================================
# DNS LOOKUP
# ==========================================

def dns_result(domain):
    lines = title_block("DNS LOOKUP", domain)

    try:
        ips = sorted({
            x[4][0]
            for x in socket.getaddrinfo(
                domain,
                None,
                type=socket.SOCK_STREAM
            )
        })

        lines.append(f"Total IPs Found: {len(ips)}")

        for ip in ips[:25]:
            lines.append(f"• {ip}")

    except Exception as e:
        lines.append(f"DNS failed: {type(e).__name__}")

    return "\n".join(lines)


# ==========================================
# FLASK HEALTH CHECK
# ==========================================

@app.route("/")
def home():
    return jsonify({
        "service": "NetXToolsPro",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    }), 200


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False
    )


# ==========================================
# START BOT
# ==========================================

if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    log.info("NetXToolsPro starting...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=60
        )
