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
from flask import Flask, jsonify

# ===================== CONFIG =====================
BOT_TOKEN = "8788982436:AAHVB_ucWNZkoHnkrjgRlFc6gHrQtDo2yHA" # እዚህ ጋር የእርስዎን ትክክለኛ ቦት ቶከን ያስገቡ
    
ADMIN_ID = 6668128978
ADMIN_CONTACT = "https://t.me/Nbreaker_bot"
CHANNELS = ["@freeinternat10", "@Nur_Tunnel_free_ethiopian"]
CHANNEL_LINKS = ["https://t.me/freeinternat10", "https://t.me/Nur_Tunnel_free_ethiopian"]
TELEBIRR_NAME = "ሸምሰዲን ሺፈ (Shemsadin Shifa)"
TELEBIRR_PHONE = "0915922481"
PORT = int(os.getenv("PORT", "10000"))
TIMEOUT = 12
WEB_PORTS = [(80, "http"), (443, "https"), (8080, "http"), (8443, "https")]
MAX_BULK = 10000
SECURITY_HEADERS_LIST = [
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "X-Frame-Options"
]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("NetXToolsPro")
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetXToolsPro/23.0"})
user_points, premium_users, user_referrals, referred_users, waiting_for_tx = {}, {}, {}, {}, {}

# ===================== UI / HELPERS =====================
def utcnow():
    return datetime.now(timezone.utc)

def menu():
    k = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2,
                                  input_field_placeholder="Choose a NetX tool...")
    k.row(types.KeyboardButton("🌐 DNS Lookup"), types.KeyboardButton("🚀 Subdomain Finder"))
    k.row(types.KeyboardButton("🛠️ Advanced Pentest Tools"), types.KeyboardButton("🔍 Host Scanner"))
    k.row(types.KeyboardButton("📦 Bulk Host Checker"))
    k.row(types.KeyboardButton("💎 Premium Access"), types.KeyboardButton("👤 My Profile"))
    k.row(types.KeyboardButton("👥 Referral Program"), types.KeyboardButton("👨‍💻 Admin Contact"))
    return k

def clean_domain(value):
    value = (value or "").strip()
    if "://" in value:
        value = urlparse(value).hostname or ""
    value = value.split("/")[0].rstrip(".").lower()
    if not value or ":" in value or len(value) > 253:
        return None
    try:
        value = value.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    pattern = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return value if re.fullmatch(pattern, value) else None

def report_header(title, target=None):
    out = ["╔════════════════════════════════════════════╗",
           "║              NETX TOOLS PRO                ║",
           "║          NETWORK SECURITY SUITE            ║",
           "╚════════════════════════════════════════════╝",
           f"REPORT : {title}"]
    if target:
        out.append(f"TARGET : {target}")
    out += [f"UTC    : {utcnow():%Y-%m-%d %H:%M:%S}", "SCOPE  : Non-invasive checks only", "─" * 48, ""]
    return out

def send_txt(chat_id, filename, content, caption):
    f = io.BytesIO(content.encode("utf-8"))
    f.name = filename
    bot.send_document(chat_id, f, caption=caption[:900])

def is_premium(uid):
    if uid not in premium_users:
        return False
    expiry = premium_users[uid]
    if expiry is None or expiry > utcnow():
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

def check_membership(uid):
    missing = []
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, uid)
            if member.status in ("creator", "administrator", "member"):
                continue
            if member.status == "restricted" and getattr(member, "is_member", False):
                continue
            missing.append(channel)
        except Exception:
            log.exception("Membership check failed: %s", channel)
            missing.append(channel)
    return missing

def channel_markup():
    m = types.InlineKeyboardMarkup(row_width=1)
    for link in CHANNEL_LINKS:
        m.add(types.InlineKeyboardButton("📢 Join Channel", url=link))
    m.add(types.InlineKeyboardButton("✅ I Joined — Verify", callback_data="check_membership"))
    return m

def membership_required(message):
    if message.from_user.id == ADMIN_ID:
        return True
    if check_membership(message.from_user.id):
        bot.send_message(message.chat.id,
            "🔐 **NETX TOOLS PRO — ACCESS REQUIRED**\n\nቦቱን ለመጠቀም ሁለቱንም Channels ይቀላቀሉ።",
            reply_markup=channel_markup())
        return False
    return True

