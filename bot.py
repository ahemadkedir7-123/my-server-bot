import os
import re
import io
import time
import ssl
import socket
import logging
import threading
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

import requests
import telebot
from telebot import types
from telebot.handler_backends import ContinueHandling
from flask import Flask, jsonify

# ==================================================
# CONFIGURATION
# ==================================================

BOT_TOKEN = "8788982436:AAGlEaGWZgwWFcvecIJgBUOAG5L9-oB-AV0" # እዚህ ጋር የእርስዎን ትክክለኛ ቦት ቶከን ያስገቡ
ADMIN_ID = 6668128978
ADMIN_CONTACT = "https://t.me/Nbreaker_bot"

CHANNELS = [
    "@freeinternat10",
    "@Nur_Tunnel_free_ethiopian"
]

CHANNEL_LINKS = [
    "https://t.me/freeinternat10",
    "https://t.me/Nur_Tunnel_free_ethiopian"
]

TELEBIRR_NAME = "ሸምሰዲን ሺፈ (Shemsadin Shifa)"
TELEBIRR_PHONE = "0915922481"

PORT = int(os.getenv("PORT", "10000"))
TIMEOUT = 12

if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError("Set your BOT_TOKEN environment variable.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("NetXToolsPro")

session = requests.Session()
session.headers.update({
    "User-Agent": "NetXToolsPro/20.0"
})

# ==================================================
# USER DATA
# ==================================================

user_points = {}
premium_users = {}
user_referrals = {}
referred_users = set()
waiting_for_tx = {}

# ==================================================
# GENERAL HELPERS
# ==================================================

def clean_domain(value):
    value = (value or "").strip().lower()

    if "://" in value:
        value = urlparse(value).hostname or value

    value = value.split("/")[0].split(":")[0].rstrip(".")

    pattern = (
        r"(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    return value if re.fullmatch(pattern, value) else None


def title_block(title, target=""):
    lines = [
        "╔══════════════════════════════════╗",
        "║          NETX TOOLS PRO          ║",
        f"║       {title.center(26)}       ║",
        "╚══════════════════════════════════╝"
    ]

    if target:
        lines.append(f"Target: {target}")

    lines.append(
        "Time UTC: " +
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )

    lines.append("")
    return lines


def menu():
    k = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    k.add(
        types.KeyboardButton("🌐 DNS Lookup"),
        types.KeyboardButton("🚀 Subdomain Finder"),
        types.KeyboardButton("🛠️ Advanced Pentest Tools"),
        types.KeyboardButton("🔍 Host Scanner (Bug Host)"),
        types.KeyboardButton("📦 Bulk Host Checker"),
        types.KeyboardButton("💎 Get Unlimited / Premium"),
        types.KeyboardButton("👥 Referral Program"),
        types.KeyboardButton("👤 My Profile / Points"),
        types.KeyboardButton("👨‍💻 Admin Contact")
    )

    return k


def is_premium(uid):
    if uid not in premium_users:
        return False

    expiry = premium_users[uid]

    if expiry is None:
        return True

    if expiry > datetime.now(timezone.utc):
        return True

    premium_users.pop(uid, None)
    return False


def check_and_deduct_point(uid):
    if is_premium(uid):
        return True

    points = user_points.get(uid, 20)

    if points <= 0:
        return False

    user_points[uid] = points - 1
    return True


def send_txt(chat_id, filename, content, caption):
    data = io.BytesIO(content.encode("utf-8"))
    data.name = filename

    bot.send_document(
        chat_id,
        data,
        caption=caption
    )


# ==================================================
# CHANNEL SUBSCRIPTION CHECK
# ==================================================

def check_membership(user_id):
    missing = []

    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)

            if member.status in ("creator", "administrator", "member"):
                continue

            if member.status == "restricted" and getattr(
                member, "is_member", False
            ):
                continue

            missing.append(channel)

        except Exception:
            log.exception("Channel membership check failed: %s", channel)
            missing.append(channel)

    return missing


def send_join_message(chat_id, missing=None):
    markup = types.InlineKeyboardMarkup(row_width=1)

    for link in CHANNEL_LINKS:
        markup.add(
            types.InlineKeyboardButton(
                "📢 Join Channel",
                url=link
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "✅ I Joined - Check Again",
            callback_data="check_membership"
        )
    )

    bot.send_message(
        chat_id,
        "🔒 NETX TOOLS PRO - CHANNEL VERIFICATION\n\n"
        "ቦቱን ለመጠቀም ሁለቱንም Channels መቀላቀል አለብዎት።\n"
        "ከተቀላቀሉ በኋላ I Joined የሚለውን ይጫኑ።",
        reply_markup=markup
    )


def membership_required(message):
    uid = message.from_user.id

    # Admin bypass
    if uid == ADMIN_ID:
        return True

    missing = check_membership(uid)

    if missing:
        send_join_message(message.chat.id, missing)
        return False

    return True


@bot.callback_query_handler(
    func=lambda c: c.data == "check_membership"
)
def check_membership_callback(call):
    uid = call.from_user.id

    if uid == ADMIN_ID or not check_membership(uid):
        bot.answer_callback_query(
            call.id,
            "✅ Membership verified!",
            show_alert=True
        )

        bot.send_message(
            call.message.chat.id,
            "✅ ሁለቱም Channels ተረጋግጠዋል።",
            reply_markup=menu()
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ ሁለቱንም Channels አልተቀላቀሉም።",
            show_alert=True
        )


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):
    if not membership_required(message):
        return

    uid = message.from_user.id

    user_points.setdefault(uid, 20)

    args = message.text.split()

    if len(args) > 1 and args[1].startswith("REF_"):
        try:
            referrer = int(args[1].split("_")[1])

            if referrer != uid and uid not in referred_users:
                referred_users.add(uid)

                user_points[referrer] = (
                    user_points.get(referrer, 20) + 20
                )

                user_referrals.setdefault(
                    referrer, set()
                ).add(uid)

                try:
                    bot.send_message(
                        referrer,
                        "🎉 አዲስ Referral ገብቷል። +20 Points!"
                    )
                except Exception:
                    pass

        except Exception:
            pass

    bot.send_message(
        uid,
        "🚀 NETX TOOLS PRO\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 Points: {user_points[uid]}\n\n"
        "🌐 DNS Lookup\n"
        "🚀 Subdomain Finder\n"
        "🛠️ Advanced Security Report\n"
        "🔍 Detailed Host Checker\n"
        "💎 Premium Access\n\n"
        "በፈቃድ ባለዎት ድረ-ገጾች ላይ ብቻ ይጠቀሙ።",
        reply_markup=menu()
    )


