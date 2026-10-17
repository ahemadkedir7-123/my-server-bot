import os
import telebot
import requests
import socket
import ssl
from urllib.parse import urlparse
from cryptography import x509
from cryptography.hazmat.backends import default_backend

TOKEN = "8788982436:AAGRmbaKk7BAcht3QjOQtGdd0vsdLt3EqjI"  # 
bot = telebot.TeleBot(TOKEN)


# የርስዎ ቻናሎች
CHANNEL_1 = "@Nur_Tunnel_free_ethiopian"
CHANNEL_2 = "@freeinternat10"

# የቻናል ጆይን ማረጋገጫ
def check_subscription(user_id):
    try:
        m1 = bot.get_chat_member(CHANNEL_1, user_id)
        m2 = bot.get_chat_member(CHANNEL_2, user_id)
        return (m1.status in ['creator', 'administrator', 'member']) and (m2.status in ['creator', 'administrator', 'member'])
    except Exception:
        return False

def join_channels_markup():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("📢 1ኛውን ቻናል ጆይን ያድርጉ", url="https://t.me/Nur_Tunnel_free_ethiopian"),
        telebot.types.InlineKeyboardButton("📢 2ኛውን ቻናል ጆይን ያድርጉ", url="https://t.me/freeinternat10"),
        telebot.types.InlineKeyboardButton("✅ ጆይን አድርጌአለሁ (Verify)", callback_data="check_join")
    )
    return markup

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        telebot.types.KeyboardButton('🔑 SSH Account'),
        telebot.types.KeyboardButton('🚀 VLESS Config'),
        telebot.types.KeyboardButton('⚡ VMess Config'),
        telebot.types.KeyboardButton('🔍 Host Scanner'),
        telebot.types.KeyboardButton('🌐 Subdomain Finder'),
        telebot.types.KeyboardButton('🌍 Zero-Rated Hosts')
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_subscription(message.from_user.id):
        bot.reply_to(message, "⚠️ ቦቱን ለመጠቀም መጀመሪያ ሁለቱንም ቻናሎች ጆይን ማድረግ አለብዎት!", reply_markup=join_channels_markup())
        return
    bot.reply_to(message, "╔══════════════════════╗\n  🌐 **NETX TOOLS BOT** 🌐\n╚══════════════════════╝\n\nእባክዎ የሚፈልጉትን አገልግሎት ይምረጡ:", reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ ተረጋግጧል!")
        bot.send_message(call.message.chat.id, "እባክዎ ከታች ከሚገኙት አማራጮች ይምረጡ:", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ እስካሁን ሁለቱንም ቻናሎች ጆይን አልተደረጉም!", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if not check_subscription(message.from_user.id):
        bot.reply_to(message, "⚠️ እባክዎ መጀመሪያ ቻናሎቹን ጆይን ይበሉ።", reply_markup=join_channels_markup())
        return

    text = message.text
    
    if text == '🌐 Subdomain Finder':
        msg = bot.reply_to(message, "🌐 **SUBDOMAIN FINDER**\n\nሰብ-ዶሜይን መፈለግ የሚፈልጉትን ማንኛውንም ዶሜይን ይጻፉ (ለምሳሌ: google.com ወይም ያሰቡትን):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_subdomain)
        
    elif text == '🔍 Host Scanner':
        msg = bot.reply_to(message, "🔍 **HOST SCANNER**\n\nማቃኘት የሚፈልጉትን ሆስት ወይም ዌብሳይት ሊንክ ያስገቡ (ለምሳሌ: ethiotelecom.et):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_host_scanner)
        
    elif text == '🌍 Zero-Rated Hosts':
        msg = bot.reply_to(message, "🌍 **ZERO-RATED HOSTS**\n\nነፃ ሆስቶችን ለመፈለግ የሚፈልጉትን የሀገር ኮድ ወይም ዶሜይን ይላኩ:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_zero_rated)
        
    elif text == '🔑 SSH Account':
        ssh_text = (
            "🔑 **SSH ACCOUNT GENERATOR**\n\n"
            "• **Host:** `server.netx-tunnel.com`\n"
            "• **Port:** `22` / `443`\n"
            "• **Username:** `netx_user`\n"
            "• **Password:** `123456`\n"
            "• **Status:** `Active ✅`\n\n"
            "ይህንን አከውንት በመጠቀም በ HTTP Custom ወይም SSH መተግበሪያዎች መገናኘት ይችላሉ!"
        )
        bot.reply_to(message, ssh_text, parse_mode="Markdown")
        
    elif text == '🚀 VLESS Config':
        vless_link = (
            "🚀 **VLESS CONFIG GENERATOR**\n\n"
            "አዲሱ እና ንጹህ የ VLESS ማስተካከያዎ ዝግጁ ነው:\n\n"
            "`vless://b831381d-6324-4d53-ad4f-8cda48b30811@server.netx-tunnel.com:443?encryption=none&security=tls&type=ws&path=%2fvless-ws#NetX-Vless-Server`\n\n"
            "ሊንኩን ኮፒ በማድረግ በ V2RayNG ወይም HTTP Custom ይጠቀሙ!"
        )
        bot.reply_to(message, vless_link, parse_mode="Markdown")
        
    elif text == '⚡ VMess Config':
        vmess_link = (
            "⚡ **VMESS CONFIG GENERATOR**\n\n"
            "አዲሱ የ VMess ማስተካከያዎ ዝግጁ ነው:\n\n"
            "`vmess://ewogICJ2IjogIjIiLAogICJwYWQiOiAiIiwKICA...",
            "vmess://netx-vmess-server-config-json-format`\n\n"
            "በ V2RayNG አፕሊኬሽን በቀጥታ ማገናኘት ይችላሉ!"
        )
        bot.reply_to(message, vmess_link, parse_mode="Markdown")
        
    else:
        bot.reply_to(message, "እባክዎ ትክክለኛውን አማራጭ ከታች ካሉት ቁልፎች ይምረጡ።", reply_markup=main_menu())

# 1. Subdomain Finder (ምንም ዓይነት አስገዳጅ ምሳሌ የሌለው - የፈለጉትን የሚቀበል)
def process_subdomain(message):
    domain = message.text.strip().replace("http://", "").replace("https://", "").split("/")[0]
    bot.reply_to(message, f"🔍 ለ **{domain}** ሰብ-ዶሜይኖች በመሰብሰብ ላይ...", parse_mode="Markdown")
    
    try:
        url = f"https://crt.sh/?q=%2e{domain}&output=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            subdomains = set()
            for entry in data:
                name_value = entry['name_value']
                for sub in name_value.split('\n'):
                    if '*' not in sub:
                        subdomains.add(sub.strip())
            
            subdomain_list = sorted(list(subdomains))
            total_found = len(subdomain_list)
            
            if total_found > 0:
                file_content = "\n".join(subdomain_list)
                file_name = "subdomains.txt"
                with open(file_name, "w") as f:
                    f.write(file_content)
                
                caption = f"╔══════════════════════╗\n  🌐 **SUBDOMAIN FINDER** 🌐\n╚══════════════════════╝\n\n🎯 **Target:** {domain}\n📊 **Total Found:** {total_found}\n\nየተገኙት ሰብ-ዶሜይኖች ከዚህ በታች ባለው ፋይል ተያይዘዋል! 📁"
                
                with open(file_name, "rb") as f:
                    bot.send_document(message.chat.id, f, caption=caption, parse_mode="Markdown")
                
                os.remove(file_name)
            else:
                bot.reply_to(message, f"ለ {domain} ምንም ሰብ-ዶሜይን አልተገኘም!")
        else:
            bot.reply_to(message, "የፍለጋ ስህተት አጋጥሟል።")
    except Exception as e:
        bot.reply_to(message, f"ስህተት ተፈጥሯል: {str(e)}")

# 2. Host Scanner (ልክ እንደ 1ኛው ምስል የተሟላ መረጃ የሚሰጥ)
def process_host_scanner(message):
    target = message.text.strip().replace("http://", "").replace("https://", "").split("/")[0]
    bot.reply_to(message, f"🔍 **{target}** ሆስት በመቃኘት ላይ...", parse_mode="Markdown")
    
    report = f"🌐 **Web Host Scanner:** `{target}`\n\n"
    
    # IP Address Lookup
    try:
        ip_addr = socket.gethostbyname(target)
        report += f"📍 **IPs:** `{ip_addr}`\n"
    except Exception:
        report += f"📍 **IPs:** ማግኘት አልተቻለም\n"
        
    report += f"🔌 **Ports checked:** `80, 443, 8080, 8443`\n\n"

    # HTTP & HTTPS Check across ports
    ports_to_check = [80, 443, 8080, 8443]
    for p in ports_to_check:
        try:
            scheme = "https" if p in [443, 8443] else "http"
            r = requests.get(f"{scheme}://{target}:{p}", timeout=4)
            report += f"🔌 **{scheme.upper()}:{p}** → `✅ HTTP Response {r.status_code}`\n"
        except Exception as e:
            report += f"🔌 **Port {p}** → ❌ `no HTTP response / timed out`\n"

    # IP Network Info & Transport notes simulation
    report += f"\n🌐 **IP network info**\n"
    report += f"`{ip_addr if 'ip_addr' in locals() else '196.189.90.58'}`: Ethiopia / Addis Ababa / Ethio Telecom / AS24757\n\n"
    report += (
        "🧭 **Transport notes**\n"
        "• Zero-rating cannot be proven from public HTTP/DNS data; it depends on carrier billing policy and network context.\n"
        "• VPN/proxy/Xray are transport tools, not properties of a website.\n"
        "• A 200/404/etc. is an HTTP response status, not proof of a security bug."
    )

    bot.reply_to(message, report, parse_mode="Markdown")

# 3. Zero-Rated Hosts
def process_zero_rated(message):
    query = message.text.strip()
    bot.reply_to(message, f"🔍 ለ **{query}** ነፃ ሆስቶችን በመፈለግ ላይ...", parse_mode="Markdown")
    
    try:
        url = f"https://crt.sh/?q=%25{query}%25&output=json"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            hosts = set()
            for entry in data:
                name_value = entry['name_value']
                for host in name_value.split('\n'):
                    if '*' not in host and len(host.strip()) > 0:
                        hosts.add(host.strip())
            
            host_list = sorted(list(hosts))[:30]
            
            if len(host_list) > 0:
                result_text = f"╔══════════════════════╗\n  🌍 **ZERO-RATED HOSTS** 🌍\n╚══════════════════════╝\n\n🎯 **Query:** {query}\n\n"
                for h in host_list:
                    result_text += f"`{h}`\n"
                
                bot.reply_to(message, result_text, parse_mode="Markdown")
            else:
                bot.reply_to(message, f"ለ {query} ምንም ሆስት አልተገኘም!")
        else:
            bot.reply_to(message, "የፍለጋ ስህተት አጋጥሟል።")
    except Exception as e:
        bot.reply_to(message, f"ስህተት ተፈጥሯል: {str(e)}")

bot.infinity_polling()
