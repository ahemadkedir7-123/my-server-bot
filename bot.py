
import os
import re
import io
import ssl
import socket
import time
import logging
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
import telebot
from telebot import types
from flask import Flask, jsonify

# ==================================================
# NETX TOOLS PRO — CONFIGURATION
# ==================================================

TOKEN = "8788982436:AAFTXTcXdwxUkR36DmzV8hGSiOMm-Ok28AM"
bot = telebot.TeleBot(TOKEN)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("NetXToolsPro")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "NetXToolsPro/2.0"
})

REQUEST_TIMEOUT = 12
MAX_SUBDOMAINS_IN_CHAT = 50
MAX_SUBDOMAIN_FILE_SIZE = 5 * 1024 * 1024

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "Referrer-Policy",
    "Permissions-Policy"
]


# ==================================================
# DOMAIN VALIDATION
# ==================================================

def normalize_domain(value):
    if not value:
        return None

    value = value.strip().lower()

    if "://" in value:
        try:
            value = urlparse(value).hostname or ""
        except ValueError:
            return None

    value = value.split("/")[0].rstrip(".")

    # Remove a port only when input looks like host:port.
    if value.count(":") == 1:
        host, possible_port = value.rsplit(":", 1)
        if possible_port.isdigit():
            value = host

    if not value or len(value) > 253:
        return None

    pattern = (
        r"(?=.{1,253}$)"
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
        r"[a-z]{2,63}"
    )

    if not re.fullmatch(pattern, value):
        return None

    return value


def valid_domain_or_reply(message):
    domain = normalize_domain(message.text or "")

    if not domain:
        bot.reply_to(
            message,
            "❌ Domain ትክክል አይደለም።\n"
            "ምሳሌ: example.com"
        )
        return None

    return domain


def get_domain(message, callback):
    prompt = bot.send_message(
        message.chat.id,
        "🌐 Domain ላክ።\n\n"
        "ምሳሌ: example.com\n"
        "ወይም: https://example.com"
    )
    bot.register_next_step_handler(prompt, callback)


# ==================================================
# MAIN MENU
# ==================================================

def main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton("🌐 DNS Lookup"),
        types.KeyboardButton("🔎 Subdomain Finder"),
        types.KeyboardButton("🛰️ Web Recon"),
        types.KeyboardButton("🛡️ Pentest Tools"),
        types.KeyboardButton("🔍 Host Checker"),
        types.KeyboardButton("ℹ️ Help")
    )

    return keyboard


