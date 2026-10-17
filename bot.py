import os
import telebot
import requests
import socket
import ssl
from urllib.parse import urlparse
from cryptography import x509
from cryptography.hazmat.backends import default_backend

TOKEN = os.getenv('8788982436:AAGRmbaKk7BAcht3QjOQtGdd0vsdLt3EqjI')
bot = telebot.TeleBot(TOKEN)

# የእርስዎ ሁለቱ ቻናሎች ዩዘርናም (እባክዎ @ በሚለው ይጻፉ)
CHANNEL_1 = "@Nur_Tunnel_free_ethiopian"
CHANNEL_2 = "@freeinternat10"

# ተጠቃሚው ሁለቱንም ቻናሎች ጆይን አድርጎ እንደሆነ የሚያረጋግጥ ተግባር
def check_subscription(user_id):
    try:
        # የመጀመሪያውን ቻናል ማረጋገጥ
        member1 = bot.get_chat_member(CHANNEL_1, user_id)
        is_sub1 = member1.status in ['creator', 'administrator', 'member']
        
        # ሁለተኛውን ቻናል ማረጋገጥ
        member2 = bot.get_chat_member(CHANNEL_2, user_id)
        is_sub2 = member2.status in ['creator', 'administrator', 'member']
        
        return is_sub1 and is_sub2
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False

# ቻናሎቹን ጆይን እንድያደርጉ የሚጠይቅ ቆንጆ ንድፍ (Layout) ያለው የቁልፍ ሰሌዳ
def join_channels_markup():
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    btn1 = telebot.types.InlineKeyboardButton("📢 1ኛውን ቻናል ጆይን ያድርጉ", url="https://t.me/Nur_Tunnel_free_ethiopian")
    btn2 = telebot.types.InlineKeyboardButton("📢 2ኛውን ቻናል ጆይን ያድርጉ", url="https://t.me/freeinternat10")
    check_btn = telebot.types.InlineKeyboardButton("✅ ጆይን አድርጌአለሁ (Verify)", callback_data="check_join")
    markup.add(btn1, btn2, check_btn)
    return markup

