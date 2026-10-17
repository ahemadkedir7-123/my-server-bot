import os
import threading
import requests
import socket
import ssl
from flask import Flask
import telebot
from telebot import types

# 1. የቦት ቶከን
TOKEN = "8788982436:AAGRmbaKk7BAcht3QjOQtGdd0vsdLt3EqjI"  # 
bot = telebot.TeleBot(TOKEN)


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

# 4. ዋናውን ሜኑ (Inline Keyboard) ማሳያ ፋንክሽን
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌐 Subdomain Finder", callback_data="tool_subdomain"),
        types.InlineKeyboardButton("📡 Web Host Scanner", callback_data="tool_scanner"),
        types.InlineKeyboardButton("🔍 Domain & IP Recon", callback_data="tool_recon"),
        types.InlineKeyboardButton("ℹ️ Telegram User Info", callback_data="tool_userinfo"),
        types.InlineKeyboardButton("📞 Phone Metadata", callback_data="tool_phone"),
        types.InlineKeyboardButton("🖼️ Image Info", callback_data="tool_image"),
        types.InlineKeyboardButton("📢 PROMOTION MARKET", callback_data="tool_promo"),
        types.InlineKeyboardButton("🆘 Help / How to Use", callback_data="tool_help")
    )
    return markup

# 5. /start ትእዛዝ እና ቋሚ Menu Button ማዋቀር
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    # ቻናል ማረጋገጫ
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

    bot.send_message(
        chat_id, 
        "🛡️ **NetX Tools Pro Bot**\n\n"
        "💎 Paid credits: **0**\n"
        "⏳ Weekly access: **Yes**\n"
        "🎯 Referrals: **0**\n\n"
        "ማከናወን የሚፈልጉትን መሳሪያ ከታች ካሉት አማራጮች ይምረጡ፦",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# 6. የቁልፎች እና የመሳሪያዎች ስራ አስኪያጅ (Callback Handler)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "check_sub":
        if check_subscription(chat_id):
            bot.answer_callback_query(call.id, "✅ ማረጋገጫው ተሳክቷል!")
            try:
                bot.delete_message(chat_id, call.message.message_id)
            except:
                pass
            bot.send_message(
                chat_id, 
                "🎉 **እንኳን ደህና መጡ! NetX Tools ሙሉ በሙሉ ስራ ጀምሯል!**",
                reply_markup=get_main_menu(),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ እባክዎ በመጀመሪያ ቻናሎቹን ይቀላቀሉ!", show_alert=True)
            
    elif data == "tool_subdomain":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🌐 **Super Subdomain Finder**\n\nእባክዎ መቃኘት የሚፈልጉትን ዶሜይን ይላኩ (ለምሳሌ: `google.com`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_super_subdomain)

    elif data == "tool_scanner":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "📡 **Web Host Scanner**\n\nእባክዎ መቃኘት የሚፈልጉትን ሆስት ወይም ዶሜይን ይላኩ (ለምሳሌ: `example.com`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_web_scanner)

    elif data == "tool_recon":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(chat_id, "🔍 **Domain & IP Recon**\n\nእባክዎ የ IP አድራሻ ወይም ዶሜይን ይላኩ:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_ip_recon)

    elif data == "tool_userinfo":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "ℹ️ የእርስዎ የቴሌግራም መረጃ:\n\n- User ID: `{}`\n- Name: `{}`".format(chat_id, call.from_user.first_name), parse_mode="Markdown", reply_markup=get_main_menu())

    elif data == "tool_promo":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📢 **PROMOTION MARKET**\n\nማስታወቂያዎችን እና የቻናል እድገት ፕሮግራሞችን ለማግኘት አድሚኑን ያነጋግሩ: @Admin", reply_markup=get_main_menu(), parse_mode="Markdown")

    elif data == "tool_help":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🆘 **እርዳታ እና አጠቃቀም**\n\nይህ ቦት ንዑስ ዶሜኖች (Subdomains)፣ የሰርቨር ፖርቶች እና የአይፒ መረጃዎችን በፍጥነት እንዲያገኙ ይረዳል።", reply_markup=get_main_menu(), parse_mode="Markdown")

    else:
        bot.answer_callback_query(call.id, "⚠️ ይህ መሳሪያ በዝግጅት ላይ ነው!", show_alert=True)

# 7. 🌐 Subdomain Finder (Super Scan) Real Implementation
def process_super_subdomain(message):
    chat_id = message.chat.id
    query = message.text.strip()

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    processing_msg = bot.send_message(chat_id, f"🔍 **Super Scan** በ `{query}` ላይ በመካሄድ ላይ ነው...", parse_mode="Markdown")

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

            subdomain_list = sorted(list(subdomains))[:40]
            
            if subdomain_list:
                result_text = f"✅ **የተገኙ Super Scan ውጤቶች ({query}) [ጠቅላላ: {len(subdomain_list)}]:**\n\n" + "\n".join([f"<code>{s}</code>" for s in subdomain_list])
                bot.delete_message(chat_id, processing_msg.message_id)
                bot.send_message(chat_id, result_text, parse_mode="HTML", reply_markup=get_main_menu())
            else:
                bot.edit_message_text(f"⚠️ ለ `{query}` ምንም ንዑስ ዶሜይን አልተገኘም።", chat_id, processing_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ ከሰርቨሩ ጋር ግንኙነት መፍጠር አልተቻለም።", chat_id, processing_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል: {e}", chat_id, processing_msg.message_id)

# 8. 📡 Web Host Scanner Real Implementation
def process_web_scanner(message):
    chat_id = message.chat.id
    domain = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    processing_msg = bot.send_message(chat_id, f"📡 **Web Host Scan** በ `{domain}` ላይ በመካሄድ ላይ ነው...", parse_mode="Markdown")

    try:
        ip = socket.gethostbyname(domain)
        ports = [80, 443, 8080, 8443]
        open_ports = []

        for port in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            s.close()

        # HTTP Status Check
        http_status = "Unknown"
        try:
            r = requests.get(f"https://{domain}", timeout=5)
            http_status = str(r.status_code)
        except:
            try:
                r = requests.get(f"http://{domain}", timeout=5)
                http_status = str(r.status_code)
            except:
                http_status = "Connection Failed"

        report = (
            f"📡 **Web Host Scan Report for:** `{domain}`\n\n"
            f"🌐 **IP Address:** `{ip}`\n"
            f"🔓 **Open Ports:** `{open_ports if open_ports else 'None'}`\n"
            f"🌐 **HTTP Status:** `{http_status}`"
        )
        bot.delete_message(chat_id, processing_msg.message_id)
        bot.send_message(chat_id, report, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል ወይም ሆስቱ አልተገኘም: {e}", chat_id, processing_msg.message_id)

# 9. 🔍 Domain & IP Recon Real Implementation
def process_ip_recon(message):
    chat_id = message.chat.id
    target = message.text.strip().replace("https://", "").replace("http://", "").split("/")[0]

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    try:
        ip = socket.gethostbyname(target)
        api_url = f"http://ip-api.com/json/{ip}"
        res = requests.get(api_url, timeout=5).json()

        if res.get('status') == 'success':
            text = (
                f"🔍 **IP Recon Result:**\n\n"
                f"📌 **Target:** `{target}`\n"
                f"🌐 **IP:** `{ip}`\n"
                f"🌍 **Country:** `{res.get('country')}`\n"
                f"🏙️ **City:** `{res.get('city')}`\n"
                f"🏢 **ISP:** `{res.get('isp')}`"
            )
            bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=get_main_menu())
        else:
            bot.send_message(chat_id, f"⚠️ መረጃ ማግኘት አልተቻለም። IP: `{ip}`", parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        bot.send_message(chat_id, f"❌ ስህተት ተፈጥሯል: {e}", reply_markup=get_main_menu())

# 10. Flask Server for Render
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
