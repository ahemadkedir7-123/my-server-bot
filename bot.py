import os
import threading
import requests
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

# 4. ዋናውን ሜኑ (ቁልፎች) ማሳያ ፋንክሽን
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
        "ማከናወን የሚፈልጉትን መሳሪያ ከታች ባሉት ቁልፎች ይምረጡ፦",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# 6. የኢንላይን ቁልፎች እና ሜኑ አስተዳዳሪ
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "check_sub":
        if check_subscription(chat_id):
            bot.answer_callback_query(call.id, "✅ ማረጋገጫው ተሳክቷል!")
            bot.delete_message(chat_id, call.message.message_id)
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
        msg = bot.send_message(chat_id, "🌐 **Super Subdomain Finder**\n\nእባክዎ መቃኘት የሚፈልጉትን ዶሜይን ይላኩ (ለምሳሌ: `google.com` ወይም `telegram.org`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_super_subdomain)

    elif data == "tool_scanner":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "📡 **Web Host Scanner**\n\nይህ መሳሪያ የድር ሰርቨሮችን ፖርቶች እና ኤችቲቲፒ ስተተስ ይቃኛል (በቅርብ ቀን ሙሉ ስራ ይጀምራል)።", reply_markup=get_main_menu())

    elif data == "tool_help":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "🆘 **እርዳታ እና አጠቃቀም**\n\nቦቱን ለመጠቀም ከላይ ካሉት አማራጮች የሚፈልጉትን መሳሪያ ይጫኑ። ለ Subdomain ፍለጋ የድር ጣቢያ ስም መጻፍ በቂ ነው።", reply_markup=get_main_menu())

    else:
        bot.answer_callback_query(call.id, "⚠️ ይህ መሳሪያ በዝግጅት ላይ ነው!", show_alert=True)

# 7. የተሻሻለ እና ጥልቅ የ Subdomain ፍለጋ (Super Scan)
def process_super_subdomain(message):
    chat_id = message.chat.id
    query = message.text.strip()

    if not check_subscription(chat_id):
        send_welcome(message)
        return

    processing_msg = bot.send_message(chat_id, f"🔍 **Super Scan** በ `{query}` ላይ በመካሄድ ላይ ነው... እባክዎ ትንሽ ይጠብቁ።", parse_mode="Markdown")

    try:
        url = f"https://crt.sh/?q=%25.{query}&output=json"
        # የጊዜ ገደብ ወደ 30 ሰከንድ ከፍ ተደርጓል (Timeout እንዳይፈጠር)
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except Exception:
                bot.edit_message_text("⚠️ ከሰርቨሩ የተገኘው መረጃ ትክክለኛ አይደለም።", chat_id, processing_msg.message_id)
                return

            subdomains = set()
            for entry in data:
                name_value = entry.get('name_value')
                if name_value:
                    for sub in name_value.split('\n'):
                        sub = sub.strip()
                        if sub and not sub.startswith('*'):
                            subdomains.add(sub)

            subdomain_list = sorted(list(subdomains))[:40] # እስከ 40 ጥልቅ ውጤቶች
            
            if subdomain_list:
                result_text = f"✅ **የተገኙ Super Scan ውጤቶች ({query}) [총 {len(subdomain_list)}]:**\n\n" + "\n".join([f"<code>{s}</code>" for s in subdomain_list])
                bot.delete_message(chat_id, processing_msg.message_id)
                bot.send_message(chat_id, result_text, parse_mode="HTML", reply_markup=get_main_menu())
            else:
                bot.edit_message_text(f"⚠️ ለ `{query}` ምንም ንዑስ ዶሜይን አልተገኘም።", chat_id, processing_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("⚠️ ከ `crt.sh` ሰርቨር ጋር ግንኙነት መፍጠር አልተቻለም።", chat_id, processing_msg.message_id)
            
    except requests.exceptions.Timeout:
        bot.edit_message_text("⏱️ ሰርቨሩ (crt.sh) በጥያቄው መብዛት ምክንያት ዘግይቷል (Timeout)። እባክዎ እንደገና ይሞክሩ።", chat_id, processing_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ ስህተት ተፈጥሯል: {e}", chat_id, processing_msg.message_id)

# 8. Render ሰርቨር እንዳይዘጋ የሚያደርግ የ Flask ሰርቨር
app = Flask('')

@app.route('/')
def home():
    return "NetX Tools Pro Bot is running successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 9. ማስጀመር
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    
    print("Bot is starting polling...")
    bot.infinity_polling()