@bot.message_handler(commands=["start", "menu"])
def start_command(message):
    bot.send_message(
        message.chat.id,
        "🚀 NETX TOOLS PRO\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "የድረ-ገጽ እና የኔትወርክ መረጃ መሣሪያዎች።\n\n"
        "🌐 DNS Lookup — IP መረጃ\n"
        "🔎 Subdomain Finder — public subdomains\n"
        "🛰️ Web Recon — መሠረታዊ web መረጃ\n"
        "🛡️ Pentest Tools — መሠረታዊ security checks\n"
        "🔍 Host Checker — ዝርዝር host report\n\n"
        "⚠️ የራስህን ወይም ለመፈተሽ ፈቃድ "
        "ያለህን ሲስተም ብቻ ተጠቀም።",
        reply_markup=main_keyboard()
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    send_help(message.chat.id)


def send_help(chat_id):
    bot.send_message(
        chat_id,
        "📘 NETX TOOLS PRO — HELP\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🌐 DNS Lookup\n"
        "Domain IP addresses ለማየት።\n\n"
        "🔎 Subdomain Finder\n"
        "ከpublic certificate እና lookup sources "
        "የተገኙ subdomains ለማየት።\n\n"
        "🛰️ Web Recon\n"
        "HTTP status, redirects እና web headers።\n\n"
        "🛡️ Pentest Tools\n"
        "TLS, security headers እና TCP ports 80/443።\n\n"
        "🔍 Host Checker\n"
        "DNS, HTTP/HTTPS, TLS, response time እና "
        "security headers በሙሉ ሪፖርት።\n\n"
        "ℹ️ እነዚህ መሣሪያዎች መሠረታዊ ምርመራ "
        "ብቻ ያደርጋሉ፤ ሙሉ security audit አይደሉም።"
    )


# ==================================================
# DNS LOOKUP
# ==================================================

def dns_lookup(domain):
    try:
        results = socket.getaddrinfo(
            domain,
            None,
            type=socket.SOCK_STREAM
        )

        ips = sorted({
            item[4][0] for item in results
        })

        if not ips:
            return f"❌ {domain}\nIP address አልተገኘም።"

        return (
            "🌐 DNS LOOKUP\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Domain: {domain}\n"
            f"IP count: {len(ips)}\n\n"
            + "\n".join(f"• {ip}" for ip in ips)
        )

    except socket.gaierror:
        return (
            f"❌ DNS መረጃ አልተገኘም።\n"
            f"Domain: {domain}"
        )

    except Exception as exc:
        log.exception("DNS lookup failed")
        return f"⚠️ DNS error: {type(exc).__name__}"


def dns_handler(message):
    domain = valid_domain_or_reply(message)
    if not domain:
        return

    bot.send_message(
        message.chat.id,
        "⏳ DNS lookup በመስራት ላይ..."
    )
    bot.send_message(
        message.chat.id,
        dns_lookup(domain)
    )


# ==================================================
# SUBDOMAIN FINDER
# Uses public passive sources; no brute-force.
# ==================================================

def find_subdomains(domain):
    found = set()
    errors = []

    # Certificate Transparency
    try:
        response = SESSION.get(
            "https://crt.sh/",
            params={
                "q": f"%.{domain}",
                "output": "json"
            },
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        try:
            records = response.json()
        except ValueError:
            records = []

        for record in records:
            names = record.get("name_value", "")

            for raw_name in names.splitlines():
                name = raw_name.strip().lower().rstrip(".")

                if name.startswith("*."):
                    name = name[2:]

                if (
                    name == domain
                    or name.endswith("." + domain)
                ):
                    if normalize_domain(name):
                        found.add(name)

    except Exception as exc:
        log.warning("crt.sh failed: %s", type(exc).__name__)
        errors.append("Certificate Transparency source unavailable")

    # HackerTarget public host search
    try:
        response = SESSION.get(
            "https://api.hackertarget.com/hostsearch/",
            params={"q": domain},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        result_text = response.text.strip()

        if result_text and "error" not in result_text.lower():
            for line in result_text.splitlines():
                parts = line.split(",")

                if not parts:
                    continue

                name = parts[0].strip().lower().rstrip(".")

                if (
                    normalize_domain(name)
                    and (
                        name == domain
                        or name.endswith("." + domain)
                    )
                ):
                    found.add(name)

    except Exception as exc:
        log.warning(
            "HackerTarget failed: %s",
            type(exc).__name__
        )
        errors.append("Secondary public lookup unavailable")

    return sorted(found), errors


def subdomain_handler(message):
    domain = valid_domain_or_reply(message)
    if not domain:
        return

    status = bot.send_message(
        message.chat.id,
        "🔎 SUBDOMAIN FINDER\n\n"
        "⏳ Public sources በመፈተሽ ላይ..."
    )

    found, errors = find_subdomains(domain)

    report_lines = [
        "NETX TOOLS PRO — SUBDOMAIN REPORT",
        f"Domain: {domain}",
        f"UTC: {datetime.now(timezone.utc).isoformat()}",
        f"Total unique names found: {len(found)}",
        "",
        *found
    ]

    if errors:
        report_lines.extend([
            "",
            "Source notes:",
            *[f"- {item}" for item in errors]
        ])

    report = "\n".join(report_lines)

    summary = (
        "🔎 SUBDOMAIN FINDER\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Domain: {domain}\n"
        f"📊 Unique names found: {len(found)}\n"
    )

    if found:
        summary += (
            "\n"
            + "\n".join(
                f"• {name}"
                for name in found[:MAX_SUBDOMAINS_IN_CHAT]
            )
        )

        if len(found) > MAX_SUBDOMAINS_IN_CHAT:
            summary += (
                f"\n\n📄 ሙሉ ውጤት: {len(found)} names "
                "በTXT ፋይል ውስጥ አሉ።"
            )
    else:
        summary += (
            "\nምንም ውጤት አልተገኘም። "
            "ይህ domain subdomains የሉትም ማለት አይደለም።"
        )

    if errors:
        summary += "\n\n⚠️ አንዳንድ public sources አልተገናኙም።"

    try:
        bot.edit_message_text(
            summary[:4000],
            message.chat.id,
            status.message_id
        )
    except Exception:
        bot.send_message(message.chat.id, summary[:4000])

    file_data = io.BytesIO(report.encode("utf-8"))
    file_data.name = f"subdomains_{domain}.txt"

    bot.send_document(
        message.chat.id,
        file_data,
        caption=(
            f"📄 Subdomain report — {domain}\n"
            f"Names found: {len(found)}"
        )
    )


# ==================================================
# BASIC WEB RECON
# ==================================================

def web_recon(domain):
    lines = [
        "🛰️ BASIC WEB RECON",
        "━━━━━━━━━━━━━━━━━━",
        f"Domain: {domain}",
        ""
    ]

    for scheme in ("https", "http"):
        response = None

        try:
            response = SESSION.get(
                f"{scheme}://{domain}/",
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True
            )

            lines.extend([
                f"Scheme: {scheme.upper()}",
                f"HTTP status: {response.status_code}",
                f"Final URL: {response.url}",
                f"Redirects: {len(response.history)}"
            ])

            server = response.headers.get("Server")
            content_type = response.headers.get("Content-Type")

            if server:
                lines.append(f"Server header: {server[:200]}")

            if content_type:
                lines.append(f"Content-Type: {content_type[:200]}")

            return "\n".join(lines)

        except requests.RequestException as exc:
            lines.append(
                f"{scheme.upper()} request failed: {type(exc).__name__}"
            )

        finally:
            if response is not None:
                response.close()

    lines.append("")
    lines.append("Neither HTTP nor HTTPS returned a response.")
    return "\n".join(lines)


def recon_handler(message):
    domain = valid_domain_or_reply(message)
    if not domain:
        return

    bot.send_message(
        message.chat.id,
        "⏳ Web recon በመስራት ላይ..."
    )
    bot.send_message(
        message.chat.id,
        web_recon(domain)[:4000]
    )


# ==================================================
# HOST CHECKER — DETAILED REPORT
# ==================================================

def host_checker_report(domain):
    started = time.perf_counter()

    lines = [
        "╔══════════════════════════╗",
        "       NETX TOOLS PRO",
        "         HOST CHECKER",
        "╚══════════════════════════╝",
        "",
        f"TARGET: {domain}",
        f"UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        "━━━━━━━━ DNS / IP ━━━━━━━━"
    ]

    # DNS
    try:
        info = socket.getaddrinfo(
            domain,
            None,
            type=socket.SOCK_STREAM
        )
        ips = sorted({item[4][0] for item in info})

        if ips:
            lines.append("🟢 DNS: RESOLVED")
            for ip in ips[:15]:
                lines.append(f"  • {ip}")
            if len(ips) > 15:
                lines.append(f"  • +{len(ips) - 15} more")
        else:
            ips = []
            lines.append("🔴 DNS: NO IP FOUND")

    except Exception as exc:
        ips = []
        lines.append(f"🔴 DNS failed: {type(exc).__name__}")

    # HTTP / HTTPS
    lines.extend(["", "━━━━━━━━ WEB STATUS ━━━━━━━━"])
    web_result = None

    for scheme in ("https", "http"):
        response = None

        try:
            request_started = time.perf_counter()
            response = SESSION.get(
                f"{scheme}://{domain}/",
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True
            )
            response_time = round(
                (time.perf_counter() - request_started) * 1000
            )

            web_result = {
                "scheme": scheme,
                "status": response.status_code,
                "url": response.url,
                "redirects": len(response.history),
                "elapsed_ms": response_time,
                "headers": dict(response.headers)
            }

            lines.extend([
                f"🟢 {scheme.upper()}: RESPONSE RECEIVED",
                f"HTTP status: {response.status_code}",
                f"Response time: {response_time} ms",
                f"Redirects: {len(response.history)}",
                f"Final URL: {response.url[:300]}"
            ])
            break

        except requests.RequestException as exc:
            lines.append(
                f"🔴 {scheme.upper()} failed: {type(exc).__name__}"
            )

        finally:
            if response is not None:
                response.close()

    # TLS certificate
    lines.extend(["", "━━━━━━━━ SSL / TLS ━━━━━━━━"])

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443),
            timeout=5
        ) as raw_socket:
            with context.wrap_socket(
                raw_socket,
                server_hostname=domain
            ) as tls_socket:
                certificate = tls_socket.getpeercert()

                lines.append("🟢 TLS certificate: VERIFIED")
                lines.append(
                    f"TLS version: {tls_socket.version()}"
                )

                expiry = certificate.get("notAfter")

                if expiry:
                    expiry_ts = ssl.cert_time_to_seconds(expiry)
                    expiry_dt = datetime.fromtimestamp(
                        expiry_ts,
                        timezone.utc
                    )
                    days_remaining = (
                        expiry_dt - datetime.now(timezone.utc)
                    ).days

                    lines.append(
                        "Certificate expires: "
                        + expiry_dt.strftime("%Y-%m-%d %H:%M UTC")
                    )
                    lines.append(
                        f"Days remaining: {days_remaining}"
                    )

    except Exception as exc:
        lines.append(
            f"🔴 TLS verification failed: {type(exc).__name__}"
        )

    # Security headers
    lines.extend(["", "━━━━━━━━ SECURITY HEADERS ━━━━━━━━"])

    if web_result:
        response_headers = {
            key.lower(): value
            for key, value in web_result["headers"].items()
        }
        present = 0

        for header in SECURITY_HEADERS:
            value = response_headers.get(header.lower())

            if value:
                present += 1
                lines.append(f"🟢 {header}: PRESENT")
                lines.append(f"   Value: {value[:200]}")
            else:
                lines.append(f"🟡 {header}: MISSING")

        lines.append(
            f"Summary: {present}/{len(SECURITY_HEADERS)} headers present"
        )
    else:
        lines.append("⚠️ HTTP headers unavailable.")

    # Standard web ports only
    lines.extend(["", "━━━━━━━━ WEB PORTS ━━━━━━━━"])

    for port in (80, 443):
        try:
            with socket.create_connection(
                (domain, port),
                timeout=3
            ):
                lines.append(f"🟢 TCP {port}: REACHABLE")
        except OSError:
            lines.append(f"🔴 TCP {port}: NOT REACHABLE")

    total_time = round(
        (time.perf_counter() - started) * 1000
    )

    lines.extend([
        "",
        "━━━━━━━━ FINAL SUMMARY ━━━━━━━━",
        f"DNS: {'OK' if ips else 'FAILED'}",
        f"Website: {'RESPONDED' if web_result else 'NO RESPONSE'}",
        f"Total check time: {total_time} ms",
        "",
        "NOTES:",
        "- This is a basic diagnostic report.",
        "- Missing headers alone do not prove a vulnerability.",
        "- A failed TLS check may mean TLS is unavailable or invalid.",
        "- This is not a complete penetration test."
    ])

    return "\n".join(lines)


def send_host_report(chat_id, domain, edit_message=None):
    try:
        report = host_checker_report(domain)

        summary = (
            "🔍 NETX TOOLS PRO\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Host: {domain}\n"
            "📋 Host check completed\n\n"
            "📄 ሙሉ የDNS, Web, TLS እና security "
            "headers ሪፖርት በTXT ፋይል ተያይዟል።"
        )

        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton(
                "🔄 Check Again",
                callback_data=f"host_again:{domain}"
            ),
            types.InlineKeyboardButton(
                "🏠 Main Menu",
                callback_data="host_menu"
            )
        )

        if edit_message:
            try:
                bot.edit_message_text(
                    summary,
                    chat_id,
                    edit_message,
                    reply_markup=keyboard
                )
            except Exception:
                bot.send_message(
                    chat_id,
                    summary,
                    reply_markup=keyboard
                )
        else:
            bot.send_message(
                chat_id,
                summary,
                reply_markup=keyboard
            )

        file_data = io.BytesIO(report.encode("utf-8"))
        file_data.name = f"host_report_{domain}.txt"

        bot.send_document(
            chat_id,
            file_data,
            caption=f"📋 HOST CHECKER REPORT — {domain}"
        )

    except Exception:
        log.exception("Host checker report failed")
        bot.send_message(
            chat_id,
            "⚠️ Host Checker ስህተት አጋጥሞታል። "
            "እባክህ በኋላ እንደገና ሞክር።"
        )


