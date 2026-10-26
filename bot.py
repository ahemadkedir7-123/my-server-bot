import os, re, io, ssl, time, socket, logging, threading
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
MAX_BULK_HOSTS = 10
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
    lines = ["╭━━━━━━━━━━━━━━━━━━╮", "      NETX TOOLS PRO",
             f"       {title}", "╰━━━━━━━━━━━━━━━━━━╯"]
    if target:
        lines += ["", f"🎯 Target: {target}"]
    lines += ["", "🕒 UTC: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")]
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
    m = bot.send_message(message.chat.id, "🌐 Domain ላክ። ምሳሌ: example.com")
    bot.register_next_step_handler(m, callback)


def validate(message):
    d = domain_ok(message.text)
    if not d:
        bot.reply_to(message, "❌ Domain ትክክል አይደለም። ምሳሌ: example.com")
    return d


def send_txt(chat_id, filename, text, caption):
    data = io.BytesIO(text.encode("utf-8"))
    data.name = filename
    bot.send_document(chat_id, data, caption=caption)


@bot.message_handler(commands=["start", "menu"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🚀 NETX TOOLS PRO\n━━━━━━━━━━━━━━━━━━\n\n"
        "🌐 DNS Lookup\n🔎 Subdomain Finder\n🛰️ Web Recon\n"
        "🛡️ Pentest Tools\n🔍 Host Checker\n📦 Bulk Host Checker\n"
        "👨‍💻 Admin Contact\n\n"
        "ለራስህ ወይም ፈቃድ ላለህ ሲስተም ብቻ ተጠቀም።",
        reply_markup=menu())


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.send_message(message.chat.id,
        "📘 HELP\nDNS Lookup: IP addresses\nSubdomain Finder: public passive sources\n"
        "Web Recon: HTTP status and headers\nPentest Tools: basic TLS, headers and web ports\n"
        "Host Checker: combined report\nBulk Host Checker: up to 10 domains\n"
        "These are basic diagnostics, not a full security audit.")


def dns_result(domain):
    lines = title_block("DNS LOOKUP", domain) + ["", "━━━━━━━━ RESULTS ━━━━━━━━"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines += [f"🟢 {len(ips)} IP address(es) found"] + [f"• {ip}" for ip in ips[:25]]
    except Exception as e:
        lines.append(f"🔴 DNS failed: {type(e).__name__}")
    return "\n".join(lines)


def dns_handler(message):
    d = validate(message)
    if d:
        bot.send_message(message.chat.id, dns_result(d)[:4000])


def find_subdomains(domain):
    found, notes = set(), []
    try:
        r = session.get("https://crt.sh/", params={"q": f"%.{domain}", "output": "json"}, timeout=60)
        r.raise_for_status()
        for rec in r.json():
            for raw in rec.get("name_value", "").splitlines():
                name = raw.strip().lower().rstrip(".")
                if name.startswith("*."):
                    name = name[2:]
                if domain_ok(name) and (name == domain or name.endswith("." + domain)):
                    found.add(name)
        notes.append("crt.sh: responded")
    except Exception as e:
        notes.append(f"crt.sh unavailable ({type(e).__name__})")
        log.warning("crt.sh failed: %s", type(e).__name__)
    try:
        r = session.get("https://api.hackertarget.com/hostsearch/",
                        params={"q": domain}, timeout=30)
        r.raise_for_status()
        body = r.text.strip()
        if body.lower().startswith(("error", "api count", "no records")):
            notes.append("HackerTarget: " + body[:120])
        else:
            for line in body.splitlines():
                name = line.split(",")[0].strip().lower().rstrip(".")
                if domain_ok(name) and (name == domain or name.endswith("." + domain)):
                    found.add(name)
            notes.append("HackerTarget: responded")
    except Exception as e:
        notes.append(f"HackerTarget unavailable ({type(e).__name__})")
    return sorted(found), notes


def subdomain_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, "🔎 Subdomain Finder: public sources እየተፈተሹ ነው...")
    found, notes = find_subdomains(d)
    lines = title_block("SUBDOMAIN REPORT", d) + ["", f"📊 Names found: {len(found)}", ""]
    lines += [f"• {x}" for x in found[:40]] if found else ["No names returned by queried sources."]
    lines += ["", "SOURCE STATUS:"] + notes + ["", "Zero results do not prove no subdomains exist."]
    try:
        bot.edit_message_text("\n".join(lines)[:4000], message.chat.id, m.message_id)
    except Exception:
        bot.send_message(message.chat.id, "\n".join(lines)[:4000])
    send_txt(message.chat.id, f"subdomains_{d}.txt",
             "\n".join(lines + [""] + found), f"📄 Subdomain report — {d}")


def web_get(domain, scheme):
    return session.get(f"{scheme}://{domain}/", timeout=TIMEOUT,
                       allow_redirects=True, stream=True)


def web_recon_result(domain):
    lines = title_block("WEB RECON", domain) + ["", "━━━━━━━━ HTTP / HTTPS ━━━━━━━━"]
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            lines += [f"🟢 {scheme.upper()} — HTTP {r.status_code}",
                      f"⏱️ {ms} ms", f"🔁 Redirects: {len(r.history)}",
                      f"🔗 Final URL: {r.url[:220]}"]
            for h in ("Server", "Content-Type"):
                if r.headers.get(h): lines.append(f"{h}: {r.headers[h][:160]}")
            return "\n".join(lines)
        except requests.RequestException as e:
            lines.append(f"🔴 {scheme.upper()}: {type(e).__name__}")
        finally:
            if r is not None: r.close()
    return "\n".join(lines + ["No HTTP response received."])


def recon_handler(message):
    d = validate(message)
    if d: bot.send_message(message.chat.id, web_recon_result(d)[:4000])


def host_report(domain):
    lines = title_block("HOST CHECKER", domain) + ["", "━━━━━━━━ DNS / IP ━━━━━━━━"]
    ips = []
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines.append("🟢 DNS resolved" if ips else "🔴 No IP addresses")
        lines += [f"• {ip}" for ip in ips[:15]]
    except Exception as e:
        lines.append(f"🔴 DNS: {type(e).__name__}")
    lines += ["", "━━━━━━━━ HTTP / HTTPS ━━━━━━━━"]
    headers, responded = {}, False
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            headers, responded = dict(r.headers), True
            lines += [f"🟢 {scheme.upper()} — HTTP {r.status_code}",
                      f"⏱️ {ms} ms", f"🔁 Redirects: {len(r.history)}",
                      f"🔗 {r.url[:200]}"]
            break
        except requests.RequestException as e:
            lines.append(f"🔴 {scheme.upper()}: {type(e).__name__}")
        finally:
            if r is not None: r.close()
    lines += ["", "━━━━━━━━ SSL / TLS ━━━━━━━━"]
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=15) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                lines.append(f"🟢 TLS: {tls.version()}")
                expiry = tls.getpeercert().get("notAfter")
                if expiry:
                    dt = datetime.fromtimestamp(ssl.cert_time_to_seconds(expiry), timezone.utc)
                    lines += [f"Certificate expires: {dt:%Y-%m-%d %H:%M UTC}",
                              f"Days remaining: {(dt - datetime.now(timezone.utc)).days}"]
    except Exception as e:
        lines.append(f"⚠️ TLS: {type(e).__name__}")
    lines += ["", "━━━━━━━━ SECURITY HEADERS ━━━━━━━━"]
    if responded:
        lower = {k.lower(): v for k, v in headers.items()}
        count = 0
        for h in SECURITY_HEADERS:
            exists = bool(lower.get(h.lower()))
            count += int(exists)
            lines.append(f"{'🟢 PRESENT' if exists else '🟡 MISSING'}: {h}")
        lines.append(f"Summary: {count}/{len(SECURITY_HEADERS)} present")
    else:
        lines.append("Headers unavailable")
    lines += ["", "━━━━━━━━ WEB PORTS ━━━━━━━━"]
    for port in (80, 443):
        try:
            with socket.create_connection((domain, port), timeout=10):
                lines.append(f"🟢 TCP {port}: reachable")
        except OSError:
            lines.append(f"🔴 TCP {port}: not reachable")
    lines += ["", "Basic diagnostics only; missing headers do not alone prove a vulnerability."]
    return "\n".join(lines)


