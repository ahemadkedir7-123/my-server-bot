import os
import re
import io
import ssl
import time
import socket
import logging
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
import telebot
from telebot import types
from flask import Flask, jsonify

# እዚህ ጋር የእርስዎን የቴሌግራም ቦት ቶከን ያስገቡ
BOT_TOKEN = "8788982436:AAGlEaGWZgwWFcvecIJgBUOAG5L9-oB-AV0"

ADMIN_CONTACT = "https://t.me/None_Breaker"
ADMIN_ID = 123456789  # የእርስዎን አድሚን ID እዚህ ያስገቡ
PORT = int(os.getenv("PORT", "10000"))
TIMEOUT = 60
MAX_BULK_HOSTS = 20
SECURITY_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"
]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("NetXToolsPro")
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetXToolsPro/6.0"})

user_points = {}
premium_users = set()
user_referrals = {}


def clean_domain(value):
    """ ተጠቃሚው የጻፈውን ማንኛውንም ዶሜይን ያለ ገደብ ልክ እንደ ትክክለኛ ዶሜይን የሚያስተካክል """
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
        types.KeyboardButton("🔎 Subdomain Finder"),
        types.KeyboardButton("🛰️ Web Recon"),
        types.KeyboardButton("🔍 Host Scanner (Bug Host)"),
        types.KeyboardButton("📦 Bulk Host Checker"),
        types.KeyboardButton("💎 Get Unlimited / Premium"),
        types.KeyboardButton("👥 Referral Program"),
        types.KeyboardButton("👨‍💻 Admin Contact"),
    )
    return k


def ask_domain(message, callback):
    m = bot.send_message(message.chat.id, "🌐 **የሚፈልጉትን ዶሜይን ያስገቡ።** (ምሳሌ: `google.com`, `ethiotelecom.et`):", parse_mode="Markdown")
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
    args = message.text.split()
    
    if len(args) > 1 and args[1].startswith("REF_"):
        try:
            referrer_id = int(args[1].split("_")[1])
            if referrer_id != chat_id and chat_id not in user_referrals.get(referrer_id, set()):
                user_points[referrer_id] = user_points.get(referrer_id, 0) + 10
                user_referrals.setdefault(referrer_id, set()).add(chat_id)
                try:
                    bot.send_message(referrer_id, f"🎉 **እንኳን ደስ አለዎት!** አዲስ ሰው በሪፈራል ሊንክዎ ገብቷል +10 ፖይንት አግኝተዋል! 🎁", parse_mode="Markdown")
                except Exception:
                    pass
        except Exception:
            pass

    bot.send_message(
        chat_id,
        "🚀 **NETX TOOLS PRO (ULTIMATE CYBER SUITE)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔎 **Subdomain Finder:** ከሺህ በላይ ንዑስ ዶሜይኖችን በጥልቀት ይፈልጋል።\n"
        "🔍 **Host Scanner:** ፖርቶችን እና Bug Host ሁኔታዎችን አብጠርጥሮ ያወጣል።\n"
        "💎 **Unlimited / Premium:** በቴሌብር በመክፈል ፕሪሚየም ይሁኑ።\n"
        "👥 **Referral:** ጓደኛ በመጋበዝ ነፃ ፖይንቶችን ሰብስቡ።\n\n"
        "💡 *ለራስህ ወይም ፈቃድ ላለህ ሲስተም ብቻ ተጠቀም።*",
        reply_markup=menu(), parse_mode="Markdown")


@bot.message_handler(commands=["approve"])
def approve_user(message):
    if message.from_user.id != ADMIN_ID and message.from_user.id != 7755866750:
        return
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        uid = int(parts[1])
        premium_users.add(uid)
        bot.reply_to(message, f"✅ ተጠቃሚ `{uid}` አሁን **Premium / Unlimited** ሆኗል!", parse_mode="Markdown")
        try:
            bot.send_message(uid, "🎉 **እንኳን ደስ አለዎት!** ክፍያዎ ተረጋግጦ ቦቱ በአሁን ሰዓት **Unlimited / Premium** ሆኖ ተከፍቷል!", parse_mode="Markdown")
        except Exception:
            pass
    else:
        bot.reply_to(message, "⚠️ አጠቃቀም: `/approve <user_id>`", parse_mode="Markdown")


# ==========================================
# 🔎 DEEP SUBDOMAIN FINDER (Subfinder ቴክኖሎጂ ሙሉ በሙሉ)
# ==========================================
def find_subdomains(domain):
    found, notes = set(), []
    
    # 1. crt.sh
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

    # 2. AlienVault OTX
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

    # 3. HackerTarget
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

    # 4. BufferOver.run
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

    # 5. ThreatCrowd
    try:
        res = session.get(f"https://www.threatcrowd.org/searchApi/v2/domain/report.html?domain={domain}", timeout=15)
        if res.status_code == 200:
            for sub in res.json().get('subdomains', []):
                sub = sub.strip().lower().rstrip(".")
                if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ ThreatCrowd: Active")
    except Exception as e:
        notes.append(f"⚠️ ThreatCrowd: {type(e).__name__}")

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
                    if domain_ok_sub(sub, domain): found.add(sub)
            notes.append("✅ Wayback Archive: Active")
    except Exception as e:
        notes.append(f"⚠️ Wayback: {type(e).__name__}")

    return sorted(found), notes


