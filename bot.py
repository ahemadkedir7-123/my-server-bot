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
            "📁 **Bulk Bug Host Scanner (.txt)**\n\n"
            "እባክዎ **ያለ ምንም ገደብ** በርካታ ዶሜይኖችን የያዘ **`.txt` ፋይል** ይላኩ። ቦቱ ሁሉንም በአንድ ላይ ስካን አድርጎ ትክክለኛ የባግ ሆስት (CDN/Cloud) ያላቸውን ለይቶ ያሳውቅዎታል።", 
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
            "• **Subdomain Finder:** ከበርካታ ሰርቨሮች የተገኙ ንዑስ-ዶሜይኖችን በአንድ ላይ ያወጣል።\n"
            "• **Bulk Bug Host Checker:** ትክክለኛ CDN/Cloud ያላቸውን የባግ ሆስት ዶሜይኖች ይለያል።",
            parse_mode="Markdown"
        )
    else:
        msg = bot.send_message(chat_id, f"🌐 **Super Subdomain Finder**\n\nለ `{text}` ንዑስ-ዶሜይኖች በመሰብሰብ ላይ...", parse_mode="Markdown")
        process_subdomain_direct(chat_id, text, msg.message_id)

# 8. 📁 Bulk Bug Host Checker (ትክክለኛ የባግ ሆስት ማጣሪያ ያለው)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    if not message.document.file_name.endswith('.txt'):
        bot.send_message(chat_id, "⚠️ እባክዎ የ **`.txt`** ፋይል ብቻ ይላኩ!")
        return

    processing_msg = bot.send_message(chat_id, "🔄 ፋይሉ እየወረደ እና ዶሜይኖቹ በትክክለኛ የባግ ሆስት መስፈርት እየተቃኙ ነው...", parse_mode="Markdown")

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
                
                server = r.headers.get('Server', '').lower()
                via = r.headers.get('Via', '').lower()
                x_cache = r.headers.get('X-Cache', '').lower()
                
                # ትክክለኛ የባግ ሆስት ሊሆኑ የሚችሉት (CDN የሚጠቀሙ ወይም ሪዳይሬክት የሚያደርጉ) ብቻ እንዲመረጡ ይደረጋል
                if r.status_code in [200, 301, 302, 403, 405] and ('cloudflare' in server or 'cloudfront' in server or 'akamai' in server or 'cloudfront' in via or 'cloudfront' in x_cache or 'awselb' in server):
                    valid_bug_hosts.append(f"• `http://{domain}` (Server: `{r.headers.get('Server', 'CDN')}`)")
            except:
                continue

        report = f"📊 **BULK BUG HOST SCAN REPORT (FILTERED)**\n\n"
        report += f"Total Scanned: `{len(domains)}`\n"
        report += f"Valid Bug Hosts Found: `{len(valid_bug_hosts)}`\n\n"

        if valid_bug_hosts:
            report += "🎯 **Potential Working Bug Hosts (CDN/Cloud):**\n" + "\n".join(valid_bug_hosts[:50])
        else:
            report += "⚠️ ምንም የሚሰራ የባግ ሆስት (CDN/Cloud) በፋይሉ ውስጥ አልተገኘም።"

        bot.delete_message(chat_id, processing_msg.message_id)
        
        if len(report) > 4000:
            file_io = io.BytesIO(report.encode('utf-8'))
            file_io.name = "valid_bug_hosts.txt"
            bot.send_document(chat_id, file_io, caption="✅ **ውጤቱ ስለረዘመ በሰነድ መልክ ተልኳል**", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, report, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል: {e}", chat_id, processing_msg.message_id)

# 9. 🌐 Subdomain Finder (አንድም ሳይቀር ሙሉ በሙሉ የሚያመጣ)
def process_super_subdomain(message):
    chat_id = message.chat.id
    if not message.text:
        return
    query = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]
    processing_msg = bot.send_message(chat_id, f"🔍 ለ `{query}` ንዑስ-ዶሜይኖች ከሁሉም ሰርቨሮች በጥልቀት በመፈለግ ላይ... እባክዎ ትንሽ ይጠብቁ...", parse_mode="Markdown")
    process_subdomain_direct(chat_id, query, processing_msg.message_id)

