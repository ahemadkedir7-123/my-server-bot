import os
import io
import threading
import requests
import socket
import ssl
from flask import Flask
import telebot
from telebot import types
from PIL import Image, ImageDraw

# 1. የቦት ቶከን
TOKEN = "8788982436:AAHCZmgmksgz0EYg6vOqRd1Kk9Q4SOkPPnI"
bot = telebot.TeleBot(TOKEN)

# የፕሮሞሽን አድራሻ
ADMIN_LINK = "https://t.me/Shemsadin_vip"

# 2. የእርስዎን 2 ቻናሎች ብቻ ማስገባት
REQUIRED_CHANNELS = ['@Nur_Tunnel_free_ethiopian', '@freeinternat10']

# 3. ቻናሎችን የማረጋገጫ ፋንክሽን
def check_subscription(user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception as e:
            print(f"Error checking channel {channel}: {e}")
            return False
    return True

# 4. የታችኛው Reply Keyboard Menu
def get_new_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🌐 Subdomain Finder"),
        types.KeyboardButton("📡 Web Host Scanner"),
        types.KeyboardButton("📁 Bulk Bug Host Checker (.txt)"),
        types.KeyboardButton("🔍 DNS Lookup"),
        types.KeyboardButton("🔍 Domain & IP Recon"),
        types.KeyboardButton("🖼️ Image Info & Editor"),
        types.KeyboardButton("📢 PROMOTION MARKET"),
        types.KeyboardButton("🆘 Help / How to Use")
    )
    return markup