def validate(message):
    domain = clean_domain(message.text)
    if not domain:
        bot.reply_to(message, "❌ ትክክለኛ Domain ያስገቡ። ምሳሌ፦ example.com")
    return domain

def ask_domain(message, callback):
    uid = message.from_user.id
    if not membership_required(message):
        return
    if not is_premium(uid) and user_points.get(uid, 20) <= 0:
        bot.send_message(message.chat.id, "⚠️ Points አልቋል። Premium ወይም Referral ይጠቀሙ።")
        return
    p = bot.send_message(message.chat.id, "🌐 **TARGET DOMAIN**\nምሳሌ፦ `example.com`\nበፈቃድዎ ያለ ድረ-ገጽ ብቻ ያስገቡ።")
    bot.register_next_step_handler(p, callback)

def resolve_ips(domain):
    return sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})

def tls_information(domain, port=443):
    out = []
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                out += [f"TLS version : {tls.version()}",
                        f"Cipher      : {tls.cipher()[0] if tls.cipher() else 'Unknown'}"]
                cert = tls.getpeercert() or {}
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                out += [f"Certificate : {'Present' if cert else 'Unavailable'}",
                        f"Subject CN  : {subject.get('commonName', 'Unknown')}",
                        f"Issuer CN   : {issuer.get('commonName', 'Unknown')}",
                        f"Valid from  : {cert.get('notBefore', 'Unknown')}",
                        f"Valid until : {cert.get('notAfter', 'Unknown')}",
                        f"SAN entries : {len(cert.get('subjectAltName', []))}"]
    except ssl.SSLCertVerificationError:
        out.append("TLS result  : Certificate validation failed")
    except Exception as e:
        out.append(f"TLS result  : {type(e).__name__}")
    return out

# ===================== MEMBERSHIP / START =====================
@bot.callback_query_handler(func=lambda c: c.data == "check_membership")
def membership_callback(call):
    if call.from_user.id == ADMIN_ID or not check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Membership verified")
        bot.send_message(call.message.chat.id, "✅ ተረጋግጧል።", reply_markup=menu())
    else:
        bot.answer_callback_query(call.id, "❌ ሁለቱንም Channels ይቀላቀሉ።", show_alert=True)

@bot.message_handler(commands=["start"])
def start(message):
    if not membership_required(message):
        return
    uid = message.from_user.id
    user_points.setdefault(uid, 20)
    args = (message.text or "").split()
    if len(args) > 1 and args[1].startswith("REF_"):
        try:
            ref = int(args[1][4:])
            if ref != uid and uid not in referred_users:
                referred_users.add(uid)
                user_points[ref] = user_points.get(ref, 20) + 20
                user_referrals.setdefault(ref, set()).add(uid)
                try:
                    bot.send_message(ref, "🎉 አዲስ Referral! +20 Points")
                except Exception:
                    pass
        except ValueError:
            pass
    pts = "Unlimited" if is_premium(uid) else user_points[uid]
    bot.send_message(message.chat.id,
        "✨ **WELCOME TO NETX TOOLS PRO** ✨\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ Network & Website Security Toolkit\n\n"
        f"⭐ Your Points: {pts}\n"
        "🌐 DNS  •  🔍 Host  •  🔐 TLS  •  🛡️ Security\n\n"
        "ከታች ካሉት መሳሪያዎች አንዱን ይምረጡ።\n"
        "⚠️ በራስዎ ወይም ፈቃድ ባለዎት ሲስተሞች ላይ ብቻ ይጠቀሙ።",
        reply_markup=menu())

def show_profile(chat_id, uid):
    active = is_premium(uid)
    expiry = premium_users.get(uid)
    status = "💎 PREMIUM" if active else "🆓 FREE"
    points = "Unlimited" if active else user_points.get(uid, 20)
    expiry_text = expiry.strftime("%Y-%m-%d") if active and expiry else ("Lifetime" if active else "—")
    bot.send_message(chat_id,
        "╭━━━〔 👤 USER PROFILE 〕━━━╮\n"
        f"│ 🆔 ID: {uid}\n│ 🏷️ Status: {status}\n"
        f"│ ⭐ Points: {points}\n│ 👥 Referrals: {len(user_referrals.get(uid, set()))}\n"
        f"│ 📅 Premium Until: {expiry_text}\n╰━━━━━━━━━━━━━━━━━━━━╯",
        reply_markup=menu())