def host_checker_handler(message):
    domain = valid_domain_or_reply(message)
    if not domain:
        return

    status = bot.send_message(
        message.chat.id,
        "🔍 NETX HOST CHECKER\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Host: {domain}\n\n"
        "⏳ DNS, HTTP/HTTPS, SSL/TLS እና "
        "security headers በመፈተሽ ላይ..."
    )

    send_host_report(
        message.chat.id,
        domain,
        edit_message=status.message_id
    )


@bot.callback_query_handler(
    func=lambda call: (
        call.data == "host_menu"
        or call.data.startswith("host_again:")
    )
)
def host_checker_callback(call):
    bot.answer_callback_query(call.id)

    if call.data == "host_menu":
        bot.send_message(
            call.message.chat.id,
            "🏠 Main Menu — መሣሪያ ምረጥ።",
            reply_markup=main_keyboard()
        )
        return

    domain = normalize_domain(
        call.data.split(":", 1)[1]
    )

    if not domain:
        bot.send_message(
            call.message.chat.id,
            "❌ Domain ትክክል አይደለም።"
        )
        return

    status = bot.send_message(
        call.message.chat.id,
        "🔄 Host check እንደገና በመስራት ላይ...\n"
        f"🎯 {domain}"
    )

    send_host_report(
        call.message.chat.id,
        domain,
        edit_message=status.message_id
    )