def host_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🔍 Checking {d}...")
    try:
        report = host_report(d)
        try:
            bot.edit_message_text(
                f"╭━━━━━━━━━━━━━━━━━━╮\n      NETX TOOLS PRO\n       HOST REPORT\n╰━━━━━━━━━━━━━━━━━━╯\n\n"
                f"🎯 Host: {d}\n✅ Check completed\n📄 Full report attached.",
                message.chat.id, m.message_id, reply_markup=report_keyboard(d))
        except Exception:
            bot.send_message(message.chat.id, f"🔍 Host report ready: {d}", reply_markup=report_keyboard(d))
        send_txt(message.chat.id, f"host_report_{d}.txt", report, f"📋 Host report — {d}")
    except Exception:
        log.exception("Host report failed")
        bot.send_message(message.chat.id, "❌ Report ማዘጋጀት አልተሳካም።")


def report_keyboard(domain):
    k = types.InlineKeyboardMarkup(row_width=2)
    k.add(types.InlineKeyboardButton("🔄 Check Again", callback_data=f"again:{domain}"),
          types.InlineKeyboardButton("🏠 Main Menu", callback_data="menu"))
    return k


@bot.callback_query_handler(func=lambda c: c.data == "menu" or c.data.startswith("again:"))
def callbacks(call):
    bot.answer_callback_query(call.id)
    if call.data == "menu":
        bot.send_message(call.message.chat.id, "🏠 Main Menu", reply_markup=menu())
    else:
        d = domain_ok(call.data.split(":", 1)[1])
        if d:
            # Reuse the normal report path without needing a fake Message.
            try:
                report = host_report(d)
                send_txt(call.message.chat.id, f"host_report_{d}.txt", report, f"📋 Host report — {d}")
            except Exception:
                bot.send_message(call.message.chat.id, "❌ Host check failed.")


