import os
import sys
import time
import json
import datetime
import subprocess
import threading
from pathlib import Path

# UTF-8 stdout fix
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import telebot

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable
RUN_NEWS_PATH = SCRIPT_DIR / "run_news.py"
FAST_WEB_PATH = SCRIPT_DIR / "fast_web_updater.py"
STATE_FILE = SCRIPT_DIR / "autopilot_state.json"
CONFIG_FILE = SCRIPT_DIR / "config.json"

BOT_TOKEN = "7687762430:AAFuWh2gSHch2Cr4ppuOQjTVK4EcYSS8GkE"
ADMIN_CHAT_ID = 6347858548
bot = telebot.TeleBot(BOT_TOKEN)

# 4 Daily Video Slots (Reels to Instagram @news_kid_ig)
VIDEO_SLOTS = [
    {"slot": 1, "time": "10:00", "display": "10:00 AM", "category": "breaking"},
    {"slot": 2, "time": "15:00", "display": "03:00 PM", "category": "national"},
    {"slot": 3, "time": "19:00", "display": "07:00 PM", "category": "tech"},
    {"slot": 4, "time": "22:30", "display": "10:30 PM", "category": "sports"}
]

# Daytime Web Update Slots (Fast 10s Cards to newskid.devv.in)
DAY_WEB_SLOTS = [
    "09:15", "11:00", "12:00", "14:15", "16:00", "18:15", "20:00", "21:45"
]

# Overnight Web Update Slots (Every 30 mins)
OVERNIGHT_WEB_SLOTS = [
    "23:15", "23:45", "00:15", "00:45", "01:15", "01:45",
    "02:15", "02:45", "03:15", "03:45", "04:15", "04:45",
    "05:15", "05:45", "06:15", "06:45", "07:15"
]

ALL_WEB_SLOTS = sorted(list(set(DAY_WEB_SLOTS + OVERNIGHT_WEB_SLOTS)))


def notify_telegram(message):
    try:
        bot.send_message(ADMIN_CHAT_ID, message, parse_mode="HTML")
    except Exception as e:
        try:
            bot.send_message(ADMIN_CHAT_ID, message)
        except Exception:
            print(f"⚠️ Telegram notice error: {e}")


def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"video_runs": {}, "web_runs": {}}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving state: {e}")


def run_video_pipeline(slot_info):
    category = slot_info.get("category", "breaking")
    display_time = slot_info.get("display", "")
    print(f"\n{'='*60}\n🎬 TRIGGERING NEWS KID VIDEO SLOT ({display_time}) | Category: {category.upper()}\n{'='*60}")
    notify_telegram(f"⚡ <b>NEWS KID Video Slot Triggered!</b>\n⏰ Time: {display_time}\n🏷️ Category: {category.upper()}\n⏳ Generating 60s Reel...")

    cmd = [PYTHON_EXE, str(RUN_NEWS_PATH), category, category]
    try:
        res = subprocess.run(cmd, cwd=str(SCRIPT_DIR), capture_output=True, text=True, timeout=600)
        if res.returncode == 0:
            print("✅ Video slot completed successfully!")
            # Read last upload details
            ig_log = SCRIPT_DIR / "last_instagram_upload.json"
            yt_log = SCRIPT_DIR / "last_youtube_upload.json"
            reel_url = ""
            yt_url = ""
            if ig_log.exists():
                try:
                    with open(ig_log, "r", encoding="utf-8") as f:
                        ld = json.load(f)
                        reel_url = ld.get("reel_url", "")
                except Exception:
                    pass
            if yt_log.exists():
                try:
                    with open(yt_log, "r", encoding="utf-8") as f:
                        yd = json.load(f)
                        yt_url = yd.get("video_url", "")
                except Exception:
                    pass

            msg = (
                f"🎉 <b>NEWS KID Video Published Successfully!</b>\n"
                f"⏰ Slot: {display_time} ({category.upper()})\n"
            )
            if yt_url:
                msg += f"📺 YouTube: {yt_url}\n"
            if reel_url:
                msg += f"📲 Instagram: {reel_url}\n"
            msg += f"🌐 Web Portal: https://newskid.devv.in"

            notify_telegram(msg)
            return True
        else:
            print(f"❌ Video generation returned non-zero code: {res.returncode}")
            print(res.stderr[-500:])
            notify_telegram(f"❌ <b>NEWS KID Video Error ({display_time})</b>:\n<code>{res.stderr[-300:]}</code>")
            return False
    except Exception as e:
        print(f"❌ Video pipeline exception: {e}")
        notify_telegram(f"❌ <b>NEWS KID Video Failed ({display_time})</b>: {e}")
        return False