# ==================================================
# BASIC AUTHORIZED PENTEST TOOLS
# ==================================================

def check_https_tls(domain):
    lines = ["[HTTPS / TLS]"]

    try:
        context = ssl.create_default_context()

        with socket.create_connection(
            (domain, 443),
            timeout=REQUEST_TIMEOUT
        ) as raw:
            with context.wrap_socket(
                raw,
                server_hostname=domain
            ) as tls:
                lines.append("HTTPS connection: Successful")
                lines.append(f"TLS version: {tls.version()}")

                cert = tls.getpeercert()
                expiry = cert.get("notAfter")

                if expiry:
                    lines.append(
                        f"Certificate expires: {expiry}"
                    )

    except Exception as exc:
        lines.append(
            f"HTTPS/TLS check failed: {type(exc).__name__}"
        )

    return lines


def check_security_headers(domain):
    lines = ["[Security Headers]"]
    response = None

    try:
        response = SESSION.get(
            f"https://{domain}/",
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            stream=True
        )

        lines.append(f"HTTP status: {response.status_code}")

        for header in SECURITY_HEADERS:
            value = response.headers.get(header)

            if value:
                lines.append(
                    f"[PRESENT] {header}: {value[:250]}"
                )
            else:
                lines.append(f"[MISSING] {header}")

    except requests.RequestException as exc:
        lines.append(
            f"Header check failed: {type(exc).__name__}"
        )

    finally:
        if response is not None:
            response.close()

    return lines