def check_bulk_host(domain):
    lines = [f"🎯 {domain}"]
    try:
        ips = sorted({x[4][0] for x in socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)})
        lines.append("DNS: OK — " + ", ".join(ips[:3]) if ips else "DNS: no IP")
    except Exception as e:
        lines.append(f"DNS: FAILED ({type(e).__name__})")
    responded = False
    last_error = "unknown"
    for scheme in ("https", "http"):
        r = None
        try:
            t = time.perf_counter()
            r = web_get(domain, scheme)
            ms = round((time.perf_counter() - t) * 1000)
            lines.append(f"{scheme.upper()}: HTTP {r.status_code} • {ms} ms")
            responded = True
            break
        except requests.RequestException as e:
            last_error = type(e).__name__
        finally:
            if r is not None: r.close()
    if not responded: lines.append(f"Web: no response ({last_error})")
    return lines


def bulk_handler(message):
    domains, invalid = [], []
    for item in (message.text or "").splitlines():
        if not item.strip(): continue
        d = domain_ok(item)
        if d:
            if d not in domains: domains.append(d)
        else: invalid.append(item.strip()[:80])
    if not domains:
        bot.reply_to(message, "❌ Domain አልተገኘም። እያንዳንዱን domain በአዲስ መስመር ላክ።")
        return
    if len(domains) > MAX_BULK_HOSTS:
        bot.reply_to(message, f"⚠️ ቢበዛ {MAX_BULK_HOSTS} hosts ብቻ ላክ።")
        return
    m = bot.send_message(message.chat.id, f"📦 Bulk Host Checker: {len(domains)} hosts እየተፈተሹ ነው...")
    lines = title_block("BULK HOST REPORT") + [f"Hosts: {len(domains)}", ""]
    for d in domains:
        lines += check_bulk_host(d) + [""]
    if invalid: lines += ["Invalid entries skipped:"] + invalid
    report = "\n".join(lines)
    try: bot.edit_message_text(f"📦 BULK HOST CHECKER\n━━━━━━━━━━━━━━━━━━\n✅ Checked: {len(domains)}\n📄 Full results attached as TXT.", message.chat.id, m.message_id)
    except Exception: pass
    send_txt(message.chat.id, "netx_bulk_host_report.txt", report, "📦 Bulk Host Report")


