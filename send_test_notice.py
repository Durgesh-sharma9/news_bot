import json
import telebot

BOT_TOKEN = "7687762430:AAFuWh2gSHch2Cr4ppuOQjTVK4EcYSS8GkE"
ADMIN_CHAT_ID = 6347858548

bot = telebot.TeleBot(BOT_TOKEN)
try:
    with open('/home/opc/news_bot/web_feed.json', 'r', encoding='utf-8') as f:
        feed = json.load(f)
    top = feed[0]
    msg = (
        "🌐 <b>NEWS KID Web Update Live (18:15)!</b>\n\n"
        f"📰 <b>{top['title']}</b>\n"
        f"🏷️ <i>श्रेणी: {top.get('category','breaking').upper()}</i>\n"
        "⚡ <i>60 शब्दों में लाइव कार्ड + AI स्टूडियो आवाज़</i>\n\n"
        "👉 <b>वेब पोर्टल पर देखें:</b> https://newskid.devv.in"
    )
    bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="HTML")
    print("Telegram notification sent successfully to user!")
except Exception as e:
    print("Error:", e)
