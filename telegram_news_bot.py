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
ADMIN_CHAT_ID = 6347858548
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
    b_auto = types.InlineKeyboardButton("⚡ 1-Click Auto Post (No Topic Needed)", callback_data="btn_auto_run")
    b1 = types.InlineKeyboardButton("🔴 Breaking News", callback_data="cat_breaking")
    b2 = types.InlineKeyboardButton("🚀 Tech & AI News", callback_data="cat_tech")
    b3 = types.InlineKeyboardButton("🇮🇳 National News", callback_data="cat_national")
    b4 = types.InlineKeyboardButton("💼 Business News", callback_data="cat_business")
    b5 = types.InlineKeyboardButton("🏏 Sports Update", callback_data="cat_sports")
    b6 = types.InlineKeyboardButton("✍️ Custom Topic", callback_data="cat_custom")
    markup.add(b_auto)
    markup.add(b1, b2)
    markup.add(b3, b4)
    markup.add(b5, b6)
    return markup


def send_rich_card_message(chat_id, card, status_msg_id=None):
    title = card.get("title", "Breaking News")
    summary = card.get("summary", "")
    badge = card.get("badge", "🔴 बड़ी खबर")
    img_url = card.get("imageUrl", "")

    caption = (
        f"⚡ <b>LIVE NEWS UPDATE PUBLISHED!</b>\n\n"
        f"📌 <b>Headline:</b>\n{title}\n\n"
        f"📰 <b>Summary:</b>\n{summary}\n\n"
        f"🏷️ <b>Category:</b> {badge}\n"
        f"🌐 <b>Live on Portal:</b> https://newskid.devv.in"
    )

    if status_msg_id:
        try:
            bot.delete_message(chat_id, status_msg_id)
        except Exception:
            pass

    # Try sending photo with caption
    sent = False
    if img_url and img_url.startswith("http"):
        try:
            bot.send_photo(chat_id, photo=img_url, caption=caption, parse_mode="HTML")
            sent = True
        except Exception as e:
            print(f"⚠️ Telegram photo notice: {e}")

    # Fallback to rich HTML text
    if not sent:
        try:
            bot.send_message(chat_id, caption, parse_mode="HTML")
        except Exception:
            clean_text = caption.replace("<b>", "").replace("</b>", "")
            bot.send_message(chat_id, clean_text)


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "<b>📰 Welcome to NEWS KID Automation Controller!</b>\n\n"
        "⚡ <b>1-Click Auto Run:</b> Type <code>/run</code> — Bot khud taaza khabar dhundhega aur 10 second me website par publish kar dega (zero typing required)!\n\n"
        "👉 <b>Other Commands:</b>\n"
        "• <code>/run</code> ➔ Instant Auto Web Card (No topic needed)\n"
        "• <code>/web [topic]</code> ➔ Specific topic card on newskid.devv.in\n"
        "• <code>/reel [topic]</code> ➔ 60s Video Reel with AI Voice & Photos\n"
        "• <code>/breaking</code> ➔ Top breaking news push\n\n"
        "Ya seedhe **koi bhi topic type karke bhej dijiye**!"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=get_main_menu())


@bot.message_handler(commands=['run', 'auto', 'fast'])
def handle_auto_run_command(message):
    chat_id = message.chat.id
    status_msg = bot.send_message(chat_id, "⚡ <b>Auto News Fetching...</b> Google News se taaza khabar dhundh kar 10s me web par daal raha hoon...")
    threading.Thread(target=generate_and_send_web_card, args=(chat_id, None, None, status_msg.message_id)).start()