def check_common_web_ports(domain):
    lines = ["[Common Web Ports]"]

    for port in (80, 443):
        try:
            with socket.create_connection(
                (domain, port),
                timeout=3
            ):
                lines.append(f"TCP port {port}: reachable")
        except OSError:
            lines.append(f"TCP port {port}: not reachable")

    return lines


def run_basic_pentest(domain):
    report = [
        "NETX TOOLS PRO — BASIC SECURITY CHECK",
        f"Target: {domain}",
        f"UTC time: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Scope: basic checks only; no exploitation performed.",
        ""
    ]

    try:
        ips = sorted({
            item[4][0]
            for item in socket.getaddrinfo(
                domain,
                None,
                type=socket.SOCK_STREAM
            )
        })
        report.append("[DNS]")
        report.extend(ips or ["No IP addresses found"])
    except Exception as exc:
        report.extend([
            "[DNS]",
            f"DNS check failed: {type(exc).__name__}"
        ])

    report.append("")
    report.extend(check_https_tls(domain))
    report.append("")
    report.extend(check_security_headers(domain))
    report.append("")
    report.extend(check_common_web_ports(domain))
    report.extend([
        "",
        "IMPORTANT:",
        "- Missing headers alone do not prove a vulnerability.",
        "- Port reachability does not prove a security weakness.",
        "- This is not a full penetration test."
    ])

    return "\n".join(report)


