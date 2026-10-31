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
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NetXToolsPro/4.0"})


def smart_domain(value):
    """ ተጠቃሚው 'ኢትዮ ቴሌኮም' ወይም 'safaricom' ብሎ ቢጽፍ ራሱ አውቶማቲክ .et አያይዞ ትክክለኛ ዶሜይን የሚያደርግ """
    val = (value or "").strip().lower()
    if "://" in val:
        val = urlparse(val).hostname or ""
    val = val.split("/")[0].rstrip(".")
    
    # ስም ብቻ ከገባ (ለምሳሌ ethiotelecom) ራሱ .et ወይም .com ይጨምራል
    if "." not in val:
        val = f"{val}.et"
        
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
        types.KeyboardButton("🛡️ Advanced Pentest & Bug Host"),
        types.KeyboardButton("🔍 Host Checker"),
        types.KeyboardButton("📦 Bulk Host Checker"),
        types.KeyboardButton("👨‍💻 Admin Contact"),
        types.KeyboardButton("ℹ️ Help"),
    )
    return k


def ask_domain(message, callback):
    m = bot.send_message(message.chat.id, "🌐 **ስም ወይም ዶሜይን ላክ።** (ምሳሌ: `ethiotelecom` ወይም `safaricom.et`):", parse_mode="Markdown")
    bot.register_next_step_handler(m, callback)


def validate(message):
    d = smart_domain(message.text)
    if not d:
        bot.reply_to(message, "❌ **ትክክለኛ ስም ወይም ዶሜይን አልገባም።** እንደገና ይሞክሩ።", parse_mode="Markdown")
    return d


def send_txt(chat_id, filename, text, caption):
    data = io.BytesIO(text.encode("utf-8"))
    data.name = filename
    bot.send_document(chat_id, data, caption=caption, parse_mode="Markdown")


@bot.message_handler(commands=["start", "menu"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚀 **NETX TOOLS PRO (ULTIMATE EDITION)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌐 **DNS Lookup**\n"
        "🔎 **Subdomain Finder (Deep 1000+ Sources)**\n"
        "🛰️ **Web Recon**\n"
        "🛡️ **Advanced Pentest & Bug Host**\n"
        "🔍 **Host Checker**\n"
        "📦 **Bulk Host Checker**\n"
        "👨‍💻 **Admin Contact**\n\n"
        "💡 *ለራስህ ወይም ፈቃድ ላለህ ሲስተም ብቻ ተጠቀም።*",
        reply_markup=menu(), parse_mode="Markdown")


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id,
        "📘 **HELP / አጠቃቀም**\n\n"
        "• **Subdomain Finder:** ዶሜይን ወይም ስም ብቻ (ለምሳሌ ethiotelecom) ሲያስገቡ ከሺህ በላይ ንዑስ ዶሜይኖችን በጥልቀት ይፈልጋል። ከ 10 በታች ከሆነ ቻት ውስጥ፤ ከ 10 በላይ ከሆነ በፋይል (.txt) ይልካል።\n"
        "• **Advanced Pentest & Bug Host:** የኮነክሽን ጥንካሬን፣ የትኞቹ ሆስቶች ከክፍያ ነፃ (Free Bug Host) እንደሆኑ፣ የደህንነት ድክመቶችን እና ፖርቶችን በጥልቀት ይፈትሻል።", parse_mode="Markdown")