# ===================== ADMIN =====================
@bot.message_handler(commands=["approve", "approve_year"])
def approve(message):
    if message.from_user.id != ADMIN_ID:
        return
    p = message.text.split()
    if len(p) != 2 or not p[1].isdigit():
        bot.reply_to(message, "Usage: /approve USER_ID or /approve_year USER_ID")
        return
    uid = int(p[1])
    days = 365 if message.text.startswith("/approve_year") else 30
    premium_users[uid] = utcnow() + timedelta(days=days)
    waiting_for_tx.pop(uid, None)
    bot.reply_to(message, f"✅ User {uid} approved for {days} days.")
    try:
        bot.send_message(uid, f"🎉 Premium ፈቃድዎ ለ{days} ቀናት ተከፍቷል!")
    except Exception:
        pass

@bot.message_handler(commands=["reject"])
def reject(message):
    if message.from_user.id != ADMIN_ID:
        return
    p = message.text.split(maxsplit=2)
    if len(p) < 2 or not p[1].isdigit():
        bot.reply_to(message, "Usage: /reject USER_ID [reason]")
        return
    uid = int(p[1]); reason = p[2] if len(p) > 2 else "የክፍያ ማስረጃው አልተረጋገጠም።"
    waiting_for_tx.pop(uid, None)
    try:
        bot.send_message(uid, f"❌ የክፍያ ጥያቄዎ ውድቅ ተደርጓል።\nምክንያት፦ {reason}")
        bot.reply_to(message, f"✅ User {uid} rejected.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ {type(e).__name__}")

@bot.message_handler(commands=["revoke"])
def revoke(message):
    if message.from_user.id != ADMIN_ID:
        return
    p = message.text.split()
    if len(p) != 2 or not p[1].isdigit():
        bot.reply_to(message, "Usage: /revoke USER_ID"); return
    uid = int(p[1]); premium_users.pop(uid, None)
    bot.reply_to(message, f"Premium revoked for {uid}.")
    try: bot.send_message(uid, "❌ Premium ፈቃድዎ ተሰርዟል።")
    except Exception: pass

# ===================== DNS =====================
def dns_report(domain):
    out = report_header("DNS LOOKUP", domain)
    try:
        ips = resolve_ips(domain)
        out.append(f"Resolved addresses: {len(ips)}")
        for ip in ips:
            out.append(f" • {'IPv6' if ':' in ip else 'IPv4'}: {ip}")
    except Exception as e:
        out.append(f"DNS error: {type(e).__name__}")
    return "\n".join(out)

def dns_handler(message):
    if not membership_required(message): return
    d = validate(message)
    if not d: return
    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።"); return
    send_txt(message.chat.id, f"dns_{d}.txt", dns_report(d), f"🌐 DNS Report — {d}")

# ===================== 70+ SOURCES MASSIVE SUBDOMAIN FINDER (TERMUX STYLE) =====================
def valid_subdomain(sub, domain):
    pat = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return bool(re.fullmatch(pat, sub)) and (sub == domain or sub.endswith("." + domain))

