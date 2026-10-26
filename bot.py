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

TOKEN = "8788982436:AAFTXTcXdwxUkR36DmzV8hGSiOMm-Ok28AM"
bot = telebot.TeleBot(TOKEN)
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
session.headers.update({"User-Agent": "NetXToolsPro/3.0"})


def domain_ok(value):
    value = (value or "").strip().lower()
    if "://" in value:
        value = urlparse(value).hostname or ""
    value = value.split("/")[0].rstrip(".")
    if value.count(":") == 1:
        host, port = value.rsplit(":", 1)
        if port.isdigit():
            value = host
    pat = r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    return value if re.fullmatch(pat, value) else None


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
        types.KeyboardButton("🛡️ Pentest Tools"),
        types.KeyboardButton("🔍 Host Checker"),
        types.KeyboardButton("📦 Bulk Host Checker"),
        types.KeyboardButton("👨‍💻 Admin Contact"),
        types.KeyboardButton("ℹ️ Help"),
    )
    return k


def ask_domain(message, callback):
    m = bot.send_message(message.chat.id, "🌐 **Domain ላክ።** ምሳሌ: `example.com`", parse_mode="Markdown")
    bot.register_next_step_handler(m, callback)


def validate(message):
    d = domain_ok(message.text)
    if not d:
        bot.reply_to(message, "❌ **Domain ትክክል አይደለም።** ምሳሌ: `example.com`", parse_mode="Markdown")
    return d


def send_txt(chat_id, filename, text, caption):
    data = io.BytesIO(text.encode("utf-8"))
    data.name = filename
    bot.send_document(chat_id, data, caption=caption, parse_mode="Markdown")


@bot.message_handler(commands=["start", "menu"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚀 **NETX TOOLS PRO**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🌐 **DNS Lookup**\n"
        "🔎 **Subdomain Finder**\n"
        "🛰️ **Web Recon**\n"
        "🛡️ **Pentest Tools (Advanced)**\n"
        "🔍 **Host Checker**\n"
        "📦 **Bulk Host Checker**\n"
        "👨‍💻 **Admin Contact**\n\n"
        "💡 *ለራስህ ወይም ፈቃድ ላለህ ሲስተም ብቻ ተጠቀም።*",
        reply_markup=menu(), parse_mode="Markdown")


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id,
        "📘 **HELP / አጠቃቀም**\n\n"
        "• **DNS Lookup:** የአይፒ አድራሻዎችን ይፈልጋል።\n"
        "• **Subdomain Finder:** ከብዙ ምንጮች ንዑስ ዶሜይኖችን በጥልቀት ያወጣል።\n"
        "• **Pentest Tools:** ሙሉ የደህንነት ቅኝት (SSL, Security Headers, Ports እና Vulnerability Indicators) ያከናውናል።\n"
        "• **Bulk Host Checker:** በርካታ ዶሜይኖችን በአንድ ላይ ይፈትሻል።", parse_mode="Markdown")


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


def find_subdomains(domain):
    found, notes = set(), []
    try:
        r = session.get("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"}, timeout=30)
        if r.status_code == 200:
            for rec in r.json():
                for raw in rec.get("name_value", "").splitlines():
                    name = raw.strip().lower().rstrip(".")
                    if name.startswith("*."): name = name[2:]
                    if domain_ok(name) and (name == domain or name.endswith("." + domain)):
                        found.add(name)
            notes.append("✅ crt.sh: Connected")
    except Exception as e:
        notes.append(f"⚠️ crt.sh: {type(e).__name__}")

    try:
        r = session.get("https://api.hackertarget.com/hostsearch/", params={"q": domain}, timeout=15)
        if r.status_code == 200 and "API count exceeded" not in r.text:
            for line in r.text.splitlines():
                parts = line.split(',')
                if parts:
                    name = parts[0].strip().lower().rstrip(".")
                    if domain_ok(name) and (name == domain or name.endswith("." + domain)):
                        found.add(name)
            notes.append("✅ HackerTarget: Connected")
    except Exception as e:
        notes.append(f"⚠️ HackerTarget: {type(e).__name__}")

    try:
        buf_url = f"https://dns.bufferover.run/dns?q=.{domain}"
        res = requests.get(buf_url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('FD_ALL', []) + data.get('RD_ALL', []):
                parts = item.split(',')
                if len(parts) > 1:
                    sub = parts[1].strip().lower()
                    if domain_ok(sub) and (sub == domain or sub.endswith("." + domain)):
                        found.add(sub)
            notes.append("✅ BufferOver: Connected")
    except Exception as e:
        notes.append(f"⚠️ BufferOver: {type(e).__name__}")

    return sorted(found), notes


def subdomain_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, "🔎 **Subdomain Finder:** ከሁሉም ምንጮች በጥልቀት በመፈለግ ላይ...", parse_mode="Markdown")
    found, notes = find_subdomains(d)
    
    lines = title_block("SUBDOMAIN REPORT", d) + [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 **Total Subdomains Found:** `{len(found)}`",
        ""
    ]
    lines += [f"• `{x}`" for x in found[:50]] if found else ["⚠️ ምንም ንዑስ ዶሜይን አልተገኘም።"]
    lines += ["", "📌 **SOURCE STATUS:**"] + notes
    
    try:
        bot.edit_message_text("\n".join(lines)[:4000], message.chat.id, m.message_id, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, "\n".join(lines)[:4000], parse_mode="Markdown")
        
    send_txt(message.chat.id, f"subdomains_{d}.txt", "\n".join(lines + [""] + found), f"📄 **Subdomain Report — `{d}`**")


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
        ips = sorted({x[4][0] for x})