def pentest_handler(message):
    domain = valid_domain_or_reply(message)
    if not domain:
        return

    status = bot.send_message(
        message.chat.id,
        "🛡️ BASIC SECURITY CHECK\n\n"
        "⏳ መሠረታዊ security checks በመስራት ላይ..."
    )

    report = run_basic_pentest(domain)

    try:
        bot.delete_message(
            message.chat.id,
            status.message_id
        )
    except Exception:
        pass

    file_data = io.BytesIO(report.encode("utf-8"))
    file_data.name = f"security_report_{domain}.txt"

    bot.send_document(
        message.chat.id,
        file_data,
        caption=f"🛡️ Security Check Report — {domain}"
    )


# ==================================================
# MENU ROUTER
# ==================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: True
)
def handle_menu_text(message):
    text = (message.text or "").strip()

    if text == "🌐 DNS Lookup":
        get_domain(message, dns_handler)

    elif text == "🔎 Subdomain Finder":
        get_domain(message, subdomain_handler)

    elif text == "🛰️ Web Recon":
        get_domain(message, recon_handler)

    elif text == "🛡️ Pentest Tools":
        get_domain(message, pentest_handler)

    elif text == "🔍 Host Checker":
        get_domain(message, host_checker_handler)

    elif text == "ℹ️ Help":
        send_help(message.chat.id)

    else:
        bot.send_message(
            message.chat.id,
            "ከምናሌው አንዱን ምረጥ።",
            reply_markup=main_keyboard()
        )


# ==================================================
# RENDER HEALTH ENDPOINT
# ==================================================

@app.route("/")
def home():
    return jsonify({
        "service": "NetX Tools Pro",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


def run_flask():
    port = int(os.getenv("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


# ==================================================
# START BOT
# ==================================================

if __name__ == "__main__":
    threading.Thread(
        target=run_flask,
        daemon=True
    ).start()

    log.info("NetX Tools Pro starting...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