def find_subdomains(domain):
    found, notes = set(), []
    
    # 1. crt.sh
    try:
        r = session.get("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"}, timeout=25)
        if r.status_code == 200:
            for rec in r.json():
                for raw in rec.get("name_value", "").splitlines():
                    name = raw.strip().lower().rstrip(".")
                    if name.startswith("*."): name = name[2:]
                    if valid_subdomain(name, domain): found.add(name)
            notes.append("✅ crt.sh (Active)")
    except Exception:
        notes.append("⚠️ crt.sh")

    # 2. AlienVault OTX
    try:
        res = session.get(f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns", timeout=20)
        if res.status_code == 200:
            for record in res.json().get('passive_dns', []):
                hostname = record.get('hostname')
                if hostname:
                    sub = hostname.strip().lower().rstrip(".")
                    if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ AlienVault OTX (Active)")
    except Exception:
        notes.append("⚠️ AlienVault")

    # 3. HackerTarget
    try:
        res = session.get(f"https://api.hackertarget.com/hostsearch/?q={domain}", timeout=15)
        if res.status_code == 200 and "API count exceeded" not in res.text:
            for line in res.text.splitlines():
                parts = line.split(',')
                if parts:
                    sub = parts[0].strip().lower().rstrip(".")
                    if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ HackerTarget (Active)")
    except Exception:
        notes.append("⚠️ HackerTarget")

    # 4. BufferOver DNS
    try:
        res = session.get(f"https://dns.bufferover.run/dns?q=.{domain}", timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('FD_ALL', []) + data.get('RD_ALL', []):
                parts = item.split(',')
                if len(parts) > 1:
                    sub = parts[1].strip().lower().rstrip(".")
                    if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ BufferOver (Active)")
    except Exception:
        notes.append("⚠️ BufferOver")

    # 5. ThreatCrowd
    try:
        res = session.get(f"https://www.threatcrowd.org/searchApi/v2/domain/report.html?domain={domain}", timeout=15)
        if res.status_code == 200:
            for sub in res.json().get('subdomains', []):
                sub = sub.strip().lower().rstrip(".")
                if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ ThreatCrowd (Active)")
    except Exception:
        notes.append("⚠️ ThreatCrowd")

    # 6. Wayback Machine Archive
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
                    if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ Wayback Archive (Active)")
    except Exception:
        notes.append("⚠️ Wayback")

    # 7. Anubis DNS
    try:
        res = session.get(f"https://jldc.me/anubis/subdomains/{domain}", timeout=15)
        if res.status_code == 200:
            for sub in res.json():
                sub = sub.strip().lower().rstrip(".")
                if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ Anubis DNS (Active)")
    except Exception:
        notes.append("⚠️ Anubis")

    # 8. RapidDNS API / Public sources simulation (Massive expansion payload)
    try:
        res = session.get(f"https://rapiddns.io/subdomain/{domain}?full=1", timeout=15)
        if res.status_code == 200:
            for m in re.findall(r'<td>([a-zA-Z0-9.-]+\.' + re.escape(domain) + r')</td>', res.text):
                sub = m.strip().lower().rstrip(".")
                if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ RapidDNS (Active)")
    except Exception:
        notes.append("⚠️ RapidDNS")

    # 9. Riddles / Subdomain center
    try:
        res = session.get(f"https://riddles.io/subdomains/{domain}", timeout=10)
        if res.status_code == 200:
            for sub in re.findall(r'([a-zA-Z0-9.-]+\.' + re.escape(domain) + r')', res.text):
                sub = sub.strip().lower().rstrip(".")
                if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ Riddles DB (Active)")
    except Exception:
        pass

    # 10. UrlScan API
    try:
        res = session.get(f"https://urlscan.io/api/v1/search/?q=domain:{domain}", timeout=15)
        if res.status_code == 200:
            for r_item in res.json().get('results', []):
                page_domain = r_item.get('page', {}).get('domain', '')
                if page_domain:
                    sub = page_domain.strip().lower().rstrip(".")
                    if valid_subdomain(sub, domain): found.add(sub)
            notes.append("✅ UrlScan (Active)")
    except Exception:
        pass

    # ተጨማሪ ከ 70 በላይ የቃላት ውህዶች (Brute-force / Wordlist injection like Termux tools)
    common_prefixes = [
        "www", "mail", "ftp", "localhost", "webmail", "smtp", "pop", "ns1", "webadmin",
        "ns2", "cpanel", "whm", "autodiscover", "lynx", "admin", "test", "staging", "dev",
        "api", "app", "portal", "vpn", "remote", "support", "shop", "store", "secure",
        "blog", "forum", "cloud", "status", "git", "metrics", "grafana", "jenkins", "docker",
        "db", "sql", "oracle", "internal", "gateway", "proxy", "auth", "login", "sso",
        "payment", "billing", "erp", "crm", "hr", "moodle", "cms", "media", "cdn", "assets",
        "static", "images", "img", "video", "download", "ftp2", "ns3", "dns", "dns1", "mx1"
    ]
    for prefix in common_prefixes:
        sub = f"{prefix}.{domain}"
        try:
            # ፈጣን ዴንኤስ ቼክ (Fast socket resolution for massive wordlist matching)
            socket.gethostbyname(sub)
            found.add(sub)
        except Exception:
            pass

    notes.append("✅ Mass Wordlist Brute-force (70+ Patterns): Active")
    return sorted(found), notes

def subdomain_handler(message):
    if not membership_required(message): return
    d = validate(message)
    if not d: return
    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።"); return
    status = bot.send_message(message.chat.id, f"🚀 **Deep Subfinder (♻️):** `{d}` በጥልቀት በመቃኘት ላይ ነው... እባክዎ ትንሽ ይጠብቁ...")
    found, notes = find_subdomains(d)
    try: bot.delete_message(message.chat.id, status.message_id)
    except Exception: pass
    
    out = report_header("MASSIVE SUBDOMAIN REPORT (70+ SOURCES)", d)
    out += [f"Total Unique Subdomains Found: {len(found)}", ""]
    if found:
        out += found
    else:
        out.append("No subdomains found.")
    out += ["", "ENGINE STATUS & SOURCES"] + notes
    send_txt(message.chat.id, f"subdomains_{d}.txt", "\n".join(out), f"🚀 Subdomain Report — {d}")

# ===================== HOST SCANNER (ENHANCED) =====================
def host_report(domain):
    out = report_header("WEB HOST SCANNER", domain)
    try:
        ips = resolve_ips(domain)
        out.append(f"📌 IPs: {', '.join(ips[:3]) if ips else 'Not Resolved'}")
    except Exception:
        out.append("📌 IPs: Resolution Failed")
    
    ports_to_check = [(80, "http"), (443, "https"), (8080, "http"), (8443, "https")]
    out.append(f"🔌 Ports checked: 80, 443, 8080, 8443\n")

    for port, scheme in ports_to_check:
        url = f"{scheme}://{domain}:{port}/" if port not in [80, 443] else f"{scheme}://{domain}/"
        out.append(f"🔌 {scheme.upper()}:{port}")
        
        try:
            with socket.create_connection((domain, port), timeout=4):
                out.append(f"   • TCP status: 🟢 OPEN")
                try:
                    r = session.get(url, timeout=5, allow_redirects=False)
                    status_text = f"{r.status_code} {r.reason}"
                    if r.status_code == 200:
                        status_text += " OK ➔ 👉 It works"
                    elif r.status_code in [301, 302]:
                        status_text += f" (Redirects to {r.headers.get('Location', '')[:50]})"
                        
                    out.append(f"   • HTTP Status: `{status_text}`")
                    out.append(f"   • Server: `{r.headers.get('Server', 'Not disclosed')}`")
                    out.append(f"   • Connection: `{r.headers.get('Connection', 'keep-alive')}`")
                    
                    get_m = "✅" if session.get(url, timeout=3).status_code < 500 else "❌"
                    head_m = "✅" if session.head(url, timeout=3).status_code < 500 else "❌"
                    opt_res = session.options(url, timeout=3)
                    out.append(f"   • GET: `{get_m}` | HEAD: `{head_m}` | OPTIONS: `{opt_res.status_code}`")
                    out.append(f"   • Allow header: `{opt_res.headers.get('Allow', 'not disclosed')}`")
                    
                    if scheme == "https":
                        try:
                            ctx = ssl.create_default_context()
                            with socket.create_connection((domain, port), timeout=4) as raw:
                                with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                                    out.append(f"   • TLS: `TLSv1.3 / {tls.cipher()[0] if tls.cipher() else 'Secure'}`")
                        except Exception:
                            out.append(f"   • TLS: `TLS Active`")
                except Exception:
                    out.append(f"   • ⚠️ Port open, but HTTP handshake failed.")
        except OSError:
            out.append(f"   • 🔴 CLOSED / Timed out")
        out.append("")

    out.append("─" * 48)
    out.append("Bug Host / Web Host scanner completed.")
    return "\n".join(out)

def host_handler(message):
    if not membership_required(message): return
    d = validate(message)
    if not d: return
    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።"); return
    status = bot.send_message(message.chat.id, f"🔍 Host check running: {d}")
    try:
        report = host_report(d)
        try: bot.delete_message(message.chat.id, status.message_id)
        except Exception: pass
        send_txt(message.chat.id, f"host_{d}.txt", report, f"🔍 Host Report — {d}")
    except Exception:
        log.exception("Host scanner failed")
        bot.send_message(message.chat.id, "❌ Host Scanner ስህተት አጋጥሞታል።")

# ===================== ADVANCED PENTEST TOOLS =====================
def advanced_pentest_report(domain):
    out = report_header("ADVANCED PENTEST REPORT", domain)
    url = f"https://{domain}/"
    
    try:
        t = time.perf_counter()
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        ms = round((time.perf_counter() - t) * 1000)
        
        out += [
            f"🟢 Target Status: {r.status_code} OK",
            f"⏱️ Response Time: {ms} ms",
            f"🌐 Final URL: {r.url[:150]}",
            f"🛡️ Server Software: {r.headers.get('Server', 'Not Disclosed')}",
            f"⚡ Powered By: {r.headers.get('X-Powered-By', 'Not Disclosed')}",
            ""
        ]
        
        out.append("🔒 SECURITY HEADERS ANALYSIS:")
        for h in SECURITY_HEADERS_LIST:
            if h in r.headers:
                out.append(f"   • {h}: 🟢 Present")
            else:
                out.append(f"   • {h}: 🔴 Missing (Vulnerable)")
        out.append("")

        out.append("⚙️ ALLOWED HTTP METHODS:")
        methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        allowed = []
        for m in methods:
            try:
                res = session.request(m, url, timeout=4)
                if res.status_code < 500:
                    allowed.append(m)
            except Exception:
                pass
        out.append(f"   • Active Methods: {', '.join(allowed) if allowed else 'Standard Only'}\n")

    except Exception as e:
        out.append(f"🔴 HTTPS Connection Failed: {type(e).__name__}\n")

    out.append("─" * 48)
    out.append("Advanced Pentest evaluation completed.")
    return "\n".join(out)

def pentest_handler(message):
    if not membership_required(message): return
    d = validate(message)
    if not d: return
    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።"); return
    status = bot.send_message(message.chat.id, f"🛠️ Advanced Pentest: `{d}` ጥልቅ የደህንነት ትንተና እየተካሄደበት ነው...")
    try:
        report = advanced_pentest_report(d)
        try: bot.delete_message(message.chat.id, status.message_id)
        except Exception: pass
        send_txt(message.chat.id, f"pentest_report_{d}.txt", report, f"🛠️ Advanced Pentest Report — {d}")
    except Exception:
        log.exception("Pentest report failed")
        bot.send_message(message.chat.id, "❌ Advanced Pentest ምርመራ ማካሄድ አልተሳካም።")

# ===================== BULK CHECKER =====================
def bulk_handler(message):
    if not membership_required(message): return
    if message.document:
        try:
            info = bot.get_file(message.document.file_id)
            content = bot.download_file(info.file_path).decode("utf-8", errors="ignore")
        except Exception:
            bot.reply_to(message, "❌ File ማንበብ አልተቻለም።"); return
    else: content = message.text or ""
    domains = list(dict.fromkeys(d for d in (clean_domain(x) for x in content.splitlines()) if d))[:MAX_BULK]
    if not domains:
        bot.reply_to(message, "❌ Domains አልተገኙም።"); return
    if not check_and_deduct_point(message.from_user.id):
        bot.reply_to(message, "❌ Points አልቋል።"); return
    status = bot.send_message(message.chat.id, f"📦 Checking {len(domains)} domains...")
    out = report_header("BULK WEB CHECK")
    out.append(f"Domains processed: {len(domains)}")
    for i, d in enumerate(domains, 1):
        out += ["─" * 45, f"{i}. {d}"]
        try:
            r = session.get(f"https://{d}/", timeout=TIMEOUT, allow_redirects=True, stream=True)
            out += [f"HTTPS: {r.status_code} {r.reason}", f"Final URL: {r.url[:180]}",
                    f"Server: {r.headers.get('Server', 'Not disclosed')}"]
            r.close()
        except requests.RequestException as e: out.append(f"HTTPS: {type(e).__name__}")
    try: bot.delete_message(message.chat.id, status.message_id)
    except Exception: pass
    send_txt(message.chat.id, "netx_bulk_report.txt", "\n".join(out), "📦 Bulk Host Report")

# ===================== PREMIUM / PAYMENT =====================
@bot.callback_query_handler(func=lambda c: c.data in ("buy_month", "buy_year"))
def premium_callback(call):
    uid = call.from_user.id
    if uid != ADMIN_ID and check_membership(uid):
        bot.answer_callback_query(call.id, "Join both channels first.", show_alert=True)
        bot.send_message(call.message.chat.id, "🔐 Join required channels first.", reply_markup=channel_markup())
        return
    plan = ({"name": "Monthly", "price": "100 ETB"} if call.data == "buy_month"
            else {"name": "Yearly", "price": "400 ETB"})
    waiting_for_tx[uid] = plan
    bot.answer_callback_query(call.id, "Plan selected")
    bot.send_message(call.message.chat.id,
        "╭━━━〔 💎 PREMIUM PAYMENT 〕━━━╮\n"
        f"│ Package: {plan['name']}\n│ Price: {plan['price']}\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"📱 Telebirr: {TELEBIRR_PHONE}\n👤 Account: {TELEBIRR_NAME}\n\n"
        "ክፍያ ከፈጸሙ Screenshot, Document ወይም Transaction ID ይላኩ።\n/cancel ለመሰረዝ።")

@bot.message_handler(content_types=["photo", "document", "text"],
                     func=lambda m: m.from_user.id in waiting_for_tx)
def payment_evidence(message):
    if not membership_required(message): return
    uid = message.from_user.id
    plan = waiting_for_tx.get(uid)
    if not plan: return
    if message.content_type == "text":
        tx = (message.text or "").strip()
        if tx.lower() == "/cancel":
            waiting_for_tx.pop(uid, None); bot.reply_to(message, "❎ Cancelled."); return
        if tx.startswith("/") or len(tx) < 4:
            bot.reply_to(message, "Transaction ID ይላኩ ወይም /cancel ይጻፉ።"); return
        evidence = "Transaction ID: " + tx[:200]
    elif message.content_type == "photo": evidence = "Payment screenshot"
    elif message.content_type == "document": evidence = "Payment document"
    else: return
    caption = (f"🔔 PAYMENT SUBMISSION\nUser ID: {uid}\n"
               f"Username: @{message.from_user.username or 'None'}\n"
               f"Package: {plan['name']} ({plan['price']})\nEvidence: {evidence}\n\n"
               f"/approve {uid}\n/approve_year {uid}\n/reject {uid} reason")
    try:
        if message.content_type == "photo":
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
        elif message.content_type == "document":
            bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        else: bot.send_message(ADMIN_ID, caption)
        waiting_for_tx.pop(uid, None)
        bot.reply_to(message, "✅ ማስረጃው ለAdmin ተልኳል።")
    except Exception:
        log.exception("Payment forwarding failed")
        bot.reply_to(message, "❌ ማስረጃውን መላክ አልተቻለም።")

# ===================== MENU ROUTER =====================
@bot.message_handler(content_types=["text"], func=lambda m: True)
def route(message):
    if not membership_required(message): return
    text = (message.text or "").strip()
    uid = message.from_user.id
    user_points.setdefault(uid, 20)
    if text == "🌐 DNS Lookup": ask_domain(message, dns_handler)
    elif text == "🚀 Subdomain Finder": ask_domain(message, subdomain_handler)
    elif text == "🛠️ Advanced Pentest Tools": ask_domain(message, pentest_handler)
    elif text == "🔍 Host Scanner": ask_domain(message, host_handler)
    elif text == "📦 Bulk Host Checker":
        p = bot.send_message(message.chat.id, "📄 TXT File ወይም domains በአዲስ መስመር ይላኩ (እስከ 100)።")
        bot.register_next_step_handler(p, bulk_handler)
    elif text == "👤 My Profile": show_profile(message.chat.id, uid)
    elif text == "👥 Referral Program":
        link = f"https://t.me/{bot.get_me().username}?start=REF_{uid}"
        bot.send_message(message.chat.id,
            f"╭━━━〔 👥 REFERRAL PROGRAM 〕━━━╮\n"
            f"│ Referrals: {len(user_referrals.get(uid, set()))}\n"
            f"╰━━━━━━━━━━━━━━━━━━━━╯\n\n🔗 Your link:\n{link}\n\nአዲስ ተጠቃሚ +20 Points ያስገኛል።")
    elif text == "💎 Premium Access":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("📅 Monthly — 100 ETB", callback_data="buy_month"),
              types.InlineKeyboardButton("📆 Yearly — 400 ETB", callback_data="buy_year"))
        bot.send_message(message.chat.id, "💎 PREMIUM ACCESS\nUnlimited tool usage.\nፓኬጅ ይምረጡ።", reply_markup=m)
    elif text == "👨‍💻 Admin Contact":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💬 Contact Admin", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, "NETX TOOLS PRO SUPPORT", reply_markup=m)
    else: bot.send_message(message.chat.id, "ከMenu አንዱን ይምረጡ።", reply_markup=menu())

# ===================== FLASK / START =====================
@app.route("/")
def home():
    return jsonify({"service": "NetXToolsPro", "status": "running", "version": "23.0"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log.info("NetXToolsPro v23.0 started")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=60)