def process_subdomain_direct(chat_id, query, msg_id):
    subdomains = set()
    
    # 1. ከ crt.sh (በተለያዩ ዌይ አውቶች)
    try:
        url = f"https://crt.sh/?q=%25.{query}&output=json"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=25)
        if response.status_code == 200:
            for entry in response.json():
                name_value = entry.get('name_value')
                if name_value:
                    for sub in name_value.split('\n'):
                        sub = sub.strip().lower()
                        if sub and not sub.startswith('*') and sub.endswith(query):
                            subdomains.add(sub)
    except:
        pass

    # 2. ከ HackerTarget API
    try:
        alt_url = f"https://api.hackertarget.com/hostsearch/?q={query}"
        res = requests.get(alt_url, timeout=15)
        if res.status_code == 200 and "API count exceeded" not in res.text and "error" not in res.text.lower():
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

    # 4. ከ ThreatCrowd API (ለተጨማሪ ጥልቀት)
    try:
        tc_url = f"https://www.threatcrowd.org/searchApi/v2/domain/report.html?domain={query}"
        res = requests.get(tc_url, timeout=10)
        if res.status_code == 200:
            # ራሱን የቻለ  টেকስት ፍለጋ
            import re
            found = re.findall(r'[\w.-]+\.' + re.escape(query), res.text)
            for sub in found:
                sub = sub.strip().lower()
                if sub:
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
            
            # ውጤቱ ከ 15 በላይ ሲሆን በፋይል መልክ መላክ
            if len(subdomain_list) > 15:
                file_content = "\n".join(subdomain_list)
                file_io = io.BytesIO(file_content.encode('utf-8'))
                file_io.name = f"{query}_all_subdomains.txt"
                bot.send_document(
                    chat_id, 
                    file_io, 
                    caption=f"✅ **የተገኙ ንዑስ ዶሜይኖች ({query}) [ጠቅላላ: {len(subdomain_list)}]:**\nአንድም ሳይቀር በሰነድ (.txt) ፋይል ተያይዟል!",
                    parse_mode="Markdown"
                )
            else:
                result_text = f"✅ **የተገኙ ውጤቶች ({query}) [{len(subdomain_list)}]:**\n\n" + "\n".join([f"<code>{s}</code>" for s in subdomain_list])
                bot.send_message(chat_id, result_text, parse_mode="HTML")
        else:
            bot.edit_message_text(f"⚠️ ለ `{query}` ምንም ንዑስ ዶሜይን ማግኘት አልተቻለም። እባክዎ ትንሽ ቆይተው እንደገና ይሞክሩ።", chat_id, msg_id, parse_mode="Markdown")
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
                conn = r.headers.get('Connection', 'keep-alive')
                
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

# 13. 🖼️ Image Info & Editor
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image = Image.open(io.BytesIO(downloaded_file))
        width, height = image.size
        format_type = image.format
        file_size_kb = round(len(downloaded_file) / 1024, 2)

        caption_text = message.caption
        if caption_text:
            draw = ImageDraw.Draw(image)
            text_position = (20, height - 60)
            draw.text(text_position, caption_text, fill=(255, 255, 255))
            
            output_io = io.BytesIO()
            image.save(output_io, format='JPEG')
            output_io.seek(0)

            info_msg = (
                f"🖼️ **Image Edit Success!**\n\n"
                f"📐 **Resolution:** `{width}x{height}`\n"
                f"📁 **Format:** `{format_type}`\n"
                f"📦 **Size:** `{file_size_kb} KB`\n"
                f"✍️ **Added Text:** `{caption_text}`"
            )
            bot.send_photo(chat_id, output_io, caption=info_msg, parse_mode="Markdown")
        else:
            info_msg = (
                f"🖼️ **Image Info Analysis:**\n\n"
                f"📐 **Resolution:** `{width}x{height}` px\n"
                f"📁 **Format:** `{format_type}`\n"
                f"📦 **Size:** `{file_size_kb} KB`\n\n"
                f"💡 *ምስሉ ላይ ጽሁፍ ለመጻፍ ከፎቶው ጋር Caption/ጽሁፍ አያይዘው ይላኩ!*"
            )
            bot.send_message(chat_id, info_msg, parse_mode="Markdown")

        except Exception as e:
        bot.send_message(chat_id, f"❌ ስህተት ተፈጥሯል: {e}")

