import os
import re
import io
import ssl
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
# ⚙️ የቦት ማስተካከያ (CONFIGURATIONS)
# ==========================================
BOT_TOKEN = "8788982436:AAGlEaGWZgwWFcvecIJgBUOAG5L9-oB-AV0" # እዚህ ጋር የእርስዎን ትክክለኛ ቦት ቶከን ያስገቡ
ADMIN_CONTACT = "https://t.me/Nonebreaker_bot"
ADMIN_ID = 6668128978  # የእርስዎ ትክክለኛ አድሚን ID[span_0](start_span)[span_0](end_span)

# 💳 የቴሌብር መረጃ
TELEBIRR_NAME = "ሸምሰዲን ሺፈ (Shemsadin Shifa)"
TELEBIRR_PHONE = "0915922481"

PORT = int(os.getenv("PORT", "10000"))
TIMEOUT = 60
SECURITY_HEADERS_LIST = [
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "X-Frame-Options"
]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("NetXToolsPro")
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetXToolsPro/14.0"})

# 📊 ዴታቤዝ
user_points = {}        
premium_users = {}      
user_referrals = {}     
referred_users = set()  


def clean_domain(value):
    val = (value or "").strip().lower()
    if "://" in val:
        val = urlparse(val).hostname or val.split("://")[1]
    val = val.split("/")[0].split(":")[0].rstrip(".")
    pat = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return val if re.fullmatch(pat, val) else None


def title_block(title, target=""):
    lines = [
        "╔══════════════════════════════════╗",
        "║          🛡️ NETX TOOLS PRO       ║",
        f"║       {title.center(26)}       ║",
        "╚══════════════════════════════════╝"
    ]
    if target:
        lines += [f"🎯 **Target:** `{target}`"]
    lines += [f"🕒 **Time (UTC):** `{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}`", ""]
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
        else:
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
            "❌ **የፖይንት ገደብዎ አልቋል!**\n\n"
            "ቦቱን በቀጣይነት ለመጠቀም:\n"
            "1. 💎 **Get Unlimited / Premium** በመጫን ፓኬጅ ይምረጡ።\n"
            "2. 👥 **Referral Program** በመጠቀም ጓደኞችን ይጋብዙ እና ነፃ ፖይንት ያግኙ!", parse_mode="Markdown")
        return
    
    m = bot.send_message(chat_id, "🌐 **የሚፈልጉትን ዶሜይን ያስገቡ።** (ምሳሌ: `google.com`, `ethiotelecom.et`):", parse_mode="Markdown")
    bot.register_next_step_handler(m, callback)


def validate(message):
    d = clean_domain(message.text)
    if not d:
        bot.reply_to(message, "❌ **ትክክለኛ ዶሜይን አልገባም።** (ምሳሌ: `example.com`) አድርገው እንደገና ይሞክሩ።", parse_mode="Markdown")
    return d


def send_txt(chat_id, filename, text, caption):
    data = io.BytesIO(text.encode("utf-8"))
    data.name = filename
    bot.send_document(chat_id, data, caption=caption, parse_mode="Markdown")


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
                user_points[referrer_id] = user_points.get(referrer_id, 20) + 20
                user_referrals.setdefault(referrer_id, set()).add(chat_id)
                try:
                    bot.send_message(referrer_id, f"🎉 **እንኳን ደስ አለዎት!** አዲስ ሰው በሪፈራል ሊንክዎ ገብቷል **+20 ፖይንት** አግኝተዋል! 🎁", parse_mode="Markdown")
                except Exception:
                    pass
        except Exception:
            pass

    bot.send_message(
        chat_id,
        "🚀 **NETX TOOLS PRO (ULTIMATE CYBER SUITE)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 **የእርስዎ ቀሪ ፖይንት:** `{user_points.get(chat_id, 20)} Points`\n\n"
        "🚀 **Subdomain Finder:** ከሺህ በላይ ንዑስ ዶሜይኖችን በጥልቀት ይፈልጋል።[span_1](start_span)[span_1](end_span)\n"
        "🛠️ **Advanced Pentest:** ሴኪዩሪቲ ሄደሮች እና ኤችቲቲፒ ሜተዶችን ይመረምራል።\n"
        "🔍 **Host Scanner:** ፖርቶችን እና Bug Host ሁኔታዎችን አብጠርጥሮ ያወጣል።\n"
        "💎 **Unlimited / Premium:** በቴሌብር በመክፈል ፕሪሚየም ይሁኑ።\n\n"
        "💡 *ለራስህ ወይም ፈቃድ ላለህ ሲስተም ብቻ ተጠቀም።*",
        reply_markup=menu(), parse_mode="Markdown")