# ዋናውን የቁልፍ ሰሌዳ (Menu Buttons) መፍጠር
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
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        welcome_text = (
            "╔════════════════════════╗\n"
            "  ⚠️ **ቻናሎቹን መቀላቀል ይኖርብዎታል!** ⚠️\n"
            "╚════════════════════════╝\n\n"
            "ይህንን ቦት በነፃ ለመጠቀም እባክዎ ከታች ያሉትን ሁለቱን ኦፊሻል ቻናሎች ይቀላቀሉ (Join ያድርጉ)፤ ከዚያም **Verify** የሚለውን ይጫኑ!"
        )
        bot.reply_to(message, welcome_text, reply_markup=join_channels_markup(), parse_mode="Markdown")
        return

    bot.reply_to(
        message, 
        "╔══════════════════════╗\n  🌐 **MY SERVER BOT** 🌐\n╚══════════════════════╝\n\nእባክዎ ከታች ከሚገኙት አማራጮች የሚፈልጉትን ይምረጡ:", 
        reply_markup=main_menu(), 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ እናመሰግናለን! ሁለቱንም ቻናሎች ጆይን አድርገዋል አሁን ቦቱን መጠቀም ይችላሉ።")
        bot.send_message(
            call.message.chat.id, 
            "╔══════════════════════╗\n  🌐 **MY SERVER BOT** 🌐\n╚══════════════════════╝\n\nእባክዎ ከታች ከሚገኙት አማራጮች የሚፈልጉትን ይምረጡ:", 
            reply_markup=main_menu(), 
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ እስካሁን ሁለቱንም ቻናሎች ጆይን አላደረጉም! እባክዎ በመጀመሪያ ጆይን ይበሉ።", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        bot.reply_to(message, "⚠️ ቦቱን ለመቀጠል መጀመሪያ ሁለቱንም ቻናሎች ጆይን ማድረግ አለብዎት!", reply_markup=join_channels_markup())
        return

    text = message.text
    
    if text == '🌐 Subdomain Finder':
        msg = bot.reply_to(message, "🌐 **SUBDOMAIN FINDER**\n\nሰብ-ዶሜይኖች (Subdomains) መፈለግ የሚፈልጉትን ዋና ዶሜይን በመጻፍ ይላኩ (ለምሳሌ: safaricom.et):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_subdomain)
        
    elif text == '🔍 Host Scanner':
        msg = bot.reply_to(message, "🔍 **HOST SCANNER**\n\nማቃኘት የሚፈልጉትን ሆስት ወይም ዌብሳይት ሊንክ ያስገቡ (ለምሳሌ: google.com):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_host_scanner)
        
    elif text == '🌍 Zero-Rated Hosts':
        msg = bot.reply_to(message, "🌍 **ZERO-RATED HOSTS FINDER**\n\nነፃ ሆስቶችን (Zero-Rated Hosts) መፈለግ የሚፈልጉትን የሀገር ኮድ ወይም ዶሜይን (ለምሳሌ: .et) በመጻፍ ይላኩ:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_zero_rated)
        
    elif text == '🔑 SSH Account':
        bot.reply_to(message, "🔑 **SSH Account** ማስተካከያዎች እና አዲስ አካውንት መፍጠሪያ ዝርዝሮች እዚህ ይገኛሉ።", parse_mode="Markdown")
        
    elif text == '🚀 VLESS Config':
        bot.reply_to(message, "🚀 **VLESS Config** አዳዲስ እና ነፃ የ VLESS ማስተካከያዎች።", parse_mode="Markdown")
        
    elif text == '⚡ VMess Config':
        bot.reply_to(message, "⚡ **VMess Config** አዳዲስ የ VMess ማስተካከያዎች።", parse_mode="Markdown")
        
    else:
        bot.reply_to(message, "እባክዎ ከታች ያሉትን አዝራሮች (Buttons) ይጠቀሙ።", reply_markup=main_menu())

# Subdomain Finder
def process_subdomain(message):
    domain = message.text.strip()
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
                
                caption = f"╔══════════════════════╗\n  🌐 **SUBDOMAIN FINDER** 🌐\n╚══════════════════════╝\n\n🎯 **Target:** {domain}\n📊 **Total Found:** {total_found}\n\nየተገኙት ሰብ-ዶሜይኖች ፋይሉ ውስጥ ተያይዘዋል! 📁"
                
                with open(file_name, "rb") as f:
                    bot.send_document(message.chat.id, f, caption=caption, parse_mode="Markdown")
                
                os.remove(file_name)
            else:
                bot.reply_to(message, f"ለ {domain} ምንም ሰብ-ዶሜይን አልተገኘም!")
        else:
            bot.reply_to(message, "የፍለጋ ስህተት አጋጥሟል።")
    except Exception as e:
        bot.reply_to(message, f"ስህተት ተፈጥሯል: {str(e)}")

# Host Scanner
def process_host_scanner(message):
    target = message.text.strip().replace("http://", "").replace("https://", "").split("/")[0]
    bot.reply_to(message, f"🔍 **{target}** ሆስት በመቃኘት ላይ (HTTP & TLS Info)...", parse_mode="Markdown")
    
    report = f"╔══════════════════════╗\n  🔍 **HOST SCAN REPORT** 🔍\n╚══════════════════════╝\n\n🎯 **Target:** `{target}`\n\n"
    
    try:
        ip_addr = socket.gethostbyname(target)
        report += f"🌐 **IP Address:** `{ip_addr}`\n"
    except Exception:
        report += f"🌐 **IP Address:** ማግኘት አልተቻለም\n"

    try:
        resp = requests.get(f"https://{target}", timeout=8)
        report += f"🟢 **Status Code:** `{resp.status_code}`\n"
        report += f"🔒 **HTTPS / SSL:** `Enabled (Secure)`\n"
        server_header = resp.headers.get('Server', 'አልታወቀም')
        report += f"⚙️ **Server Header:** `{server_header}`\n"
    except Exception:
        try:
            resp = requests.get(f"http://{target}", timeout=8)
            report += f"🟡 **Status Code:** `{resp.status_code}`\n"
            report += f"🔓 **HTTPS / SSL:** `Not Secure (HTTP only)`\n"
        except Exception:
            report += f"❌ **HTTP Connection:** አልተሳካም\n"

    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((target, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=target) as ssock:
                cert_bin = ssock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(cert_bin, default_backend())
                
                issuer = cert.issuer.rfc451_string()
                not_before = cert.not_valid_before.strftime('%Y-%m-%d')
                not_after = cert.not_valid_after.strftime('%Y-%m-%d')
                
                report += f"\n📜 **TLS / SSL Certificate Info:**\n"
                report += f"• **Issuer:** `{issuer}`\n"
                report += f"• **Valid From:** `{not_before}`\n"
                report += f"• **Valid Until:** `{not_after}`\n"
    except Exception:
        report += f"\n⚠️ **TLS / SSL Info:** ሰርቲፊኬት ማንበብ አልተቻለም ወይም ፖርት 443 ዝግ ነው።\n"

    bot.reply_to(message, report, parse_mode="Markdown")

# Zero-Rated Hosts
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