def run_web_update(slot_time):
    print(f"\n{'='*60}\n🌐 TRIGGERING FAST WEB NEWS UPDATE ({slot_time})\n{'='*60}")
    cmd = [PYTHON_EXE, str(FAST_WEB_PATH)]
    try:
        res = subprocess.run(cmd, cwd=str(SCRIPT_DIR), capture_output=True, text=True, timeout=120)
        if res.returncode == 0:
            print(f"✅ Fast web update for {slot_time} completed!")
            # Send Telegram alert with latest headline to user
            try:
                feed_path = SCRIPT_DIR / "web_feed.json"
                if feed_path.exists():
                    with open(feed_path, "r", encoding="utf-8") as f:
                        cards = json.load(f)
                        if cards and len(cards) > 0:
                            top = cards[0]
                            t_hi = top.get("title", "ताज़ा बड़ी खबर")
                            cat = top.get("category", "breaking").upper()
                            msg = (
                                f"🌐 <b>NEWS KID Web Update Live ({slot_time})!</b>\n\n"
                                f"📰 <b>{t_hi}</b>\n"
                                f"🏷️ <i>श्रेणी: {cat}</i>\n"
                                f"⚡ <i>60 शब्दों में लाइव कार्ड + AI स्टूडियो आवाज़</i>\n\n"
                                f"👉 <b>वेब पोर्टल पर देखें:</b> https://newskid.devv.in"
                            )
                            notify_telegram(msg)
            except Exception as te:
                print(f"⚠️ Telegram notice error: {te}")
            return True
        else:
            print(f"⚠️ Fast web update notice: {res.stderr[-300:]}")
            return False
    except Exception as e:
        print(f"⚠️ Web update error: {e}")
        return False


def main():
    print("=" * 65)
    print("🚀 NEWS KID AUTOPILOT ENGINE STARTED (24/7 SCHEDULER)")
    print("=" * 65)
    print(f"📅 Video Slots ({len(VIDEO_SLOTS)}):")
    for vs in VIDEO_SLOTS:
        print(f"   • {vs['display']} ({vs['time']}) ➔ Category: {vs['category'].upper()}")
    print(f"🌐 Web Card Slots ({len(ALL_WEB_SLOTS)}):")
    print(f"   • Daytime (8 slots): {', '.join(DAY_WEB_SLOTS)}")
    print(f"   • Overnight (17 slots): {', '.join(OVERNIGHT_WEB_SLOTS[:5])}... (Every 30m)")
    print("=" * 65)

    notify_telegram(
        "🚀 <b>NEWS KID 24/7 Autopilot Engine is Online!</b>\n\n"
        f"🎬 <b>Daily Reels:</b> 4 Slots (10:00 AM, 03:00 PM, 07:00 PM, 10:30 PM)\n"
        f"🌐 <b>Web Updates:</b> 25 Daily Card Refreshes (Day & Night)\n"
        "🟢 Status: Actively Monitoring Timers & Telegram Listener."
    )

    # Start 24/7 Interactive Telegram Bot Listener in background thread
    def start_tg():
        try:
            import telegram_news_bot
            telegram_news_bot.start_bot()
        except Exception as te:
            print(f"⚠️ Telegram listener thread note: {te}")

    threading.Thread(target=start_tg, daemon=True).start()
    print("🤖 Telegram Bot Listener (@News998889bot) launched in background!", flush=True)

    while True:
        try:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")

            state = load_state()
            today_videos = state.get("video_runs", {}).get(today_str, [])
            today_webs = state.get("web_runs", {}).get(today_str, [])

            # 1. Check Video Slots
            for vs in VIDEO_SLOTS:
                if vs["time"] == time_str and vs["slot"] not in today_videos:
                    print(f"⏰ [MATCH] Time is {time_str}. Triggering Video Slot {vs['slot']}...")
                    success = run_video_pipeline(vs)
                    if success:
                        if today_str not in state.setdefault("video_runs", {}):
                            state["video_runs"][today_str] = []
                        state["video_runs"][today_str].append(vs["slot"])
                        save_state(state)

            # 2. Check Fast Web Slots
            if time_str in ALL_WEB_SLOTS and time_str not in today_webs:
                print(f"🌐 [MATCH] Time is {time_str}. Triggering Fast Web Update...")
                success = run_web_update(time_str)
                if success:
                    if today_str not in state.setdefault("web_runs", {}):
                        state["web_runs"][today_str] = []
                    state["web_runs"][today_str].append(time_str)
                    save_state(state)

        except Exception as e:
            print(f"⚠️ Scheduler loop error: {e}")

        time.sleep(30)


if __name__ == "__main__":
    main()