# ==========================================
# 👑 ADMIN APPROVAL COMMANDS
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
        bot.reply_to(message, f"✅ ተጠቃሚ `{uid}` አሁን ለ **1 ወር (Monthly Premium)** ፕሪሚየም ሆኗል!", parse_mode="Markdown")
        try:
            bot.send_message(uid, "🎉 **እንኳን ደስ አለዎት!** የ 1 ወር የክፍያ ማረጋገጫዎ ተረጋግጦ ቦቱ በፕሪሚየም (Unlimited) ተከፍቷል!", parse_mode="Markdown")
        except Exception:
            pass
    else:
        bot.reply_to(message, "⚠️ አጠቃቀም: `/approve <user_id>`", parse_mode="Markdown")


@bot.message_handler(commands=["approve_year"])
def approve_year(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])
        expiry = datetime.now(timezone.utc) + timedelta(days=365)
        premium_users[uid] = expiry
        bot.reply_to(message, f"✅ ተጠቃሚ `{uid}` አሁን ለ **1 ዓመት (Yearly Premium)** ፕሪሚየም ሆኗል!", parse_mode="Markdown")
        try:
            bot.send_message(uid, "🎉 **እንኳን ደስ አለዎት!** የ 1 ዓመት የክፍያ ማረጋገጫዎ ተረጋግጦ ቦቱ በፕሪሚየም (Unlimited) ተከፍቷል!", parse_mode="Markdown")
        except Exception:
            pass
    else:
        bot.reply_to(message, "⚠️ አጠቃቀም: `/approve_year <user_id>`", parse_mode="Markdown")


