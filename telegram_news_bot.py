import os
import sys
import json
import time
import socket
import threading
import subprocess
from pathlib import Path

# Force IPv4 for stable Telegram connections on Windows/Linux
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
FAST_WEB_PATH = SCRIPT_DIR / "fast_web_updater.py"
SCRIPT_JSON_PATH = SCRIPT_DIR / "script.json"
VIDEO_PATH = SCRIPT_DIR / "final_news.mp4"
PYTHON_EXE = sys.executable

config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

BOT_TOKEN = config.get("telegram_bot_token", "7687762430:AAFuWh2gSHch2Cr4ppuOQjTVK4EcYSS8GkE")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

pending_topics = {}


def get_action_menu(topic):
    markup = types.InlineKeyboardMarkup(row_width=1)
    b1 = types.InlineKeyboardButton("🌐 Web Portal Card (10s Instant Live)", callback_data=f"act_web")
    b2 = types.InlineKeyboardButton("🎬 60s Video Reel (Insta + Telegram)", callback_data=f"act_video")
    markup.add(b1, b2)
    return markup


def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("🔴 Breaking News (Auto)", callback_data="cat_breaking")
    b2 = types.InlineKeyboardButton("🚀 Tech & AI News", callback_data="cat_tech")
    b3 = types.InlineKeyboardButton("🇮🇳 National News", callback_data="cat_national")
    b4 = types.InlineKeyboardButton("💼 Business News", callback_data="cat_business")
    b5 = types.InlineKeyboardButton("🏏 Sports Update", callback_data="cat_sports")
    b6 = types.InlineKeyboardButton("✍️ Type Any Topic", callback_data="cat_custom")
    markup.add(b1)
    markup.add(b2, b3)
    markup.add(b4, b5)
    markup.add(b6)
    return markup


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "<b>📰 Welcome to NEWS KID Automation Bot!</b>\n\n"
        "Aap yahan se **Web Portal** aur **Video Reels** dono direct control kar sakte hain:\n\n"
        "👉 <b>Quick Commands:</b>\n"
        "• <code>/web [topic]</code> ➔ Instant 10s Card on newskid.devv.in\n"
        "• <code>/reel [topic]</code> ➔ 60s Video Reel with Voiceover & Photos\n"
        "• <code>/breaking</code> ➔ Top live breaking news push\n\n"
        "Ya seedhe **koi bhi topic type karke bhej dijiye**, bot automatic research karke publish kar dega!"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu())