@bot.message_handler(commands=['web'])
def handle_web_command(message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        topic = args[1].strip()
        status_msg = bot.send_message(chat_id, f"⏳ <b>Researching \"{topic}\"...</b> 10s me web card ban raha hai...")
        threading.Thread(target=generate_and_send_web_card, args=(chat_id, topic, "breaking", status_msg.message_id)).start()
    else:
        # If no topic, run auto!
        handle_auto_run_command(message)


@bot.message_handler(commands=['reel', 'video', 'news'])
def handle_video_command(message):
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    topic = args[1].strip() if len(args) > 1 else "breaking"
    status_msg = bot.send_message(chat_id, f"🎬 <b>60s Video Reel Generation Started:</b> <i>\"{topic}\"</i>\n• AI Script\n• Anchor Voice\n• Photos & Subtitles...")
    threading.Thread(target=generate_and_send_news_video, args=(chat_id, topic, "breaking", status_msg.message_id)).start()


@bot.message_handler(commands=['breaking'])
def handle_breaking_command(message):
    handle_auto_run_command(message)


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

    if data == "btn_auto_run":
        bot.answer_callback_query(call.id, text="Auto fetching breaking news...")
        bot.edit_message_text("⚡ <b>Auto News Fetching...</b> Google News se taaza khabar dhoondh raha hoon...", chat_id, call.message.message_id)
        threading.Thread(target=generate_and_send_web_card, args=(chat_id, None, None, call.message.message_id)).start()
        return

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
        bot.answer_callback_query(call.id, text=f"Auto processing {category}...")
        bot.edit_message_text(f"⏳ <b>{category.upper()} News Fetching...</b> Card ban raha hai...", chat_id, call.message.message_id)
        threading.Thread(target=generate_and_send_web_card, args=(chat_id, None, category, call.message.message_id)).start()
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
    try:
        from fast_web_updater import run_fast_web_update
        card = run_fast_web_update(target_category=category, custom_topic=topic)
        if card and isinstance(card, dict):
            send_rich_card_message(chat_id, card, status_msg_id)
        else:
            if status_msg_id:
                bot.edit_message_text("❌ Card generate nahi ho paya!", chat_id, status_msg_id)
    except Exception as e:
        print(f"❌ Web update error: {e}")
        if status_msg_id:
            try:
                bot.edit_message_text(f"❌ Error: {e}", chat_id, status_msg_id)
            except Exception:
                pass


def generate_and_send_news_video(chat_id, topic, category="breaking", status_msg_id=None):
    try:
        cmd = [PYTHON_EXE, str(RUN_NEWS_PATH), topic or "breaking", category]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', cwd=str(SCRIPT_DIR))

        if res.returncode != 0:
            err = res.stderr[-300:] if res.stderr else res.stdout[-300:]
            if status_msg_id:
                bot.edit_message_text(f"❌ Video render error: {err}", chat_id, status_msg_id)
            return

        # Read last upload details
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
        summary = ""
        if SCRIPT_JSON_PATH.exists():
            try:
                with open(SCRIPT_JSON_PATH, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                    headline = sdata.get("title", headline)
                    scenes = sdata.get("scenes", [])
                    summary = " ".join([s.get("voice_text", "") for s in scenes if s.get("voice_text")][:2])
            except Exception:
                pass

        caption = (
            f"🎉 <b>NEWS REEL PUBLISHED LIVE!</b>\n\n"
            f"📌 <b>Headline:</b>\n{headline}\n\n"
            f"📰 <b>Story:</b>\n{summary[:160]}...\n\n"
            f"📲 <b>Instagram Reel:</b> {reel_url or '@news_kid_ig'}\n"
            f"🌐 <b>Live Portal:</b> https://newskid.devv.in"
        )

        if status_msg_id:
            try:
                bot.delete_message(chat_id, status_msg_id)
            except Exception:
                pass

        if VIDEO_PATH.exists():
            with open(VIDEO_PATH, "rb") as vf:
                bot.send_video(chat_id, video=vf, caption=caption, parse_mode="HTML", supports_streaming=True)
        else:
            bot.send_message(chat_id, caption, parse_mode="HTML")
    except Exception as e:
        if status_msg_id:
            try:
                bot.edit_message_text(f"❌ Video error: {e}", chat_id, status_msg_id)
            except Exception:
                pass


def start_bot():
    print("=" * 60)
    print("🤖 NEWS KID TELEGRAM CONTROLLER ACTIVE: @News998889bot")
    print("   Commands: /run (Auto Push) | /web [topic] | /reel [topic]")
    print("=" * 60)
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Telegram polling error: {e}, reconnecting in 5s...")
            time.sleep(5)


if __name__ == "__main__":
    start_bot()