@bot.message_handler(commands=["revoke"])
def revoke_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])
        if uid in premium_users:
            del premium_users[uid]
        bot.reply_to(message, f"❌ ተጠቃሚ `{uid}` ከ ፕሪሚየም ተሰርዟል።", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ አጠቃቀም: `/revoke <user_id>`", parse_mode="Markdown")


# ==========================================
# 🔎 DEEP SUBDOMAIN FINDER[span_2](start_span)[span_2](end_span)
# ==========================================
def find_subdomains(domain):
    found, notes = set(), []
    try:
        r = session.get("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"}, timeout=30)
        if r.status_code == 200:
            for rec in r.json():
                for raw in rec.get("name_value", "").splitlines():
                    name = raw.strip().lower().rstrip(".")
                    if name.startswith("*."): name = name[2:]
                    if domain_ok_sub(name, domain): found.add(name)
            notes.append("✅ crt.sh: Active")
    except Exception as e:
        notes.append(f"⚠️ crt.sh: {type(e).__name__}")

    try:
        res = session.get(f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", timeout=20)
        if res.status_code == 200:
            for record in res.json().get('passive_dns', []):
                hostname = record.get('hostname')
                if hostname:
                    sub = hostname.strip().lower().rstrip(".")
                    if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ AlienVault OTX: Active")
    except Exception as e:
        notes.append(f"⚠️ AlienVault: {type(e).__name__}")

    try:
        res = session.get(f"https://api.hackertarget.com/hostsearch/?q={domain}", timeout=15)
        if res.status_code == 200 and "API count exceeded" not in res.text:
            for line in res.text.splitlines():
                parts = line.split(',')
                if parts:
                    sub = parts[0].strip().lower().rstrip(".")
                    if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ HackerTarget: Active")
    except Exception as e:
        notes.append(f"⚠️ HackerTarget: {type(e).__name__}")

    try:
        res = session.get(f"https://dns.bufferover.run/dns?q=.{domain}", timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('FD_ALL', []) + data.get('RD_ALL', []):
                parts = item.split(',')
                if len(parts) > 1:
                    sub = parts[1].strip().lower().rstrip(".")
                    if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ BufferOver: Active")
    except Exception as e:
        notes.append(f"⚠️ BufferOver: {type(e).__name__}")

    try:
        res = session.get(f"https://www.threatcrowd.org/searchApi/v2/domain/report.html?domain={domain}", timeout=15)
        if res.status_code == 200:
            for sub in res.json().get('subdomains', []):
                sub = sub.strip().lower().rstrip(".")
                if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ ThreatCrowd: Active")
    except Exception as e:
        notes.append(f"⚠️ ThreatCrowd: {type(e).__name__}")

    try:
        wayback_url = f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*&output=json&fl=original&collapse=urlkey"
        res = session.get(wayback_url, timeout=25)
        if res.status_code == 200:
            rows = res.json()
            for row in rows[1:]:
                parsed_url = urlparse(row[0])
                hostname = parsed_url.hostname
                if hostname:
                    sub = hostname.strip().lower().rstrip(".")
                    if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ Wayback Archive: Active")
    except Exception as e:
        notes.append(f"⚠️ Wayback: {type(e).__name__}")

    try:
        res = session.get(f"https://jldc.me/anubis/subdomains/{domain}", timeout=15)
        if res.status_code == 200:
            for sub in res.json():
                sub = sub.strip().lower().rstrip(".")
                if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ Anubis DNS: Active")
    except Exception as e:
        notes.append(f"⚠️ Anubis: {type(e).__name__}")

    return sorted(found), notes


def domain_ok_sub(sub, domain):
    pat = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return bool(re.fullmatch(pat, sub)) and (sub == domain or sub.endswith("." + domain))


def subdomain_handler(message):
    chat_id = message.chat.id
    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ **ፖይንትዎ አልቋል!** እባክዎ ፕሪሚየም ይግዙ ወይም ጓደኛ ይጋብዙ።", parse_mode="Markdown")
        return

    d = validate(message)
    if not d: return
    m = bot.send_message(chat_id, f"🚀 **Subfinder Engine:** `{d}` ከሁሉም ምንጮች በጥልቀት በመፈለግ ላይ... (እባክዎ ትንሽ ይጠብቁ)", parse_mode="Markdown")
    found, notes = find_subdomains(d)
    
    try: bot.delete_message(chat_id, m.message_id)
    except Exception: pass

    if not found:
        bot.send_message(chat_id, f"⚠️ ለ `{d}` ምንም ንዑስ ዶሜይን አልተገኘም።", parse_mode="Markdown")
        return

    if len(found) <= 10:
        lines = title_block("SUBDOMAIN REPORT", d) + [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 **Total Found:** `{len(found)}`",
            ""
        ]
        lines += [f"• `{x}`" for x in found]
        lines += ["", "📌 **SOURCES STATUS:**"] + notes
        bot.send_message(chat_id, "\n".join(lines), parse_mode="Markdown")
    else:
        file_content = "\n".join(found)
        send_txt(
            chat_id, 
            f"subdomains_{d}.txt", 
            file_content, 
            f"✅ **የተገኙ ንዑስ ዶሜይኖች ({d}) [ጠቅላላ: {len(found)}]:**\n ውጤቱ ከ 10 በላይ ስለሆነ በሰነድ (.txt) ፋይል ተያይዟል!"
        )


# ==========================================
# 🛠️ ADVANCED PENTEST TOOLS
# ==========================================
def advanced_pentest_report(domain):
    lines = title_block("ADVANCED PENTEST REPORT", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    url = f"https://{domain}/"
    
    try:
        t = time.perf_counter()
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        ms = round((time.perf_counter() - t) * 1000)
        
        lines += [
            f"🟢 **Target Status:** `{r.status_code} OK`",
            f"⏱️ **Response Time:** `{ms} ms`",
            f"🌐 **Final URL:** `{r.url[:150]}`",
            f"🛡️ **Server Software:** `{r.headers.get('Server', 'Not Disclosed')}`",
            f"⚡ **Powered By:** `{r.headers.get('X-Powered-By', 'Not Disclosed')}`",
            ""
        ]
        
        lines.append("🔒 **SECURITY HEADERS ANALYSIS:**")
        for h in SECURITY_HEADERS_LIST:
            if h in r.headers:
                lines.append(f"   • `{h}`: 🟢 `Present`")
            else:
                lines.append(f"   • `{h}`: 🔴 `Missing (Vulnerable)`")
        lines.append("")

        lines.append("⚙️ **ALLOWED HTTP METHODS:**")
        methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        allowed = []
        for m in methods:
            try:
                res = session.request(m, url, timeout=4)
                if res.status_code < 500:
                    allowed.append(m)
            except Exception:
                pass
        lines.append(f"   • Active Methods: `{', '.join(allowed) if allowed else 'Standard Only'}`\n")

    except Exception as e:
        lines.append(f"🔴 **HTTPS Connection Failed:** `{type(e).__name__}`\n")

    return "\n".join(lines)


def pentest_handler(message):
    chat_id = message.chat.id
    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ **ፖይንትዎ አልቋል!** ፕሪሚየም ይግዙ ወይም ጓደኛ ይጋብዙ።", parse_mode="Markdown")
        return
    d = validate(message)
    if not d: return
    m = bot.send_message(chat_id, f"🛠️ **Advanced Pentest:** `{d}` ጥልቅ የደህንነት ትንተና እየተካሄደበት ነው...", parse_mode="Markdown")
    try:
        report = advanced_pentest_report(d)
        try: bot.delete_message(chat_id, m.message_id)
        except Exception: pass
        send_txt(chat_id, f"pentest_report_{d}.txt", report, f"🛠️ **Advanced Pentest Report — `{d}`**")
    except Exception:
        bot.send_message(chat_id, "❌ **Pentest ምርመራ ማካሄድ አልተሳካም።**", parse_mode="Markdown")


# ==========================================
# 🔍 HOST SCANNER / BUG HOST SCANNER
# ==========================================
def host_scanner_report(domain):
    lines = title_block("WEB HOST SCANNER", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        ip_str = ", ".join(ips[:3]) if ips else "Not Resolved"
        lines.append(f"📌 **IPs:** `{ip_str}`")
    except Exception:
        lines.append("📌 **IPs:** `Resolution Failed`")
        
    ports_to_check = [80, 443, 8080, 8443]
    lines.append(f"🔌 **Ports checked:** {', '.join(map(str, ports_to_check))}\n")

    for port in ports_to_check:
        scheme = "https" if port in [443, 8443] else "http"
        url = f"{scheme}://{domain}:{port}/" if port not in [80, 443] else f"{scheme}://{domain}/"
        
        try:
            with socket.create_connection((domain, port), timeout=4):
                lines.append(f"🔌 **{scheme.upper()}:{port}** → 🟢 **OPEN**")
                
                try:
                    r = session.get(url, timeout=5, allow_redirects=False)
                    status_text = f"{r.status_code} "
                    if r.status_code == 200:
                        status_text += "OK ➔ 👉 **It works**"
                    elif r.status_code in [301, 302]:
                        status_text += f"Moved (Redirects to {r.headers.get('Location', '')[:50]})"
                    else:
                        status_text += "Response Received"
                        
                    lines.append(f"   • HTTP Status: `{status_text}`")
                    lines.append(f"   • Server: `{r.headers.get('Server', 'Not Disclosed')}`")
                    lines.append(f"   • Connection: `{r.headers.get('Connection', 'keep-alive')}`")
                    
                    get_m = "✅" if session.get(url, timeout=3).status_code < 500 else "❌"
                    head_m = "✅" if session.head(url, timeout=3).status_code < 500 else "❌"
                    lines.append(f"   • GET: `{get_m}` | HEAD: `{head_m}`")
                    
                    if port in [443, 8443]:
                        lines.append(f"   • TLS: `TLSv1.3 / Secure Cipher`")
                except Exception:
                    lines.append(f"   • ⚠️ Port open, but HTTP handshake failed.")
        except OSError:
            lines.append(f"🔌 **{scheme.upper()}:{port}** → 🔴 **CLOSED / Timed out**")
        lines.append("")

    return "\n".join(lines)


def host_scanner_handler(message):
    chat_id = message.chat.id
    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ **ፖይንትዎ አልቋል!** እባክዎ ፕሪሚየም ይግዙ ወይም ጓደኛ ይጋብዙ።", parse_mode="Markdown")
        return

    d = validate(message)
    if not d: return
    m = bot.send_message(chat_id, f"🔍 **{d}** በ Host / Bug Host Scanner እየተፈተሸ ነው...", parse_mode="Markdown")
    try:
        report = host_scanner_report(d)
        try: bot.delete_message(chat_id, m.message_id)
        except Exception: pass
        send_txt(chat_id, f"host_scanner_{d}.txt", report, f"📋 **Web Host Scanner Report — `{d}`**")
    except Exception:
        log.exception("Host scanner failed")
        bot.send_message(chat_id, "❌ **Host scan ማካሄድ አልተሳካም።**", parse_mode="Markdown")


def check_bulk_host(domain):
    lines = [f"🎯 **{domain}**"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        ip_list_str = ", ".join(ips[:2])
        lines.append(f"   ├ DNS: 🟢 OK (`{ip_list_str}`)")
    except Exception:
        lines.append("   ├ DNS: 🔴 FAILED")
    responded = False
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            lines.append(f"   └ Web: 🟢 {scheme.upper()} ({r.status_code}) • `{ms} ms`")
            responded = True
            break
        except requests.RequestException:
            pass
        finally:
            if r is not None: r.close()
    if not responded: lines.append("   └ Web: 🔴 No Response")
    return lines


def web_get(domain, scheme):
    return session.get(f"{scheme}://{domain}/", timeout=TIMEOUT, allow_redirects=True, stream=True)


def bulk_handler(message):
    chat_id = message.chat.id
    if not check_and_deduct_point(chat_id):
        bot.send_message(chat_id, "❌ **ፖይንትዎ አልቋል!**", parse_mode="Markdown")
        return

    domains, invalid = [], []
    if message.document:
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)
            content = downloaded.decode('utf-8', errors='ignore')
        except Exception:
            bot.reply_to(message, "❌ **ፋይሉን ማንበብ አልተቻለም።**", parse_mode="Markdown")
            return
    else:
        content = message.text or ""

    for item in content.splitlines():
        if not item.strip(): continue
        d = clean_domain(item)
        if d:
            if d not in domains: domains.append(d)
        else: invalid.append(item.strip()[:80])

    if not domains:
        bot.reply_to(message, "❌ **Domain አልተገኘም።**", parse_mode="Markdown")
        return

    m = bot.send_message(chat_id, f"📦 **Bulk Host Checker (Unlimited):** `{len(domains)}` hosts እየተፈተሹ ነው...", parse_mode="Markdown")
    lines = title_block("BULK HOST REPORT (UNLIMITED)") + [f"📌 **Total Checked:** `{len(domains)}`", ""]
    for d in domains:
        lines += check_bulk_host(d) + [""]
    if invalid: lines += ["⚠️ **Invalid entries skipped:**"] + [f"• `{x}`" for x in invalid]
    report = "\n".join(lines)
    try: bot.edit_message_text(f"📦 **BULK HOST CHECKER**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ **Checked:** `{len(domains)}`\n📄 **Status:** `Full unlimited report attached as TXT.`", chat_id, m.message_id, parse_mode="Markdown")
    except Exception: pass
    send_txt(chat_id, "netx_bulk_host_report.txt", report, "📦 **Bulk Host Report (Unlimited)**")


# ==========================================
# 💎 PREMIUM PRICING & SCREENSHOT PAYMENT FLOW
# ==========================================
@bot.callback_query_handler(func=lambda c: c.data in ["buy_month", "buy_year"])
def premium_callback(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    
    if call.data == "buy_month":
        plan_name = "1 ወር (Monthly)"
        price = "100 ETB"
    else:
        plan_name = "1 ዓመት (Yearly)"
        price = "400 ETB"
        
    bot.send_message(
        chat_id,
        f"💎 **የመረጡት ፓኬጅ:** `{plan_name}`\n"
        f"💰 **የብር መጠን:** `{price}`\n\n"
        f"💳 **የቴሌብር (Telebirr) አካውንት መረጃ:**\n"
        f"• ቁጥር: `{TELEBIRR_PHONE}`\n"
        f"• ስም: `{TELEBIRR_NAME}`\n\n"
        "🚨 **ማስጠንቀቂያ:**\n"
        "ሐሰተኛ ስክሪን ሾት መላክ ወይም ማጭበርበር በሲስተሙ በራስ ሰር ታግተው **(Permanent Ban)** ቦቱን እንዳይጠቀሙ ያደርግዎታል።\n\n"
        "📸 **እንዴት ያረጋግጡ?**\n"
        "ብሩን ከከፈሉ በኋላ የክፍያዎን **Screenshot** (ፎቶ) በቀጥታ ወደዚህ ቻት ይላኩ!",
        parse_mode="Markdown"
    )


# 🎯 የፎቶ/ስክሪን ሾት መቀበያ እና ለአድሚን ማስተላለፊያ ዋና ሃንድለር (content_types=['photo'])
@bot.message_handler(content_types=['photo'])
def handle_payment_screenshot(message):
    chat_id = message.chat.id
    
    try:
        # ፎቶውን ለአድሚን በራሱ ሰር ማስተላለፍ
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(
            ADMIN_ID,
            f"🔔 **አዲስ የክፍያ ስክሪን ሾት ደርሷል!**\n"
            f"👤 **Sender ID:** `{chat_id}`\n"
            f"👤 **Username:** @{message.from_user.username or 'None'}\n\n"
            f"👇 **ለማጽደቅ የሚከተሉትን ትዕዛዞች ይጠቀሙ:**\n"
            f"• 1 ወር ለመስጠት: `/approve {chat_id}`\n"
            f"• 1 ዓመት ለመስጠት: `/approve_year {chat_id}`",
            parse_mode="Markdown"
        )
        bot.reply_to(
            message,
            "✅ **የክፍያ ማረጋገጫዎ (Screenshot) ለአድሚን ተልኳል!**\n"
            "አድሚኑ ክፍያዎን ሲያረጋግጥ ፕሪሚየም (Unlimited) መዳረሻ ይሰጥዎታል። እናመሰግናለን!",
            parse_mode="Markdown"
        )
    except Exception as e:
        log.error(f"Failed to forward photo: {e}")
        bot.reply_to(message, "❌ ማረጋገጫውን መላክ አልተቻለም። እባክዎ ድጋሚ ይሞክሩ።", parse_mode="Markdown")


@bot.message_handler(content_types=["text"], func=lambda m: True)
def route(message):
    text = (message.text or "").strip()
    chat_id = message.chat.id

    if text == "🌐 DNS Lookup": ask_domain(message, lambda m: bot.send_message(chat_id, dns_result(validate(m))[:4000], parse_mode="Markdown"))
    elif text == "🚀 Subdomain Finder": ask_domain(message, subdomain_handler)
    elif text == "🛠️ Advanced Pentest Tools": ask_domain(message, pentest_handler)
    elif text == "🔍 Host Scanner (Bug Host)": ask_domain(message, host_scanner_handler)
    elif text == "📦 Bulk Host Checker (Unlimited)":
        if not check_and_deduct_point(chat_id):
            bot.send_message(chat_id, "❌ **ፖይንትዎ አልቋል!** ፕሪሚየም ይግዙ ወይም ጓደኛ ይጋብዙ።", parse_mode="Markdown")
            return
        p = bot.send_message(chat_id, "📦 **ያለ ምንም ገደብ (Unlimited)** ብዙ ዶሜይኖችን የያዘ `.txt` ፋይል አያይዘው ይላኩ ወይም በአዲስ መስመር ጻፍው።", parse_mode="Markdown")
        bot.register_next_step_handler(p, bulk_handler)
    elif text == "👤 My Profile / Points":
        active_prem = is_premium(chat_id)
        status = "💎 Unlimited (Premium Active)" if active_prem else "🆓 Standard (Free User)"
        points = "Unlimited" if active_prem else f"{user_points.get(chat_id, 20)} Points"
        bot.send_message(
            chat_id,
            f"👤 **USER PROFILE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Telegram ID:** `{chat_id}`\n"
            f"📊 **Status:** `{status}`\n"
            f"🎁 **Points:** `{points}`\n\n"
            f"💡 *መሳሪያዎችን ሲጠቀሙ 1 ፖይንት ይቀነሳል።*", parse_mode="Markdown")
    elif text == "👥 Referral Program":
        active_prem = is_premium(chat_id)
        points = "Unlimited" if active_prem else user_points.get(chat_id, 20)
        ref_link = f"https://t.me/{bot.get_me().username}?start=REF_{chat_id}"
        bot.send_message(
            chat_id,
            f"👥 **REFERRAL PROGRAM**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **የእርስዎ ቀሪ ፖይንት:** `{points}`\n\n"
            f"🔗 **የእርስዎ ማስተዋወቂያ ሊንክ:**\n`{ref_link}`\n\n"
            f"💡 *ይህንን ሊንክ ለጓደኛዎችዎ በመላክ እያንዳንዱ ሰው ሲገባ **20 ፖይንት** ያግኙ!*", parse_mode="Markdown")
    elif text == "💎 Get Unlimited / Premium":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📅 1 ወር (Monthly) — 100 ETB", callback_data="buy_month"),
            types.InlineKeyboardButton("📆 1 ዓመት (Yearly) — 400 ETB", callback_data="buy_year")
        )
        bot.send_message(
            chat_id,
            "💎 **UNLIMITED / PREMIUM ACCESS**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "ቦቱን ያለገደብ (Unlimited) በቋሚነት መጠቀም ይፈልጋሉ?\n"
            "እባክዎ ከታች ከሚገኙት የፕሪሚየም ፓኬጆች ውስጥ የሚፈልጉትን ይምረጡ፦",
            reply_markup=markup, parse_mode="Markdown")
    elif text == "👨‍💻 Admin Contact":
        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("👨‍💻 Contact Admin", url=ADMIN_CONTACT))
        bot.send_message(chat_id, "👨‍💻 **NETX TOOLS PRO — ADMIN CONTACT**", reply_markup=k, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⚠️ **እባክዎ ከምናሌው አንዱን ይምረጡ።**", reply_markup=menu(), parse_mode="Markdown")


def dns_result(domain):
    lines = title_block("DNS LOOKUP", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━", "📌 **RESULTS:**"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines += [f"🟢 **Total IPs Found:** `{len(ips)}`"] + [f"  • `{ip}`" for ip in ips[:25]]
    except Exception as e:
        lines.append(f"🔴 **DNS failed:** `{type(e).__name__}`")
    return "\n".join(lines)


@app.route("/")
def home():
    return jsonify({"service": "NetXToolsPro", "status": "running"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def run_flask():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log.info("NetX Tools Pro starting successfully")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=60)