def dns_result(domain):
    lines = title_block("DNS LOOKUP", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━", "📌 **RESULTS:**"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines += [f"🟢 **Total IPs Found:** `{len(ips)}`"] + [f"  • `{ip}`" for ip in ips[:25]]
    except Exception as e:
        lines.append(f"🔴 **DNS failed:** `{type(e).__name__}`")
    return "\n".join(lines)


def dns_handler(message):
    d = validate(message)
    if d:
        bot.send_message(message.chat.id, dns_result(d)[:4000], parse_mode="Markdown")


# ==========================================
# 🔎 DEEP SUBDOMAIN FINDER (ከ 1000+ በላይ ዶሜይኖችን በጥልቀት የሚፈልግ)
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


def host_report(domain):
    lines = title_block("HOST CHECKER", domain) + ["━━━━━━━━━━━━━━━━━━━━━━━━━━", "📌 **1. DNS / IP RESOLUTION:**"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines.append("🟢 **Status:** `Resolved Successfully`" if ips else "🔴 **Status:** `No IP Found`")
        lines += [f"   • `{ip}`" for ip in ips[:15]]
    except Exception as e:
        lines.append(f"🔴 **DNS Error:** `{type(e).__name__}`")
        
    lines += ["", "📌 **2. HTTP / HTTPS STATUS:**"]
    headers, responded = {}, False
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            headers, responded = dict(r.headers), True
            lines += [
                f"🟢 **Scheme:** `{scheme.upper()}`",
                f"   ├ HTTP Status: `{r.status_code}`",
                f"   ├ Speed: `{ms} ms`",
                f"   └ Final URL: `{r.url[:180]}`"
            ]
            break
        except requests.RequestException as e:
            lines.append(f"🔴 **{scheme.upper()} Error:** `{type(e).__name__}`")
        finally:
            if r is not None: r.close()
            
    lines += ["", "📌 **3. SSL / TLS CERTIFICATE:**"]
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=15) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                lines.append(f"🟢 **Protocol:** `{tls.version()}`")
                expiry = tls.getpeercert().get("notAfter")
                if expiry:
                    dt = datetime.fromtimestamp(ssl.cert_time_to_seconds(expiry), timezone.utc)
                    days_left = (dt - datetime.now(timezone.utc)).days
                    lines += [
                        f"   ├ Expires At: `{dt.strftime('%Y-%m-%d %H:%M UTC')}`",
                        f"   └ Days Remaining: `{days_left} Days`"
                    ]
    except Exception as e:
        lines.append(f"⚠️ **TLS Check Failed:** `{type(e).__name__}`")
        
    lines += ["", "📌 **4. SECURITY HEADERS:**"]
    if responded:
        lower = {k.lower(): v for k, v in headers.items()}
        count = 0
        for h in SECURITY_HEADERS:
            exists = bool(lower.get(h.lower()))
            count += int(exists)
            lines.append(f"   • `{'🟢 PRESENT' if exists else '🟡 MISSING'}` : {h}")
        lines.append(f"   📊 **Score:** `{count}/{len(SECURITY_HEADERS)}` headers present.")
    else:
        lines.append("   ⚠️ Headers unavailable.")
        
    lines += ["", "📌 **5. PORT AVAILABILITY:**"]
    for port in (80, 443, 8080, 8443):
        try:
            with socket.create_connection((domain, port), timeout=5):
                lines.append(f"   • Port `{port}`: 🟢 **OPEN**")
        except OSError:
            lines.append(f"   • Port `{port}`: 🔴 **CLOSED**")
            
    return "\n".join(lines)


def host_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🔍 **{d}** በቅኝት ላይ ነው...", parse_mode="Markdown")
    try:
        report = host_report(d)
        try:
            bot.edit_message_text(
                f"╔══════════════════════════════════╗\n"
                f"║          🛡️ NETX TOOLS PRO       ║\n"
                f"║           HOST REPORT            ║\n"
                f"╚══════════════════════════════════╝\n\n"
                f"🎯 **Target:** `{d}`\n"
                f"✅ **Status:** `Scan Completed Successfully!`\n"
                f"📄 **Details:** `Full report attached as text file.`",
                message.chat.id, m.message_id, reply_markup=report_keyboard(d), parse_mode="Markdown")
        except Exception:
            bot.send_message(message.chat.id, f"🔍 **Host report ready for:** `{d}`", reply_markup=report_keyboard(d), parse_mode="Markdown")
        send_txt(message.chat.id, f"host_report_{d}.txt", report, f"📋 **Host Report — `{d}`**")
    except Exception:
        log.exception("Host report failed")
        bot.send_message(message.chat.id, "❌ **Report ማዘጋጀት አልተሳካም።**", parse_mode="Markdown")


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
        d = smart_domain(call.data.split(":", 1)[1])
        if d:
            try:
                report = host_report(d)
                send_txt(call.message.chat.id, f"host_report_{d}.txt", report, f"📋 **Host Report — `{d}`**")
            except Exception:
                bot.send_message(call.message.chat.id, "❌ **Host check failed.**", parse_mode="Markdown")


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
        d = smart_domain(item)
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


# ==========================================
# 🛡️ ADVANCED PENTEST & BUG HOST ANALYZER (በሙሉ አቅም የተስተካከለ)
# ==========================================
def pentest_report(domain):
    lines = title_block("ADVANCED PENTEST & BUG HOST AUDIT", domain) + [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Scope: Comprehensive TLS check, security headers analysis, open ports, vulnerability indicators, and Free Bug Host detection.*",
        ""
    ]
    
    # 1. TLS / SSL Deep Inspection
    lines += ["📌 **1. TLS / SSL CONFIGURATION:**"]
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=15) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                cipher = tls.cipher()
                lines += [
                    f"   • TLS Version: 🟢 `{tls.version()}`",
                    f"   • Cipher Suite: ` {cipher[0]} `",
                    f"   • Key Exchange Strength: ` {cipher[2]} bits`"
                ]
                exp = tls.getpeercert().get("notAfter")
                if exp: 
                    lines.append(f"   • Certificate Expiry: `{exp}`")
    except Exception as e:
        lines.append(f"   🔴 TLS Audit Failed: `{type(e).__name__}`")

    # 2. Security Headers & Bug Host / Free Host Analysis
    lines += ["", "📌 **2. BUG HOST & SECURITY HEADERS AUDIT:**"]
    r = None
    is_free_bug_host = False
    try:
        r = session.get(f"https://{domain}/", timeout=TIMEOUT, allow_redirects=True, stream=True)
        status = r.status_code
        server = r.headers.get("Server", "Unknown")
        lines.append(f"   • HTTP Response Status: `{status}`")
        lines.append(f"   • Web Server Banner: `{server}`")
        
        # Bug Host / Free Host ሎጂክ (Status 200, 301, 302, 403 የሆኑ እና Cloud/CDN ያላቸው Free Host ሊሆኑ ይችላሉ)
        if status in [200, 301, 302, 403]:
            is_free_bug_host = True
            lines.append(f"   • 🔥 **Bug Host Potential:** 🟢 **HIGH (Active Response Status {status})**")
        else:
            lines.append(f"   • ⚠️ **Bug Host Potential:** 🟡 Low (Status {status})")

        for h in SECURITY_HEADERS:
            val = r.headers.get(h)
            if val:
                lines.append(f"   • 🟢 `{h}`: `Present`")
            else:
                lines.append(f"   • 🟡 `{h}`: `Missing (Vulnerability Risk)`")
                
    except requests.RequestException as e:
        lines.append(f"   🔴 Inspection Failed: `{type(e).__name__}`")
    finally:
        if r is not None: r.close()

    # 3. Vulnerability Port Scanner
    lines += ["", "📌 **3. VULNERABILITY PORT SCANNER:**"]
    target_ports = [21, 22, 53, 80, 443, 8080, 8443, 3306]
    open_ports_count = 0
    for p in target_ports:
        try:
            with socket.create_connection((domain, p), timeout=3):
                lines.append(f"   • Port `{p}` (Active Service): 🟢 **OPEN**")
                open_ports_count += 1
        except OSError:
            pass
    if open_ports_count == 0:
        lines.append("   • No standard public web/admin ports detected open.")

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ *Disclaimer: Authorized penetration testing and bug hunting diagnostics only.*"
    ]
    return "\n".join(lines)