@bot.message_handler(commands=['web'])
def handle_web_command(message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        topic = args[1].strip()
        threading.Thread(target=generate_and_send_web_card, args=(chat_id, topic, "breaking")).start()
    else:
        bot.send_message(chat_id, "⚠️ Kripya topic sath me likhein!\nExample: <code>/web ISRO Chandrayaan 4</code>")


@bot.message_handler(commands=['reel', 'video', 'news'])
def handle_video_command(message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        topic = args[1].strip()
        threading.Thread(target=generate_and_send_news_video, args=(chat_id, topic, "breaking")).start()
    else:
        bot.send_message(chat_id, "⚠️ Kripya topic sath me likhein!\nExample: <code>/reel Stock Market Crash</code>")


@bot.message_handler(commands=['breaking'])
def handle_breaking_command(message):
    chat_id = message.chat.id
    threading.Thread(target=generate_and_send_web_card, args=(chat_id, None, "breaking")).start()


@bot.message_handler(func=lambda m: True)
def handle_incoming_text(message):
    chat_id = message.chat.id
    topic = message.text.strip()

    if len(topic) < 3:
        bot.send_message(chat_id, "Kripya valid news topic likhein:", reply_markup=get_main_menu())
        return

    pending_topics[chat_id] = topic
    prompt_text = (
        f"✍️ <b>Topic mila:</b> <i>\"{topic}\"</i>\n\n"
        f"Aap iska kya banana chahte hain?"
    )
    bot.send_message(chat_id, prompt_text, reply_markup=get_action_menu(topic))


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    category_map = {
        "cat_breaking": ("Latest Breaking News", "breaking"),
        "cat_tech": ("Technology News", "tech"),
        "cat_national": ("National News", "national"),
        "cat_business": ("Business & Economy News", "business"),
        "cat_sports": ("Sports News", "sports")
    }

    if data == "cat_custom":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "✍️ <b>Apna topic type karke bhejein:</b>\n(Jaise: <i>Cabinet Decision on Railway</i>)")
        return

    if data in category_map:
        topic, category = category_map[data]
        bot.answer_callback_query(call.id, text=f"Processing {category}...")
        pending_topics[chat_id] = topic
        bot.send_message(chat_id, f"📌 <b>Category:</b> {category.upper()}\nKya banana chahte hain?", reply_markup=get_action_menu(topic))
        return

    if data == "act_web":
        topic = pending_topics.get(chat_id, "Latest Breaking News")
        bot.answer_callback_query(call.id, text="Pushing to Web Portal...")
        bot.edit_message_text(f"⏳ <b>Web Portal Card ban raha hai:</b> <i>\"{topic}\"</i> (10-12s)...", chat_id, call.message.message_id)
        threading.Thread(target=generate_and_send_web_card, args=(chat_id, topic, "breaking", call.message.message_id)).start()
        return

    if data == "act_video":
        topic = pending_topics.get(chat_id, "Latest Breaking News")
        bot.answer_callback_query(call.id, text="Rendering 60s Reel...")
        bot.edit_message_text(f"⏳ <b>60s Video Reel ban rahi hai:</b> <i>\"{topic}\"</i> (2-3 min)...", chat_id, call.message.message_id)
        threading.Thread(target=generate_and_send_news_video, args=(chat_id, topic, "breaking", call.message.message_id)).start()
        return


def generate_and_send_web_card(chat_id, topic, category="breaking", status_msg_id=None):
    if not status_msg_id:
        status_msg = bot.send_message(chat_id, f"⏳ <b>Web Card Push Ho Raha Hai:</b> <i>\"{topic or 'Breaking News'}\"</i>...")
        status_msg_id = status_msg.message_id

    try:
        from fast_web_updater import run_fast_web_update
        card = run_fast_web_update(target_category=category, custom_topic=topic)
        if card and isinstance(card, dict):
            caption = (
                f"🎉 <b>CARD PUBLISHED TO WEB PORTAL!</b>\n\n"
                f"📌 <b>{card['title']}</b>\n\n"
                f"📰 {card['summary'][:160]}...\n\n"
                f"🏷️ <b>Category:</b> {card['badge']}\n"
                f"🌐 <b>Live on Portal:</b> https://newskid.devv.in"
            )
            try:
                bot.delete_message(chat_id, status_msg_id)
            except Exception:
                pass
            bot.send_photo(chat_id, photo=card.get("imageUrl"), caption=caption, parse_mode="HTML")
        else:
            bot.edit_message_text("❌ Card generate nahi ho paya!", chat_id, status_msg_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Web update error: {e}", chat_id, status_msg_id)


def generate_and_send_news_video(chat_id, topic, category="breaking", status_msg_id=None):
    if not status_msg_id:
        status_msg = bot.send_message(chat_id, f"⏳ <b>60s Reel Render Ho Rahi Hai:</b> <i>\"{topic}\"</i>\n• Real HD Photos\n• AI Anchor Voice\n• Auto-Publish to Instagram...")
        status_msg_id = status_msg.message_id

    try:
        cmd = [PYTHON_EXE, str(RUN_NEWS_PATH), topic or "breaking", category]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=str(SCRIPT_DIR))

        if res.returncode != 0:
            err = res.stderr[-300:] if res.stderr else res.stdout[-300:]
            bot.edit_message_text(f"❌ Video render error: {err}", chat_id, status_msg_id)
            return

        # Read last upload
        log_file = SCRIPT_DIR / "last_instagram_upload.json"
        reel_url = ""
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    ld = json.load(f)
                    reel_url = ld.get("reel_url", "")
            except Exception:
                pass

        headline = topic
        if SCRIPT_JSON_PATH.exists():
            try:
                with open(SCRIPT_JSON_PATH, "r", encoding="utf-8") as f:
                    headline = json.load(f).get("title", headline)
            except Exception:
                pass

        caption = (
            f"🎉 <b>NEWS REEL PUBLISHED LIVE!</b>\n\n"
            f"📌 <b>{headline}</b>\n\n"
            f"📲 <b>Instagram Reel:</b> {reel_url or '@news_kid_ig'}\n"
            f"🌐 <b>Web Portal:</b> https://newskid.devv.in"
        )

        if VIDEO_PATH.exists():
            try:
                bot.delete_message(chat_id, status_msg_id)
            except Exception:
                pass
            with open(VIDEO_PATH, "rb") as vf:
                bot.send_video(chat_id, video=vf, caption=caption, parse_mode="HTML", supports_streaming=True)
        else:
            bot.edit_message_text(caption, chat_id, status_msg_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Video error: {e}", chat_id, status_msg_id)


def start_bot():
    print("=" * 60)
    print("🤖 NEWS KID TELEGRAM CONTROLLER ACTIVE: @News998889bot")
    print("   Features: Instant Web Card Push (10s) | 60s Reel Video (3min)")
    print("=" * 60)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Telegram polling error: {e}, reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    start_bot()