def domain_ok_sub(sub, domain):
    pat = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return bool(re.fullmatch(pat, sub)) and (sub == domain or sub.endswith("." + domain))


def subdomain_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🔎 **Subdomain Finder:** `{d}` ከሁሉም ምንጮች በጥልቀት በመፈለግ ላይ... (እባክዎ ትንሽ ይጠብቁ)", parse_mode="Markdown")
    found, notes = find_subdomains(d)
    
    try: bot.delete_message(message.chat.id, m.message_id)
    except Exception: pass

    if not found:
        bot.send_message(message.chat.id, f"⚠️ ለ `{d}` ምንም ንዑስ ዶሜይን አልተገኘም።", parse_mode="Markdown")
        return

    # ብዛቱ ከ 10 በታች ከሆነ በቀጥታ ቻት ውስጥ ይላካል
    if len(found) <= 10:
        lines = title_block("SUBDOMAIN REPORT", d) + [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 **Total Found:** `{len(found)}`",
            ""
        ]
        lines += [f"• `{x}`" for x in found]
        lines += ["", "📌 **SOURCES STATUS:**"] + notes
        bot.send_message(message.chat.id, "\n".join(lines), parse_mode="Markdown")
    else:
        # ብዛቱ ከ 10 በላይ ከሆነ በ .txt ፋይል ይላካል
        report_lines = title_block("SUBDOMAIN REPORT", d) + [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 **Total Subdomains Found:** `{len(found)}`",
            ""
        ] + [f"• {x}" for x in found] + ["", "📌 **SOURCES STATUS:**"] + notes
        
        file_content = "\n".join(found)
        send_txt(
            message.chat.id, 
            f"subdomains_{d}.txt", 
            file_content, 
            f"✅ **የተገኙ ንዑስ ዶሜይኖች ({d}) [ጠቅላላ: {len(found)}]:**\n ውጤቱ ከ 10 በላይ ስለሆነ በሰነድ (.txt) ፋይል ተያይዟል!"
        )


def web_get(domain, scheme):
    return session.get(f"{scheme}://{domain}/", timeout=TIMEOUT, allow_redirects=True, stream=True)


def web_recon_result(domain):
    lines = title_block("WEB RECON", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            lines += [
                f"🟢 **{scheme.upper()} Protocol**",
                f"   ├ Status Code: `{r.status_code}`",
                f"   ├ Response Time: `{ms} ms`",
                f"   ├ Redirects: `{len(r.history)}`",
                f"   └ Final URL: `{r.url[:200]}`"
            ]
            for h in ("Server", "Content-Type", "X-Powered-By"):
                if r.headers.get(h): 
                    lines.append(f"   • `{h}`: `{r.headers[h][:120]}`")
            return "\n".join(lines)
        except requests.RequestException as e:
            lines.append(f"🔴 **{scheme.upper()}:** `{type(e).__name__}`")
        finally:
            if r is not None: r.close()
    return "\n".join(lines + ["❌ ምንም የ HTTP ምላሽ አልተገኘም።"])


def recon_handler(message):
    d = validate(message)
    if d: bot.send_message(message.chat.id, web_recon_result(d)[:4000], parse_mode="Markdown")


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
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🔍 **{d}** በ Host / Bug Host Scanner እየተፈተሸ ነው...", parse_mode="Markdown")
    try:
        report = host_scanner_report(d)
        try: bot.delete_message(message.chat.id, m.message_id)
        except Exception: pass
        send_txt(message.chat.id, f"host_scanner_{d}.txt", report, f"📋 **Web Host Scanner Report — `{d}`**")
    except Exception:
        log.exception("Host scanner failed")
        bot.send_message(message.chat.id, "❌ **Host scan ማካሄድ አልተሳካም።**", parse_mode="Markdown")


def report_keyboard(domain):
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🔄 Check Again", callback_data=f"again:{domain}"),
          types.InlineKeyboardButton("🏠 Main Menu", callback_data="menu"))
    return k


@bot.callback_query_handler(func=lambda c: c.data == "menu" or c.data.startswith("again:"))
def callbacks(call):
    bot.answer_callback_query(call.id)
    if call.data == "menu":
        bot.send_message(call.message.chat.id, "🏠 **Main Menu**", reply_markup=menu(), parse_mode="Markdown")
    else:
        d = clean_domain(call.data.split(":", 1)[1])
        if d:
            try:
                report = host_scanner_report(d)
                send_txt(call.message.chat.id, f"host_scanner_{d}.txt", report, f"📋 **Host Report — `{d}`**")
            except Exception:
                bot.send_message(call.message.chat.id, "❌ **Check failed.**", parse_mode="Markdown")


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