def pentest_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🛡️ **Advanced Pentest & Bug Host Audit** እየተካሄደ ነው (`{d}`)... ትንሽ ይጠብቁ...", parse_mode="Markdown")
    report = pentest_report(d)
    try: bot.delete_message(message.chat.id, m.message_id)
    except Exception: pass
    send_txt(message.chat.id, f"security_audit_{d}.txt", report, f"🛡️ **Advanced Security & Bug Host Report — `{d}`**")


@bot.message_handler(content_types=["text", "document"], func=lambda m: True)
def route(message):
    text = (message.text or "").strip()
    if message.document:
        bulk_handler(message)
        return

    if text == "🌐 DNS Lookup": ask_domain(message, dns_handler)
    elif text == "🔎 Subdomain Finder": ask_domain(message, subdomain_handler)
    elif text == "🛰️ Web Recon": ask_domain(message, recon_handler)
    elif text == "🛡️ Advanced Pentest & Bug Host": ask_domain(message, pentest_handler)
    elif text == "🔍 Host Checker": ask_domain(message, host_handler)
    elif text == "📦 Bulk Host Checker":
        p = bot.send_message(message.chat.id, "📦 **እስከ 20 domains ድረስ** `.txt` ፋይል አያይዘው ይላኩ ወይም በአዲስ መስመር ጻፍው።", parse_mode="Markdown")
        bot.register_next_step_handler(p, bulk_handler)
    elif text == "👨‍💻 Admin Contact":
        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("👨‍💻 Contact Admin", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, "👨‍💻 **NETX TOOLS PRO — ADMIN CONTACT**", reply_markup=k, parse_mode="Markdown")
    elif text == "ℹ️ Help":
        bot.send_message(message.chat.id,
            "📘 **HELP MENU**\n\n"
            "• **Subdomain Finder:** ስም ወይም ዶሜይን ብቻ ሲያስገቡ (ለምሳሌ ethiotelecom) ከሺህ በላይ ንዑስ ዶሜይኖችን በጥልቀት ይፈልጋል።\n"
            "• **Advanced Pentest & Bug Host:** የደህንነት ድክመቶችን እና የትኞቹ ሆስቶች ነፃ (Bug Host) ሊሆኑ እንደሚችሉ በዝርዝር ይተነትናል።", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ **እባክዎ ከምናሌው አንዱን ይምረጡ።**", reply_markup=menu(), parse_mode="Markdown")


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
    log.info("NetX Tools Pro Ultimate Edition starting")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=60)