# ==================================================
# ADMIN COMMANDS
# ==================================================

@bot.message_handler(commands=["approve"])
def approve_month(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Usage: /approve USER_ID")
        return

    uid = int(parts[1])

    premium_users[uid] = (
        datetime.now(timezone.utc) + timedelta(days=30)
    )

    bot.reply_to(message, f"✅ User {uid} approved for 30 days.")

    try:
        bot.send_message(uid, "🎉 Monthly Premium ተከፍቷል!")
    except Exception:
        pass


@bot.message_handler(commands=["approve_year"])
def approve_year(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) != 2 or not parts[1].isdigit():
        bot.reply_to(message, "Usage: /approve_year USER_ID")
        return

    uid = int(parts[1])

    premium_users[uid] = (
        datetime.now(timezone.utc) + timedelta(days=365)
    )

    bot.reply_to(message, f"✅ User {uid} approved for 365 days.")

    try:
        bot.send_message(uid, "🎉 Yearly Premium ተከፍቷል!")
    except Exception:
        pass

    @bot.message_handler(commands=['reject'])
def reject_payment(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ ይህን ትዕዛዝ መጠቀም የሚችለው Admin ብቻ ነው።")
        return

    parts = message.text.split(maxsplit=2)

    if len(parts) < 2:
        bot.reply_to(
            message,
            "⚠️ አጠቃቀም:\n"
            "/reject USER_ID ምክንያት\n\n"
            "ምሳሌ:\n"
            "/reject 8608096447 የክፍያ ማረጋገጫው አልተረጋገጠም።"
        )
        return

    try:
        user_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ User ID ትክክል አይደለም።")
        return

    reason = parts[2] if len(parts) > 2 else "የክፍያ ማረጋገጫው አልተቀበለም።"

    # የክፍያ ማስረጃ መጠባበቂያን አጽዳ
    if isinstance(waiting_for_tx, dict):
        waiting_for_tx.pop(user_id, None)
    elif isinstance(waiting_for_tx, set):
        waiting_for_tx.discard(user_id)

    try:
        bot.send_message(
            user_id,
            "❌ **የክፍያ ጥያቄዎ ውድቅ ተደርጓል።**\n\n"
            f"📌 ምክንያት: {reason}\n\n"
            "እባክዎ ማስረጃዎን ደግመው ያረጋግጡ።\n"
            "ለተጨማሪ እገዛ Admin ያነጋግሩ።",
            parse_mode="Markdown"
        )

        bot.reply_to(
            message,
            f"✅ User {user_id} የክፍያ ጥያቄ ውድቅ ተደርጓል።"
        )

    except Exception as e:
        bot.reply_to(
            message,
            f"⚠️ ውድቅ ተደርጓል፣ ግን ለተጠቃሚው መልዕክት መላክ አልተቻለም።\n{e}"
        )
@bot.message_handler(commands=["revoke"])
def revoke_user(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    if len(parts) == 2 and parts[1].isdigit():
        uid = int(parts[1])
        premium_users.pop(uid, None)

        bot.reply_to(message, f"❌ Premium revoked for {uid}.")
    else:
        bot.reply_to(message, "Usage: /revoke USER_ID")


# ==================================================
# DOMAIN INPUT
# ==================================================

def ask_domain(message, callback):
    uid = message.from_user.id

    if not membership_required(message):
        return

    if not is_premium(uid) and user_points.get(uid, 20) <= 0:
        bot.send_message(
            message.chat.id,
            "❌ Points አልቋል። Premium ይግዙ ወይም Referral ይጠቀሙ።"
        )
        return

    prompt = bot.send_message(
        message.chat.id,
        "🌐 Domain ያስገቡ። ምሳሌ: example.com"
    )

    bot.register_next_step_handler(prompt, callback)


def validate(message):
    domain = clean_domain(message.text)

    if not domain:
        bot.reply_to(
            message,
            "❌ ትክክለኛ Domain ያስገቡ።"
        )

    return domain


# ==================================================
# DNS LOOKUP
# ==================================================

def dns_result(domain):
    lines = title_block("DNS LOOKUP", domain)

    try:
        ips = sorted({
            item[4][0]
            for item in socket.getaddrinfo(
                domain,
                None,
                type=socket.SOCK_STREAM
            )
        })

        lines.append(f"Total IPs: {len(ips)}")

        for ip in ips[:30]:
            lines.append(f"• {ip}")

    except Exception as e:
        lines.append(f"DNS Error: {type(e).__name__}")

    return "\n".join(lines)


def dns_handler(message):
    if not membership_required(message):
        return

    domain = validate(message)

    if not domain:
        return

    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።")
        return

    bot.send_message(
        message.chat.id,
        dns_result(domain)
    )


# ==================================================
# SUBDOMAIN FINDER
# ==================================================

def domain_ok_sub(sub, domain):
    pattern = (
        r"(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    return (
        bool(re.fullmatch(pattern, sub))
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
            response = session.get(
                url,
                params=params,
                timeout=TIMEOUT
            )

            if response.status_code != 200:
                notes.append(f"{name}: HTTP {response.status_code}")
                continue

            if name == "crt.sh":
                for record in response.json():
                    for raw in record.get("name_value", "").splitlines():
                        sub = raw.strip().lower().rstrip(".")

                        if sub.startswith("*."):
                            sub = sub[2:]

                        if domain_ok_sub(sub, domain):
                            found.add(sub)

            elif name == "AlienVault":
                for record in response.json().get("passive_dns", []):
                    sub = (
                        record.get("hostname", "")
                        .strip().lower().rstrip(".")
                    )

                    if domain_ok_sub(sub, domain):
                        found.add(sub)

            elif name == "HackerTarget":
                for line in response.text.splitlines():
                    sub = line.split(",")[0].strip().lower().rstrip(".")

                    if domain_ok_sub(sub, domain):
                        found.add(sub)

            notes.append(f"{name}: OK")

        except Exception as e:
            notes.append(f"{name}: {type(e).__name__}")

    return sorted(found), notes


def subdomain_handler(message):
    if not membership_required(message):
        return

    domain = validate(message)

    if not domain:
        return

    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።")
        return

    status = bot.send_message(
        message.chat.id,
        f"🔎 {domain} እየተመረመረ ነው..."
    )

    found, notes = find_subdomains(domain)

    try:
        bot.delete_message(
            message.chat.id,
            status.message_id
        )
    except Exception:
        pass

    if not found:
        bot.send_message(
            message.chat.id,
            "⚠️ Subdomain አልተገኘም።"
        )
        return

    report = title_block("SUBDOMAIN REPORT", domain)
    report.append(f"Total Found: {len(found)}")
    report.append("")

    report.extend(found)
    report.append("")
    report.append("SOURCE STATUS")
    report.extend(notes)

    send_txt(
        message.chat.id,
        f"subdomains_{domain}.txt",
        "\n".join(report),
        f"Subdomain Report: {domain}"
    )


# ==================================================
# TLS INFORMATION
# ==================================================

def tls_information(domain, port=443):
    result = []

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, port),
            timeout=TIMEOUT
        ) as sock:

            with context.wrap_socket(
                sock,
                server_hostname=domain
            ) as tls:

                result.append(f"TLS Version: {tls.version()}")
                result.append(
                    f"Cipher: {tls.cipher()[0] if tls.cipher() else 'Unknown'}"
                )

                cert = tls.getpeercert()

                if cert:
                    result.append("Certificate: Present")

                    subject = dict(
                        x[0] for x in cert.get("subject", [])
                    )

                    issuer = dict(
                        x[0] for x in cert.get("issuer", [])
                    )

                    result.append(
                        f"Certificate Subject: {subject.get('commonName', 'Unknown')}"
                    )

                    result.append(
                        f"Certificate Issuer: {issuer.get('commonName', 'Unknown')}"
                    )

                    result.append(
                        f"Valid Until: {cert.get('notAfter', 'Unknown')}"
                    )

    except Exception as e:
        result.append(f"TLS Error: {type(e).__name__}")

    return result


# ==================================================
# DETAILED HOST CHECKER
# ==================================================

def host_scanner_report(domain):
    lines = title_block("WEB HOST SCANNER", domain)
    lines.append("=" * 35)

    # DNS
    try:
        ips = sorted({
            item[4][0]
            for item in socket.getaddrinfo(
                domain,
                None,
                type=socket.SOCK_STREAM
            )
        })

        lines.append("IP ADDRESSES:")
        for ip in ips:
            lines.append(f"  • {ip}")

    except Exception as e:
        lines.append(f"DNS ERROR: {type(e).__name__}")

    lines.append("")
    lines.append("PORT CHECK RESULTS")
    lines.append("Ports: 80, 443, 8080, 8443")
    lines.append("")

    ports = [
        (80, "http"),
        (443, "https"),
        (8080, "http"),
        (8443, "https")
    ]

    for port, scheme in ports:
        lines.append("-" * 35)
        lines.append(f"{scheme.upper()} PORT: {port}")

        # Connection check
        try:
            with socket.create_connection(
                (domain, port),
                timeout=5
            ):
                lines.append("Port Status: OPEN")

        except OSError:
            lines.append("Port Status: CLOSED / TIMEOUT")
            continue

        url = f"{scheme}://{domain}:{port}/"

        try:
            response = session.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=False,
                stream=True
            )

            lines.append(
                f"HTTP Status: {response.status_code} "
                f"{response.reason}"
            )

            lines.append(
                f"Server: {response.headers.get('Server', 'Not Disclosed')}"
            )

            lines.append(
                f"Connection: {response.headers.get('Connection', 'Not Disclosed')}"
            )

            location = response.headers.get("Location")

            if location:
                lines.append(f"Redirect: {location[:250]}")
            else:
                lines.append("Redirect: None")

            response.close()

        except requests.RequestException as e:
            lines.append(f"HTTP Error: {type(e).__name__}")
            continue

        # GET
        try:
            r = session.get(
                url,
                timeout=TIMEOUT,
                allow_redirects=False,
                stream=True
            )

            lines.append(f"GET: {r.status_code}")
            r.close()

        except requests.RequestException:
            lines.append("GET: Failed")

        # HEAD
        try:
            r = session.head(
                url,
                timeout=TIMEOUT,
                allow_redirects=False
            )

            lines.append(f"HEAD: {r.status_code}")

        except requests.RequestException:
            lines.append("HEAD: Failed")

        # OPTIONS
        try:
            r = session.options(
                url,
                timeout=TIMEOUT,
                allow_redirects=False
            )

            lines.append(f"OPTIONS: {r.status_code}")

            allow = r.headers.get("Allow", "Not disclosed")
            lines.append(f"Allow Header: {allow}")

        except requests.RequestException:
            lines.append("OPTIONS: Failed")

        # TLS
        if scheme == "https":
            lines.append("TLS INFORMATION:")

            lines.extend(
                tls_information(domain, port)
            )

        lines.append("")

    lines.append("=" * 35)
    lines.append("End of Host Scanner Report")

    return "\n".join(lines)


def host_scanner_handler(message):
    if not membership_required(message):
        return

    domain = validate(message)

    if not domain:
        return

    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።")
        return

    status = bot.send_message(
        message.chat.id,
        f"🔍 Host Checker: {domain}\n"
        "የHTTP እና TLS መረጃ እየተሰበሰበ ነው..."
    )

    try:
        report = host_scanner_report(domain)

        try:
            bot.delete_message(
                message.chat.id,
                status.message_id
            )
        except Exception:
            pass

        send_txt(
            message.chat.id,
            f"host_scanner_{domain}.txt",
            report,
            f"🛡️ Detailed Host Scanner Report: {domain}"
        )

    except Exception:
        log.exception("Host scanner failed")
        bot.send_message(
            message.chat.id,
            "❌ Host Scanner ስህተት አጋጥሞታል።"
        )


# ==================================================
# ADVANCED PENTEST / SECURITY REPORT
# ==================================================

def advanced_pentest_report(domain):
    lines = title_block("ADVANCED SECURITY REPORT", domain)

    url = f"https://{domain}/"

    try:
        started = time.perf_counter()

        response = session.get(
            url,
            timeout=TIMEOUT,
            allow_redirects=True,
            stream=True
        )

        elapsed = round(
            (time.perf_counter() - started) * 1000
        )

        lines.extend([
            "GENERAL INFORMATION",
            f"HTTP Status: {response.status_code}",
            f"Response Time: {elapsed} ms",
            f"Final URL: {response.url[:250]}",
            f"Server: {response.headers.get('Server', 'Not Disclosed')}",
            f"Powered By: {response.headers.get('X-Powered-By', 'Not Disclosed')}",
            ""
        ])

        lines.append("SECURITY HEADERS")

        security_headers = {
            "Strict-Transport-Security":
                "HSTS",
            "Content-Security-Policy":
                "CSP",
            "X-Content-Type-Options":
                "Content Type Protection",
            "Referrer-Policy":
                "Referrer Policy",
            "Permissions-Policy":
                "Permissions Policy",
            "X-Frame-Options":
                "Clickjacking Protection"
        }

        for header, description in security_headers.items():
            value = response.headers.get(header)

            if value:
                lines.append(
                    f"[PRESENT] {header}: {value[:180]}"
                )
            else:
                lines.append(
                    f"[MISSING] {header}: {description}"
                )

        lines.append("")

        lines.append("HTTP RESPONSE HEADERS")

        for key, value in response.headers.items():
            lines.append(f"{key}: {value[:200]}")

        response.close()

    except Exception as e:
        lines.append(
            f"HTTPS Request Error: {type(e).__name__}"
        )

    lines.append("")
    lines.append("TLS DETAILS")
    lines.extend(tls_information(domain, 443))

    lines.append("")
    lines.append("HTTP OPTIONS INFORMATION")

    try:
        r = session.options(
            url,
            timeout=TIMEOUT,
            allow_redirects=False
        )

        lines.append(f"OPTIONS Status: {r.status_code}")
        lines.append(
            f"Allow Header: {r.headers.get('Allow', 'Not Disclosed')}"
        )

    except Exception as e:
        lines.append(f"OPTIONS Error: {type(e).__name__}")

    lines.append("")
    lines.append("REPORT COMPLETE")

    return "\n".join(lines)


def pentest_handler(message):
    if not membership_required(message):
        return

    domain = validate(message)

    if not domain:
        return

    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።")
        return

    status = bot.send_message(
        message.chat.id,
        f"🛠️ Advanced Security Report: {domain}\n"
        "እየተዘጋጀ ነው..."
    )

    try:
        report = advanced_pentest_report(domain)

        try:
            bot.delete_message(
                message.chat.id,
                status.message_id
            )
        except Exception:
            pass

        send_txt(
            message.chat.id,
            f"pentest_report_{domain}.txt",
            report,
            f"🛡️ Advanced Security Report: {domain}"
        )

    except Exception:
        log.exception("Pentest report failed")
        bot.send_message(
            message.chat.id,
            "❌ Security Report ማዘጋጀት አልተቻለም።"
        )


# ==================================================
# BULK HOST CHECKER
# ==================================================

def bulk_handler(message):
    if not membership_required(message):
        return

    uid = message.from_user.id

    if not check_and_deduct_point(uid):
        bot.reply_to(message, "❌ Points አልቋል።")
        return

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

    domains = []

    for line in content.splitlines():
        domain = clean_domain(line)

        if domain and domain not in domains:
            domains.append(domain)

    if not domains:
        bot.reply_to(message, "❌ Domain አልተገኘም።")
        return

    # Keep bulk requests bounded
    domains = domains[:100]

    lines = title_block("BULK HOST REPORT")
    lines.append(f"Total Domains: {len(domains)}")
    lines.append("")

    for domain in domains:
        lines.append(f"DOMAIN: {domain}")

        try:
            response = session.get(
                f"https://{domain}/",
                timeout=TIMEOUT,
                allow_redirects=True,
                stream=True
            )

            lines.append(
                f"HTTPS Status: {response.status_code}"
            )

            lines.append(
                f"Server: {response.headers.get('Server', 'Unknown')}"
            )

            response.close()

        except Exception as e:
            lines.append(
                f"HTTPS Error: {type(e).__name__}"
            )

        lines.append("")

    send_txt(
        message.chat.id,
        "netx_bulk_report.txt",
        "\n".join(lines),
        "📦 Bulk Host Report"
    )


# ==================================================
# PREMIUM PAYMENT
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data in ["buy_month", "buy_year"]
)
def premium_callback(call):
    uid = call.from_user.id

    if uid != ADMIN_ID and check_membership(uid):
        bot.answer_callback_query(
            call.id,
            "Join both channels first.",
            show_alert=True
        )
        send_join_message(call.message.chat.id)
        return

    bot.answer_callback_query(call.id)

    if call.data == "buy_month":
        plan = {
            "plan_name": "Monthly",
            "price": "100 ETB",
            "plan_code": "month"
        }
    else:
        plan = {
            "plan_name": "Yearly",
            "price": "400 ETB",
            "plan_code": "year"
        }

    waiting_for_tx[uid] = plan

    bot.send_message(
        call.message.chat.id,
        f"💎 Package: {plan['plan_name']}\n"
        f"💰 Price: {plan['price']}\n\n"
        f"Telebirr Number: {TELEBIRR_PHONE}\n"
        f"Account Name: {TELEBIRR_NAME}\n\n"
        "ክፍያውን ከፈጸሙ በኋላ ከሚከተሉት አንዱን ይላኩ:\n"
        "📸 Screenshot\n"
        "📁 Document\n"
        "📝 Transaction ID\n\n"
        "/cancel በመጻፍ መሰረዝ ይችላሉ።"
    )


