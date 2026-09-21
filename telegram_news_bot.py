import os
import sys
import json
import time
import socket
import threading
import subprocess
from pathlib import Path

# Force IPv4 for stable Telegram connections on Windows
import urllib3.util.connection as urllib3_cn
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET
socket.setdefaulttimeout(300)

# Windows UTF-8 console output fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

import telebot
from telebot import types, apihelper

apihelper.READ_TIMEOUT = 300
apihelper.CONNECT_TIMEOUT = 120

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
RUN_NEWS_PATH = SCRIPT_DIR / "run_news.py"
SCRIPT_JSON_PATH = SCRIPT_DIR / "script.json"
VIDEO_PATH = SCRIPT_DIR / "final_news.mp4"
PYTHON_EXE = sys.executable

# Load Token
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

BOT_TOKEN = config.get("telegram_bot_token", "7687762430:AAFuWh2gSHch2Cr4ppuOQjTVK4EcYSS8GkE")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

user_states = {}


def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("🔴 Breaking News (Auto)", callback_data="cat_breaking")
    b2 = types.InlineKeyboardButton("🚀 Tech & AI News", callback_data="cat_tech")
    b3 = types.InlineKeyboardButton("🇮🇳 National News", callback_data="cat_national")
    b4 = types.InlineKeyboardButton("💼 Business & Economy", callback_data="cat_business")
    b5 = types.InlineKeyboardButton("🏏 Sports Update", callback_data="cat_sports")
    b6 = types.InlineKeyboardButton("✍️ Custom Topic", callback_data="cat_custom")
    markup.add(b1)
    markup.add(b2, b3)
    markup.add(b4, b5)
    markup.add(b6)
    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "<b>📰 Welcome to FastNews AI Bot!</b>\n\n"
        "Main aapke liye <b>real-time breaking news</b> ki high-retention "
        "vertical videos banata hoon (with real news photos + news anchor voice + subtitles)!\n\n"
        "👉 Niche diye gaye buttons se category select karein ya type karein:\n"
        "<code>/news Chandrayaan 4 Update</code>\n"
        "<code>/breaking</code> (Latest Live News)"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu())


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    category_topics = {
        "cat_breaking": "Latest Breaking News India",
        "cat_tech": "Artificial Intelligence and Tech News India",
        "cat_national": "Top National News India",
        "cat_business": "Stock Market and Business News India",
        "cat_sports": "Latest Cricket and Sports News India"
    }

    if data == "cat_custom":
        user_states[chat_id] = "awaiting_custom_topic"
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "✍️ <b>Apna Topic type karke bhejein:</b>\n(Jaise: <i>ISRO New Satellite Launch</i> ya <i>Union Budget Update</i>)")
        return

    if data in category_topics:
        topic = category_topics[data]
        bot.answer_callback_query(call.id, text=f"Generating: {topic[:20]}...")
        threading.Thread(target=generate_and_send_news, args=(chat_id, topic)).start()


@bot.message_handler(commands=['news'])
def handle_news_command(message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        topic = args[1].strip()
        threading.Thread(target=generate_and_send_news, args=(chat_id, topic)).start()
    else:
        bot.send_message(chat_id, "⚠️ Kripya topic sath mein likhein!\nExample: <code>/news ISRO Mission</code>")


@bot.message_handler(commands=['breaking'])
def handle_breaking_command(message):
    chat_id = message.chat.id
    threading.Thread(target=generate_and_send_news, args=(chat_id, "Latest Breaking News India")).start()


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    topic = message.text.strip()

    if state == "awaiting_custom_topic" or len(topic) > 3:
        user_states.pop(chat_id, None)
        threading.Thread(target=generate_and_send_news, args=(chat_id, topic)).start()
    else:
        bot.send_message(chat_id, "Kripya menu se option chunein:", reply_markup=get_main_menu())


def generate_and_send_news(chat_id, topic):
    status_msg = bot.send_message(
        chat_id,
        f"⏳ <b>Generating News Video:</b> <i>\"{topic}\"</i>\n"
        f"• Researching Google News RSS...\n"
        f"• Fetching Real HD News Photos...\n"
        f"• Creating Hindi Anchor Voiceover...\n"
        f"<i>Kripya 20-30 seconds wait karein...</i>"
    )

    try:
        cmd = [PYTHON_EXE, str(RUN_NEWS_PATH), topic]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=str(SCRIPT_DIR))

        if result.returncode != 0:
            err = result.stderr[-300:] if result.stderr else result.stdout[-300:]
            bot.edit_message_text(f"❌ Video generation error: {err}", chat_id, status_msg.message_id)
            return

        if not VIDEO_PATH.exists():
            bot.edit_message_text("❌ final_news.mp4 generate nahi ho payi!", chat_id, status_msg.message_id)
            return

        # Read details from script.json
        headline = "FastNews Breaking Update"
        badge = "🔴 BREAKING NEWS"
        if SCRIPT_JSON_PATH.exists():
            try:
                with open(SCRIPT_JSON_PATH, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                    headline = sdata.get("title", headline)
                    badge = sdata.get("badge", badge)
            except Exception:
                pass

        bot.edit_message_text("📤 <b>Video ban gayi! Telegram par upload ho rahi hai...</b>", chat_id, status_msg.message_id)

        caption = (
            f"🎬 <b>{badge}</b>\n\n"
            f"📌 <b>{headline}</b>\n\n"
            f"⚡ Generated via FastNews AI\n"
            f"#News #BreakingNews #Shorts #India"
        )

        with open(VIDEO_PATH, "rb") as vf:
            bot.send_video(
                chat_id=chat_id,
                video=vf,
                caption=caption,
                parse_mode="HTML",
                supports_streaming=True,
                timeout=300
            )

        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")


def start_bot():
    print("=" * 60)
    print("🤖 FASTNEWS AI TELEGRAM BOT ACTIVE: @News998889bot")
    print("   Mode: Local Testing (Zero Video Downloads, Fast Render)")
    print("=" * 60)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)


if __name__ == "__main__":
    start_bot()
