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
TOKEN = "8788982436:AAGRmbaKk7BAcht3QjOQtGdd0vsdLt3EqjI"  # 
bot = telebot.TeleBot(TOKEN)

# የፕሮሞሽን አድራሻ
ADMIN_LINK = "https://t.me/Shemsadin_vip"

# 2. ማስገደድ የሚፈለጉባቸው ቻናሎች
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

# 4. አዲሱ የታችኛው Reply Keyboard Menu (የድሮውን የሚተካ)
def get_new_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🌐 Subdomain Finder"),
        types.KeyboardButton("📡 Web Host Scanner"),
        types.KeyboardButton("🔍 Domain & IP Recon"),
        types.KeyboardButton("🖼️ Image Info & Editor"),
        types.KeyboardButton("📢 PROMOTION MARKET"),
        types.KeyboardButton("🆘 Help / How to Use")
    )
    return markup

# 5. /start ትእዛዝ (የድሮውን ቁልፎች አጥፍቶ አዲሱን ማስገቢያ)
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
            "⚠️ **ቦቱን ከመጠቀምዎ በፊት ከታች ያሉትን ቻናሎች መቀላቀል አለብዎት!**\n\nእባክዎ ቻናሎቹን ይቀላቀሉና 'Checked' የሚለውን ይጫኑ።",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    # የድሮው ቁልፎች እንዲጠፉ አዲሱን Menu ማስገባት
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
        bot.answer_callback_query(call.id, "❌ እባክዎ በመጀመሪያ ቻናሎቹን ይቀላቀሉ!", show_alert=True)

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
        msg = bot.send_message(chat_id, "📡 **Web Host Scanner (Deep Analysis)**\n\nእባክዎ መቃኘት የሚፈልጉትን ሆስት ወይም ዶሜይን ይላኩ (ለምሳሌ: `ethiotelecom.et`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_web_scanner_deep)

    elif text == "🔍 Domain & IP Recon":
        msg = bot.send_message(chat_id, "🔍 **Domain & IP Recon**\n\nእባክዎ IP አድራሻ ወይም ዶሜይን ይላኩ:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ip_recon)

    elif text == "🖼️ Image Info & Editor":
        bot.send_message(chat_id, "🖼️ **Image Info & Editor**\n\nእባክዎ መረጃውን ማወቅ ወይም ጽሁፍ መፃፍ የሚፈልጉበትን ምስል (Photo) ይላኩ። ከምስሉ ጋር ጽሁፍ (Caption) ካካተቱ ምስሉ ላይ ይፃፋል!", parse_mode="Markdown")

    elif text in ["📢 PROMOTION MARKET", "Promotion market"]:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💬 Contact Admin", url=ADMIN_LINK))
        bot.send_message(
            chat_id, 
            f"📢 **PROMOTION MARKET**\n\n"
            f"ማስታወቂያዎችን፣ ቦቶችን እና የቻናል እድገት አገልግሎቶችን ለማግኘት ከታች ያለውን ቁልፍ በመጫን ያነጋግሩ፦\n\n"
            f"👤 **Admin Link:** {ADMIN_LINK}",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif text == "🆘 Help / How to Use":
        bot.send_message(
            chat_id, 
            "🆘 **እርዳታ እና አጠቃቀም**\n\n"
            "• **Subdomain Finder:** የድረ-ገፆችን ንዑስ ዶሜይኖች ይፈልጋል።\n"
            "• **Web Host Scanner:** የሆስቱን የፖርቶች ሁኔታ (HTTP/HTTPS)፣ IP Network እና Transport notes ዝርዝር ይሰጣል።\n"
            "• **Image Info & Editor:** የፎቶ መረጃዎችን ያወጣል፤ ጽሁፍም ይጽፋል።",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(chat_id, "እባክዎ ከታች ካለው ሜኑ ውስጥ አንዱን ይምረጡ።", reply_markup=get_new_reply_keyboard())

# 8. 🌐 Subdomain Finder
def process_super_subdomain(message):
    chat_id = message.chat.id
    if not message.text:
        return
    query = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    processing_msg = bot.send_message(chat_id, f"🔍 ለ `{query}` ንዑስ-ዶሜይኖች በመሰብሰብ ላይ...", parse_mode="Markdown")

    try:
        url = f"https://crt.sh/?q=%25.{query}&output=json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            subdomains = set()
            for entry in data:
                name_value = entry.get('name_value')
                if name_value:
                    for sub in name_value.split('\n'):
                        sub = sub.strip()
                        if sub and not sub.startswith('*'):
                            subdomains.add(sub)

            subdomain_list = sorted(list(subdomains))[:35]
            
            if subdomain_list:
                result_text = f"✅ **Super Scan ውጤቶች ({query}) [{len(subdomain_list)}]:**\n\n" + "\n".join([f"<code>{s}</code>" for s in subdomain_list])
                bot.delete_message(chat_id, processing_msg.message_id)
                bot.send_message(chat_id, result_text, parse_mode="HTML")
            else:
                bot.edit_message_text(f"⚠️ ለ `{query}` ምንም ንዑስ ዶሜይን አልተገኘም።", chat_id, processing_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ ከሰርቨሩ ጋር ግንኙነት መፍጠር አልተቻለም።", chat_id, processing_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል: {e}", chat_id, processing_msg.message_id)

# 9. 📡 Web Host Scanner Deep Analysis (በምስል 2 መሰረት የቀረበ)
def process_web_scanner_deep(message):
    chat_id = message.chat.id
    if not message.text:
        return
    domain = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    processing_msg = bot.send_message(chat_id, f"📡 ለ `{domain}` ሙሉ የሆስት ዳሰሳ በማካሄድ ላይ...", parse_mode="Markdown")

    try:
        # IP Resolution
        ip = socket.gethostbyname(domain)
        
        # IP Network Info (Geo IP)
        net_info = "Unknown"
        try:
            geo_res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
            if geo_res.get('status') == 'success':
                net_info = f"{geo_res.get('country')} / {geo_res.get('city')} / {geo_res.get('isp')} / {geo_res.get('as')}"
        except:
            pass

        # Check Specific Ports
        ports_to_check = [
            ("HTTP:80", f"http://{domain}:80"),
            ("HTTPS:443", f"https://{domain}:443"),
            ("HTTP:8080", f"http://{domain}:8080"),
            ("HTTPS:8443", f"https://{domain}:8443")
        ]

        port_results = []
        for name, url in ports_to_check:
            try:
                r = requests.get(url, timeout=4, verify=True)
                port_results.append(f"🔌 **{name}** ➔ <code>{r.status_code} {r.reason}</code>")
            except requests.exceptions.SSLError as ssl_err:
                port_results.append(f"🔌 **{name}** ➔ ❌ no HTTP response\n`[SSL: CERTIFICATE_VERIFY_FAILED]`")
            except requests.exceptions.Timeout:
                port_results.append(f"🔌 **{name}** ➔ ❌ no HTTP response\n`timed out`")
            except Exception as e:
                port_results.append(f"🔌 **{name}** ➔ ❌ no HTTP response\n`connection failed`")

        report = (
            f"📡 **Web Host Scanner:** `{domain}`\n\n"
            f"📍 **IPs:** `{ip}`\n"
            f"🔌 **Ports checked:** 80, 443, 8080, 8443\n\n" +
            "\n\n".join(port_results) +
            f"\n\n🌍 **IP network info**\n`{ip}`: {net_info}\n\n"
            f"🧭 **Transport notes**\n"
            f"• Zero-rating cannot be proven from public HTTP/DNS data; it depends on carrier billing policy and network context.\n"
            f"• VPN/proxy/Xray are transport tools, not properties of a website. Use them only on networks/services you are authorized to use.\n"
            f"• A 200/404/etc. is an HTTP response status, not proof of a security bug."
        )

        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(chat_id, report, parse_mode="Markdown")

    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል (ሆስቱ አልተገኘም): {e}", chat_id, processing_msg.message_id)

# 10. 🔍 Domain & IP Recon
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

# 11. 🖼️ Image Info & Editor
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    if not check_subscription(chat_id):
        send_welcome(message)
        return

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
        bot.send_message(chat_id, f"❌ የምስል ስህተት: {e}")

# 12. Flask Server for Render
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