@bot.message_handler(
    content_types=["photo", "document", "text"],
    func=lambda m: m.chat.id in waiting_for_tx
)
def handle_payment_evidence(message):
    if not membership_required(message):
        return

    uid = message.from_user.id
    plan = waiting_for_tx.get(uid)

    if not plan:
        return

    if message.content_type == "text":
        tx = (message.text or "").strip()

        if tx.lower() == "/cancel":
            waiting_for_tx.pop(uid, None)
            bot.reply_to(message, "❌ Payment cancelled.")
            return

        evidence = f"Transaction ID: {tx}"

    elif message.content_type == "photo":
        evidence = "Payment Screenshot"

    elif message.content_type == "document":
        evidence = "Payment Document"

    else:
        return

    username = message.from_user.username or "None"

    caption = (
        "🔔 NEW PAYMENT SUBMISSION\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"User ID: {uid}\n"
        f"Username: @{username}\n"
        f"Package: {plan['plan_name']}\n"
        f"Price: {plan['price']}\n"
        f"Evidence: {evidence}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"Monthly: /approve {uid}\n"
        f"Yearly: /approve_year {uid}"
    )

    try:
        if message.content_type == "photo":
            bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=caption
            )

        elif message.content_type == "document":
            bot.send_document(
                ADMIN_ID,
                message.document.file_id,
                caption=caption
            )

        else:
            bot.send_message(
                ADMIN_ID,
                caption
            )

        waiting_for_tx.pop(uid, None)

        bot.reply_to(
            message,
            "✅ የክፍያ ማስረጃዎ ለአድሚን ተልኳል። "
            "ከተረጋገጠ በኋላ Premium ይከፈታል።"
        )

    except Exception:
        log.exception("Payment forwarding failed")
        bot.reply_to(
            message,
            "❌ ማስረጃውን መላክ አልተቻለም።"
        )