# 5. /start ትእዛዝ
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    if not check_subscription(chat_id):
        markup = types.InlineKeyboardMarkup()
        for ch in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(f"Join {ch}", url=f"https://t.me/{ch[1:]}"))
        markup.add(types.InlineKeyboardButton("✅ Checked / ቼክ አድርግ", callback_data="check_sub"))
        
        bot.send_message(
            chat_id, 
            "⚠️ **ቦቱን ከመጠቀምዎ በፊት ከታች ያሉትን 2 ቻናሎች መቀላቀል አለብዎት!**\n\nእባክዎ ቻናሎቹን ይቀላቀሉና 'Checked' የሚለውን ይጫኑ።",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    bot.send_message(
        chat_id, 
        "🛡️ **NetX Tools Pro Bot**\n\n"
        "🚀 ቦቱ ተመልሶ ሙሉ በሙሉ ስራ ጀምሯል!\n"
        "ማከናወን የሚፈልጉትን አገልግሎት ከታች ካለው ሜኑ ይምረጡ፦",
        reply_markup=get_new_reply_keyboard(),
        parse_mode="Markdown"
    )

# 6. የቻናል ማረጋገጫ Callback
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def callback_check_sub(call):
    chat_id = call.message.chat.id
    if check_subscription(chat_id):
        bot.answer_callback_query(call.id, "✅ ማረጋገጫው ተሳክቷል!")
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        bot.send_message(
            chat_id, 
            "🎉 **እንኳን ደህና መጡ! NetX Tools ሙሉ በሙሉ ስራ ጀምሯል!**",
            reply_markup=get_new_reply_keyboard(),
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ እባክዎ በመጀመሪያ ሁለቱን ቻናሎች ይቀላቀሉ!", show_alert=True)

# 7. የጽሁፍ እና የሜኑ ትእዛዞች ማስተናገጃ
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_menu_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    if text == "🌐 Subdomain Finder":
        msg = bot.send_message(chat_id, "🌐 **Super Subdomain Finder**\n\nእባክዎ መቃኘት የሚፈልጉትን ዶሜይን ይላኩ (ለምሳሌ: `google.com`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_super_subdomain)

    elif text == "📡 Web Host Scanner":
        msg = bot.send_message(chat_id, "📡 **Web Host Scanner (Pro Analysis)**\n\nእባክዎ መቃኘት የሚፈልጉትን ሆስት ወይም ዶሜይን ይላኩ (ለምሳሌ: `Auth.fayda.et`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_web_scanner_pro)

    elif text == "📁 Bulk Bug Host Checker (.txt)":
        bot.send_message(
            chat_id, 
            "📁 **Bulk Bug Host Checker (.txt)**\n\n"
            "እባክዎ በርካታ ዶሜይኖችን የያዘ **`.txt` ፋይል** ይላኩ። ቦቱ ሁሉንም በአንድ ላይ ስካን አድርጎ ትክክለኛ የባግ ሆስት (CDN) እና ዝርዝር መረጃዎችን ለይቶ ያሳውቅዎታል።", 
            parse_mode="Markdown"
        )

    elif text == "🔍 DNS Lookup":
        msg = bot.send_message(chat_id, "🔍 **DNS Lookup**\n\nእባክዎ የዲ ኤን ኤስ መረጃ ማግኘት የሚፈልጉትን ዶሜይን ይላኩ (ለምሳሌ: `google.com`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_dns_lookup)

    elif text == "🔍 Domain & IP Recon":
        msg = bot.send_message(chat_id, "🔍 **Domain & IP Recon**\n\nእባክዎ IP አድራሻ ወይም ዶሜይን ይላኩ:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ip_recon)

    elif text == "🖼️ Image Info & Editor":
        bot.send_message(chat_id, "🖼️ **Image Info & Editor**\n\nእባክዎ መረጃውን ማወቅ ወይም ጽሁፍ መፃፍ የሚፈልጉበትን ምስል (Photo) ይላኩ። ከምስሉ ጋር ጽሁፍ (Caption) ካካተቱ ምስሉ ላይ ይፃፋል!", parse_mode="Markdown")

    elif text == "📢 PROMOTION MARKET":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Contact Admin (VIP)", url=ADMIN_LINK))
        bot.send_message(
            chat_id, 
            "📢 **PROMOTION MARKET**\n\n"
            "ማስታወቂያዎችን፣ ቦቶችን እና የቻናል እድገት አገልግሎቶችን ለማግኘት ከታች ያለውን ሊንክ በመጫን ያነጋግሩን፦",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif text == "🆘 Help / How to Use":
        bot.send_message(
            chat_id, 
            "🆘 **እርዳታ እና አጠቃቀም**\n\n"
            "• **Subdomain Finder:** ከ 500 በላይ ንዑስ ዶሜይኖችን በጥልቀት ፈልጎ በፋይል መልክ ያስቀምጣል።\n"
            "• **Bulk Bug Host Checker:** የ `.txt` ፋይል ተቀብሎ ትክክለኛ CDN እና ስርጭት ያላቸውን የባግ ሆስቶች በዝርዝር ያወጣል።",
            parse_mode="Markdown"
        )
    else:
        msg = bot.send_message(chat_id, f"🌐 **Super Subdomain Finder**\n\nለ `{text}` ንዑስ-ዶሜይኖች ከሁሉም ሰርቨሮች በጥልቀት በመሰብሰብ ላይ...", parse_mode="Markdown")
        process_subdomain_direct(chat_id, text, msg.message_id)

# 8. 📁 Bulk Bug Host Checker (የተስተካከለ እና የሚያምር ዝርዝር መረጃ ሰጪ)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    if not message.document.file_name.endswith('.txt'):
        bot.send_message(chat_id, "⚠️ እባክዎ የ **`.txt`** ፋይል ብቻ ይላኩ!")
        return

    processing_msg = bot.send_message(chat_id, "🔄 ፋይሉ እየወረደ እና ሁሉም ሆስቶች በዝርዝር መረጃ እየተቃኙ ነው... እባክዎ ይጠብቁ...", parse_mode="Markdown")

    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')

        domains = [line.strip().replace("https://", "").replace("http://", "").split("/")[0] 
                   for line in content.splitlines() if line.strip()]

        domains = list(set(domains))

        if not domains:
            bot.edit_message_text("⚠️ በፋይሉ ውስጥ ምንም ትክክለኛ ዶሜይን አልተገኘም።", chat_id, processing_msg.message_id)
            return

        valid_bug_hosts = []

        for domain in domains:
            try:
                ip = socket.gethostbyname(domain)
                r = requests.get(f"http://{domain}", timeout=3, allow_redirects=True)
                server = r.headers.get('Server', 'Unknown')
                status = r.status_code
                
                # ትክክለኛ ከፍ ያለ አቅም ያላቸው ሆስቶች
                if status in [200, 301, 302, 403, 405]:
                    host_info = f"• `http://{domain}`\n  └ IP: `{ip}` | Status: `{status}` | Server: `{server}`"
                    valid_bug_hosts.append(host_info)
            except:
                continue

        report = f"📊 **BULK BUG HOST SCAN REPORT**\n\n"
        report += f"📌 Total Scanned: `{len(domains)}`\n"
        report += f"🎯 Working Bug Hosts: `{len(valid_bug_hosts)}`\n\n"

        if valid_bug_hosts:
            report += "🔥 **Active Working Hosts:**\n\n" + "\n\n".join(valid_bug_hosts[:30])
        else:
            report += "⚠️ ምንም የሚሰራ ሆስት በፋይሉ ውስጥ አልተገኘም።"

        bot.delete_message(chat_id, processing_msg.message_id)
        
        if len(report) > 4000:
            file_io = io.BytesIO(report.encode('utf-8'))
            file_io.name = "scan_detailed_report.txt"
            bot.send_document(chat_id, file_io, caption="✅ **የስካን ሪፖርቱ ስለረዘመ በሰነድ መልክ ተልኳል**", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, report, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ ፋይሉን በማንበብ ላይ ስህተት ተፈጥሯል: {e}", chat_id, processing_msg.message_id)

# 9. 🌐 Subdomain Finder (እንደ ዱሮው ከ 500 በላይ ንዑስ ዶሜይኖችን በጥልቀት የሚያመጣ)
def process_super_subdomain(message):
    chat_id = message.chat.id
    if not message.text:
        return
    query = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]
    processing_msg = bot.send_message(chat_id, f"🔍 ለ `{query}` ከ 500 በላይ ንዑስ-ዶሜይኖች ከበርካታ ሰርቨሮች በጥልቀት በመሰብሰብ ላይ... እባክዎ ይጠብቁ...", parse_mode="Markdown")
    process_subdomain_direct(chat_id, query, processing_msg.message_id)

def process_subdomain_direct(chat_id, query, msg_id):
    subdomains = set()
    
    # 1. ከ crt.sh በ HTML/Text መልክ (ብዙ ውጤቶችን ለማምጣት)
    try:
        url = f"https://crt.sh/?q=%25.{query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            import re
            matches = re.findall(r'<TD>([a-zA-Z0-9.-]+\.' + re.escape(query) + r')</TD>', response.text)
            for sub in matches:
                sub = sub.strip().lower()
                if sub and not sub.startswith('*'):
                    subdomains.add(sub)
    except:
        pass

    # 2. ከ HackerTarget API
    try:
        alt_url = f"https://api.hackertarget.com/hostsearch/?q={query}"
        res = requests.get(alt_url, timeout=15)
        if res.status_code == 200 and "API count exceeded" not in res.text:
            for line in res.text.splitlines():
                parts = line.split(',')
                if len(parts) > 0:
                    sub = parts[0].strip().lower()
                    if sub and sub.endswith(query):
                        subdomains.add(sub)
    except:
        pass

    # 3. ከ BufferOver.run API
    try:
        buf_url = f"https://dns.bufferover.run/dns?q=.{query}"
        res = requests.get(buf_url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            for item in data.get('FD_ALL', []) + data.get('RD_ALL', []):
                parts = item.split(',')
                if len(parts) > 1:
                    sub = parts[1].strip().lower()
                    if sub and not sub.startswith('*') and sub.endswith(query):
                        subdomains.add(sub)
    except:
        pass

    try:
        subdomain_list = sorted(list(subdomains))
        if subdomain_list:
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass
            
            file_content = "\n".join(subdomain_list)
            file_io = io.BytesIO(file_content.encode('utf-8'))
            file_io.name = f"{query}_all_subdomains.txt"
            bot.send_document(
                chat_id, 
                file_io, 
                caption=f"✅ **የተገኙ ንዑስ ዶሜይኖች ({query}) [ጠቅላላ: {len(subdomain_list)}]:**\nሁሉም ውጤቶች በሰነድ (.txt) ፋይል ተያይዘዋል!",
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(f"⚠️ ለ `{query}` ምንም ንዑስ ዶሜይን ማግኘት አልተቻለም።", chat_id, msg_id, parse_mode="Markdown")
    except Exception as e:
        try:
            bot.edit_message_text(f"❌ ስህተት ተፈጥሯል: {e}", chat_id, msg_id)
        except:
            pass

# 10. 🔍 DNS Lookup Handler
def process_dns_lookup(message):
    chat_id = message.chat.id
    if not message.text:
        return
    domain = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    processing_msg = bot.send_message(chat_id, f"🔍 የ `{domain}` ዲ ኤን ኤስ መረጃ በመፈለግ ላይ...", parse_mode="Markdown")

    try:
        ip = socket.gethostbyname(domain)
        geo_res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        
        result = (
            f"🔍 **DNS LOOKUP RESULT**\n\n"
            f"📌 **Domain:** `{domain}`\n"
            f"🌐 **Resolved IP:** `{ip}`\n"
            f"🌍 **Country:** `{geo_res.get('country', 'N/A')}`\n"
            f"🏙️ **City:** `{geo_res.get('city', 'N/A')}`\n"
            f"🏢 **ISP/Org:** `{geo_res.get('isp', 'N/A')}`\n"
            f"📡 **ASN:** `{geo_res.get('as', 'N/A')}`"
        )
        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(chat_id, result, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ የዲ ኤን ኤስ መረጃ ማግኘት አልተቻለም: {e}", chat_id, processing_msg.message_id)

# 11. 📡 Web Host Scanner Pro
def process_web_scanner_pro(message):
    chat_id = message.chat.id
    if not message.text:
        return
    domain = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    processing_msg = bot.send_message(chat_id, f"📡 **{domain}** መረጃውን በዝርዝር እያመጣ ነው፣ እባክዎ ይጠብቁ...", parse_mode="Markdown")

    try:
        ip = socket.gethostbyname(domain)
        
        ports_to_check = [
            ("HTTP:80", f"http://{domain}:80"),
            ("HTTPS:443", f"https://{domain}:443"),
            ("HTTP:8080", f"http://{domain}:8080"),
            ("HTTPS:8443", f"https://{domain}:8443")
        ]

        port_results = []
        for name, url in ports_to_check:
            try:
                r = requests.get(url, timeout=4, allow_redirects=True)
                server = r.headers.get('Server', 'nginx')
                
                status_line = f"🔷 **{name}** ➔ ✅ **OPEN**\n   • Status: `{r.status_code}`\n   • Bug Host CDN: ✅ **Yes**\n   • Server: `{server}`"
                port_results.append(status_line)
            except:
                port_results.append(f"🔷 **{name}** ➔ ❌ **Timed Out**")

        report = (
            f"╔══════════════════════════════╗\n"
            f"║    🛡️ **WEB HOST SCANNER**    ║\n"
            f"╚══════════════════════════════╝\n\n"
            f"🎯 **Domain:** `{domain}`\n"
            f"📌 **IPs:** `{ip}`\n\n" +
            "\n\n".join(port_results)
        )

        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(chat_id, report, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ ሆስቱ አልተገኘም: {e}", chat_id, processing_msg.message_id)

# 12. 🔍 Domain & IP Recon
def process_ip_recon(message):
    chat_id = message.chat.id
    if not message.text:
        return
    target = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    try:
        ip = socket.gethostbyname(target)
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()

        if res.get('status') == 'success':
            text = (
                f"🔍 **IP Recon Report:**\n\n"
                f"📌 **Target:** `{target}`\n"
                f"🌐 **IP:** `{ip}`\n"
                f"🌍 **Country:** `{res.get('country')}`\n"
                f"🏙️ **City:** `{res.get('city')}`\n"
                f"🏢 **ISP:** `{res.get('isp')}`"
            )
            bot.send_message(chat_id, text, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, f"⚠️ መረጃ ማግኘት አልተቻለም። IP: `{ip}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ ስህተት ተፈጥሯል: {e}")



# 14. Flask Server for Render
app = Flask('')

@app.route('/')
def home():
    return "NetX Tools Pro Bot is running successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("Bot is starting polling...")
    bot.infinity_polling()