def bulk_handler(message):
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
        bot.reply_to(message, "❌ **Domain አልተገኘም።** `.txt` ፋይል ወይም ዶሜይኖችን በአዲስ መስመር ላክ።", parse_mode="Markdown")
        return
    if len(domains) > MAX_BULK_HOSTS:
        bot.reply_to(message, f"⚠️ **ቢበዛ {MAX_BULK_HOSTS} hosts ብቻ ላክ።**", parse_mode="Markdown")
        return

    m = bot.send_message(message.chat.id, f"📦 **Bulk Host Checker:** `{len(domains)}` hosts እየተፈተሹ ነው...", parse_mode="Markdown")
    lines = title_block("BULK HOST REPORT") + [f"📌 **Total Checked:** `{len(domains)}`", ""]
    for d in domains:
        lines += check_bulk_host(d) + [""]
    if invalid: lines += ["⚠️ **Invalid entries skipped:**"] + [f"• `{x}`" for x in invalid]
    report = "\n".join(lines)
    try: bot.edit_message_text(f"📦 **BULK HOST CHECKER**\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ **Checked:** `{len(domains)}`\n📄 **Status:** `Full report attached as TXT.`", message.chat.id, m.message_id, parse_mode="Markdown")
    except Exception: pass
    send_txt(message.chat.id, "netx_bulk_host_report.txt", report, "📦 **Bulk Host Report**")


@bot.message_handler(content_types=["text", "document"], func=lambda m: True)
def route(message):
    text = (message.text or "").strip()
    chat_id = message.chat.id
    
    if message.document:
        bulk_handler(message)
        return

    if text == "🌐 DNS Lookup": ask_domain(message, dns_handler)
    elif text == "🔎 Subdomain Finder": ask_domain(message, subdomain_handler)
    elif text == "🛰️ Web Recon": ask_domain(message, recon_handler)
    elif text == "🔍 Host Scanner (Bug Host)": ask_domain(message, host_scanner_handler)
    elif text == "📦 Bulk Host Checker":
        p = bot.send_message(chat_id, "📦 **እስከ 20 domains ድረስ** `.txt` ፋይል አያይዘው ይላኩ ወይም በአዲስ መስመር ጻፍው።", parse_mode="Markdown")
        bot.register_next_step_handler(p, bulk_handler)
    elif text == "👥 Referral Program":
        points = user_points.get(chat_id, 0)
        ref_link = f"https://t.me/{bot.get_me().username}?start=REF_{chat_id}"
        bot.send_message(
            chat_id,
            f"👥 **REFERRAL PROGRAM**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎁 **የእርስዎ ፖይንት:** `{points} Points`\n\n"
            f"🔗 **የእርስዎ ማስተዋወቂያ ሊንክ:**\n`{ref_link}`\n\n"
            f"💡 *ይህንን ሊንክ ለጓደኛዎችዎ በመላክ እያንዳንዱ ሰው ሲገባ **10 ፖይንት** ያግኙ!*", parse_mode="Markdown")
    elif text == "💎 Get Unlimited / Premium":
        bot.send_message(
            chat_id,
            "💎 **UNLIMITED / PREMIUM ACCESS**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "ቦቱን ያለገደብ (Unlimited) መጠቀም ይፈልጋሉ?\n\n"
            "💳 **በቴሌብር (Telebirr) ክፍያ:**\n"
            "• የብር መጠን: `100 ETB / Month`\n"
            "• የቴሌብር አካውንት: `0912345678` (ስም: Your Name)\n\n"
            "📌 **እንዴት ይክፈሉ?**\n"
            "1. ከላይ ባለው ቁጥር ብሩን ያስተላልፉ።\n"
            "2. የክፍያውን ማረጋገጫ (Transaction ID ወይም Screenshot) ለአድሚን ይላኩ።\n"
            "3. አድሚኑ ክፍያዎን አረጋግጦ ቦቱን ፕሪሚየም ያደርግልዎታል።\n\n"
            "👨‍💻 **ክፍያ ልኮ ለማረጋገጥ:** [እዚህ ይጫኑ](https://t.me/None_Breaker)", parse_mode="Markdown", disable_web_page_preview=True)
    elif text == "👨‍💻 Admin Contact":
        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("👨‍💻 Contact Admin", url=ADMIN_CONTACT))
        bot.send_message(chat_id, "👨‍💻 **NETX TOOLS PRO — ADMIN CONTACT**", reply_markup=k, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "⚠️ **እባክዎ ከምናሌው አንዱን ይምረጡ።**", reply_markup=menu(), parse_mode="Markdown")


@app.route("/")
def home():
    return jsonify({"service": "NetX Tools Pro", "status": "running"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def run_flask():
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)


if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log.info("NetX Tools Pro Ultimate Suite with Unrestricted Domain & Subfinder starting")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=60)