def pentest_report(domain):
    lines = title_block("BASIC SECURITY CHECK", domain)
    lines += ["", "Scope: basic TLS, security headers and common web ports. No exploitation."]
    lines += ["", "━━━━━━━━ TLS ━━━━━━━━"]
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=15) as raw:
            with ctx.wrap_socket(raw, server_hostname=domain) as tls:
                lines.append(f"🟢 TLS: {tls.version()}")
                exp = tls.getpeercert().get("notAfter")
                if exp: lines.append(f"Certificate expiry: {exp}")
    except Exception as e:
        lines.append(f"⚠️ TLS: {type(e).__name__}")
    lines += ["", "━━━━━━━━ SECURITY HEADERS ━━━━━━━━"]
    r = None
    try:
        r = session.get(f"https://{domain}/", timeout=TIMEOUT, allow_redirects=True, stream=True)
        lines.append(f"HTTP status: {r.status_code}")
        for h in SECURITY_HEADERS:
            lines.append(f"{'🟢 PRESENT' if r.headers.get(h) else '🟡 MISSING'}: {h}")
    except requests.RequestException as e:
        lines.append(f"⚠️ Headers: {type(e).__name__}")
    finally:
        if r is not None: r.close()
    lines += ["", "━━━━━━━━ WEB PORTS ━━━━━━━━"]
    for p in (80, 443):
        try:
            with socket.create_connection((domain, p), timeout=10): lines.append(f"🟢 TCP {p}: reachable")
        except OSError: lines.append(f"🔴 TCP {p}: not reachable")
    lines += ["", "Basic diagnostics only; these checks do not prove a vulnerability."]
    return "\n".join(lines)


def pentest_handler(message):
    d = validate(message)
    if not d: return
    m = bot.send_message(message.chat.id, f"🛡️ Basic security checks: {d}...")
    report = pentest_report(d)
    try: bot.delete_message(message.chat.id, m.message_id)
    except Exception: pass
    send_txt(message.chat.id, f"security_report_{d}.txt", report, f"🛡️ Security Report — {d}")


@bot.message_handler(content_types=["text"], func=lambda m: True)
def route(message):
    text = (message.text or "").strip()
    if text == "🌐 DNS Lookup": ask_domain(message, dns_handler)
    elif text == "🔎 Subdomain Finder": ask_domain(message, subdomain_handler)
    elif text == "🛰️ Web Recon": ask_domain(message, recon_handler)
    elif text == "🛡️ Pentest Tools": ask_domain(message, pentest_handler)
    elif text == "🔍 Host Checker": ask_domain(message, host_handler)
    elif text == "📦 Bulk Host Checker":
        p = bot.send_message(message.chat.id, "እስከ 10 domains ድረስ ላክ። እያንዳንዱን በአዲስ መስመር አስገባ።")
        bot.register_next_step_handler(p, bulk_handler)
    elif text == "👨‍💻 Admin Contact":
        k = types.InlineKeyboardMarkup()
        k.add(types.InlineKeyboardButton("👨‍💻 Contact Admin", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, "NETX TOOLS PRO — ADMIN CONTACT", reply_markup=k)
    elif text == "ℹ️ Help":
        bot.send_message(message.chat.id,
            "📘 HELP\nDNS Lookup: IP addresses\nSubdomain Finder: passive public sources\n"
            "Web Recon: HTTP status/headers\nPentest Tools: basic authorized checks\n"
            "Host Checker: full diagnostic report\nBulk Host Checker: up to 10 hosts\n"
            "These tools are basic diagnostics, not a full security audit.")
    else:
        bot.send_message(message.chat.id, "ከምናሌው አንዱን ምረጥ።", reply_markup=menu())


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
    log.info("NetX Tools Pro starting")
    # Run only one live instance using this bot token to avoid getUpdates conflicts.
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=60)