# ==================================================
# MAIN MENU ROUTER
# ==================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda m: True
)
def route(message):
    if not membership_required(message):
        return

    text = (message.text or "").strip()
    uid = message.from_user.id

    user_points.setdefault(uid, 20)

    if text == "🌐 DNS Lookup":
        ask_domain(message, dns_handler)

    elif text == "🚀 Subdomain Finder":
        ask_domain(message, subdomain_handler)

    elif text == "🛠️ Advanced Pentest Tools":
        ask_domain(message, pentest_handler)

    elif text == "🔍 Host Scanner (Bug Host)":
        ask_domain(message, host_scanner_handler)

    elif text == "📦 Bulk Host Checker":
        prompt = bot.send_message(
            message.chat.id,
            "TXT File ወይም Domains በአዲስ መስመር ይላኩ።"
        )

        bot.register_next_step_handler(
            prompt,
            bulk_handler
        )

    elif text == "👤 My Profile / Points":
        active = is_premium(uid)

        status = "Premium Active" if active else "Free User"
        points = "Unlimited" if active else user_points.get(uid, 20)

        bot.send_message(
            message.chat.id,
            "👤 USER PROFILE\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"ID: {uid}\n"
            f"Status: {status}\n"
            f"Points: {points}"
        )

    elif text == "👥 Referral Program":
        link = (
            f"https://t.me/{bot.get_me().username}"
            f"?start=REF_{uid}"
        )

        bot.send_message(
            message.chat.id,
            f"👥 REFERRAL PROGRAM\n\n"
            f"Your Link:\n{link}\n\n"
            "አዲስ ተጠቃሚ ሲገባ +20 Points ያገኛሉ።"
        )

    elif text == "💎 Get Unlimited / Premium":
        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(
                "📅 Monthly - 100 ETB",
                callback_data="buy_month"
            ),
            types.InlineKeyboardButton(
                "📆 Yearly - 400 ETB",
                callback_data="buy_year"
            )
        )

        bot.send_message(
            message.chat.id,
            "💎 PREMIUM ACCESS\n"
            "የሚፈልጉትን ፓኬጅ ይምረጡ።",
            reply_markup=markup
        )

    elif text == "👨‍💻 Admin Contact":
        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "Contact Admin",
                url=ADMIN_CONTACT
            )
        )

        bot.send_message(
            message.chat.id,
            "NETX TOOLS PRO - ADMIN CONTACT",
            reply_markup=markup
        )

    else:
        bot.send_message(
            message.chat.id,
            "ከምናሌው አንዱን ይምረጡ።",
            reply_markup=menu()
        )


# ==================================================
# FLASK HEALTH CHECK
# ==================================================

@app.route("/")
def home():
    return jsonify({
        "service": "NetXToolsPro",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    log.info("NetXToolsPro started")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=60
                )
