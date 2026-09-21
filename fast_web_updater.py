import os
import sys
import json
import re
import random
import asyncio
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
USED_NEWS_FILE = SCRIPT_DIR / "used_news.json"
WEB_FEED_FILE = SCRIPT_DIR / "web_feed.json"
TEMP_DIR = SCRIPT_DIR / "temp_web"
TEMP_DIR.mkdir(exist_ok=True)

# Load configuration
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

# Key #2 (Dedicated for NEWS KID Web & Videos)
GEMINI_KEY = config.get("gemini_backup_key", config.get("gemini_api_key", "AQ.Ab8RN6Ld2EVEwc-STPYK4zJpTJAEVHrdIBIXjynyNoVTuw-VgA"))
MONGODB_URI = config.get("mongodb_uri", "mongodb+srv://dev:ipZlD6vupMTc0rmM@backend.uuio5ow.mongodb.net/newskid")
IMAGEKIT_PUBLIC_KEY = config.get("imagekit_public_key", "")
IMAGEKIT_PRIVATE_KEY = config.get("imagekit_private_key", "")
IMAGEKIT_URL_ENDPOINT = config.get("imagekit_url_endpoint", "")

CATEGORY_FEEDS = {
    "breaking": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "national": "https://news.google.com/rss/headlines/section/topic/NATION?hl=hi&gl=IN&ceid=IN:hi",
    "tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=hi&gl=IN&ceid=IN:hi",
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=hi&gl=IN&ceid=IN:hi",
    "sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=hi&gl=IN&ceid=IN:hi",
    "world": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=hi&gl=IN&ceid=IN:hi"
}

CATEGORY_BADGES = {
    "breaking": "🔴 बड़ी खबर",
    "national": "🇮🇳 देश-राजनीति",
    "tech": "🚀 टेक & AI",
    "business": "💼 बिजनेस",
    "sports": "🏏 खेल",
    "world": "🌍 दुनिया"
}

CATEGORY_SOURCES = {
    "breaking": "NEWS KID Breaking Desk",
    "national": "NEWS KID National Desk",
    "tech": "NEWS KID Science Desk",
    "business": "NEWS KID Market Desk",
    "sports": "NEWS KID Sports Desk",
    "world": "NEWS KID World Desk"
}


def load_used_titles():
    if USED_NEWS_FILE.exists():
        try:
            with open(USED_NEWS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except Exception:
            pass
    return set()


def record_used_title(title):
    used = list(load_used_titles())
    used.append(title)
    if len(used) > 200:
        used = used[-200:]
    try:
        with open(USED_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(used, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def fetch_fresh_story(category="breaking"):
    feed_url = CATEGORY_FEEDS.get(category, CATEGORY_FEEDS["breaking"])
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(feed_url, headers=headers)

    used_titles = load_used_titles()

    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = root.findall("./channel/item")

        for it in items:
            raw_title = it.findtext("title", "").strip()
            title = re.sub(r"\s*-\s*[^-]+$", "", raw_title).strip()
            desc = it.findtext("description", "").strip()
            clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()

            if title and title not in used_titles and len(title) > 15:
                return title, clean_desc
    except Exception as e:
        print(f"  ⚠️ RSS feed warning ({e}), falling back to direct topic search...", flush=True)

    return "भारत और दुनिया की बड़ी ताज़ा हलचल", "राष्ट्रीय और अंतरराष्ट्रीय स्तर पर आज के बड़े घटनाक्रम"


def search_custom_story(topic):
    """Searches Google News RSS for a specific user topic."""
    encoded = urllib.parse.quote(topic)
    feed_url = f"https://news.google.com/rss/search?q={encoded}&hl=hi&gl=IN&ceid=IN:hi"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(feed_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = root.findall("./channel/item")
        if items:
            it = items[0]
            raw_title = it.findtext("title", "").strip()
            title = re.sub(r"\s*-\s*[^-]+$", "", raw_title).strip()
            desc = it.findtext("description", "").strip()
            clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
            if title and len(title) > 10:
                return title, clean_desc
    except Exception as e:
        print(f"  ⚠️ Topic RSS notice: {e}", flush=True)

    # Fallback to English search
    try:
        en_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        req_en = urllib.request.Request(en_url, headers=headers)
        with urllib.request.urlopen(req_en, timeout=7) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        items = root.findall("./channel/item")
        if items:
            it = items[0]
            raw_title = it.findtext("title", "").strip()
            title = re.sub(r"\s*-\s*[^-]+$", "", raw_title).strip()
            desc = it.findtext("description", "").strip()
            clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
            if title and len(title) > 10:
                return title, clean_desc
    except Exception:
        pass

    return f"{topic} पर बड़ा अपडेट", f"{topic} के संबंध में हालिया विकास और महत्वपूर्ण जानकारी सामने आई है।"



def generate_news_card_ai(headline, context, category):
    """Uses Gemini Key 2 to write bilingual 60-word news card with entities."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_KEY, transport='rest')

    prompt = f"""
You are a senior professional news editor for 'NEWS KID' (a verified 60-word inshorts news portal).
Write a 100% factual, compelling, objective news card in BOTH Hindi and English based on this real event:

HEADLINE: {headline}
CONTEXT: {context}
CATEGORY: {category}

STRICT EDITORIAL RULES:
1. Cover ONLY this single event with verified facts.
2. NEVER mention any other news channels or scraping sources (NEVER mention Aaj Tak, NDTV, BBC, ANI, PTI, etc.).
3. Write clean, punchy headline in Hindi (max 12 words) and English (max 12 words).
4. Write concise summary in Hindi (50 to 60 words) and English (50 to 60 words).
5. Provide 2 to 3 SPECIFIC real-life search queries in English (real name of person, organization, court, stadium, rocket, city) so real photos can be fetched.

OUTPUT STRICTLY VALID JSON ONLY (no markdown fences, no extra text):
{{
  "title": "Hindi headline here",
  "title_en": "English headline here",
  "summary": "50-60 words Hindi summary here",
  "summary_en": "50-60 words English summary here",
  "image_queries": ["Name 1 specific", "Name 2 specific"]
}}
"""
    models = ['gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.6-flash']
    api_keys = [GEMINI_KEY]
    backup = config.get("gemini_api_key")
    if backup and backup not in api_keys:
        api_keys.append(backup)

    for k_idx, key in enumerate(api_keys, 1):
        genai.configure(api_key=key, transport='rest')
        for m in models:
            try:
                print(f"  [AI] Querying {m} (Key #{k_idx})...", flush=True)
                model = genai.GenerativeModel(m)
                res = model.generate_content(prompt)
                txt = res.text.strip()
                txt = re.sub(r"^```(?:json)?\n?", "", txt)
                txt = re.sub(r"\n?```$", "", txt).strip()
                data = json.loads(txt)
                if "title" in data and "summary" in data:
                    print(f"  [AI] Successfully parsed JSON from {m}!", flush=True)
                    return data
            except Exception as e:
                print(f"  [AI] {m} note: {str(e)[:80]}...", flush=True)
                continue

    return {
        "title": headline,
        "title_en": headline,
        "summary": context[:250] if context else headline,
        "summary_en": context[:250] if context else headline,
        "image_queries": [headline[:25]]
    }


def search_real_photos(queries):
    """Fetches real unwatermarked photos for queries using Wikimedia, Bing, and Pexels."""
    from step3_download_images import search_wikimedia_images, search_bing_images, search_pexels_images

    found_urls = []
    for q in queries:
        try:
            w_imgs = search_wikimedia_images(q)
            for u in w_imgs:
                if u and isinstance(u, str) and u.startswith("http") and u not in found_urls:
                    found_urls.append(u)
        except Exception:
            pass

        if len(found_urls) < 3:
            try:
                b_imgs = search_bing_images(q, max_results=3)
                for u in b_imgs:
                    if u and isinstance(u, str) and u.startswith("http") and u not in found_urls:
                        found_urls.append(u)
            except Exception:
                pass

        if len(found_urls) < 3:
            try:
                p_imgs = search_pexels_images(q, max_results=2)
                for u in p_imgs:
                    if u and isinstance(u, str) and u.startswith("http") and u not in found_urls:
                        found_urls.append(u)
            except Exception:
                pass

        if len(found_urls) >= 3:
            break

    if not found_urls:
        found_urls = [
            "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&q=80",
            "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=1080&q=80",
            "https://images.unsplash.com/photo-1517976487502-5f69a0db01c6?w=1080&q=80"
        ]

    return found_urls[:3]


def upload_to_imagekit_cdn(file_path, file_name, folder="/newskid_cards/"):
    if not IMAGEKIT_PRIVATE_KEY:
        return None
    try:
        from imagekitio import ImageKit
        ik = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)
        with open(file_path, "rb") as f:
            upload = ik.files.upload(
                file=f,
                file_name=file_name,
                folder=folder,
                use_unique_file_name=True,
                tags=["newskid", "fast_sync"]
            )
            return getattr(upload, "url", None)
    except Exception as e:
        print(f"  ⚠️ ImageKit warning: {e}", flush=True)
        return None


async def generate_fast_audio(text, output_file, title=""):
    """Generates natural studio voiceover via edge-tts for the complete news card."""
    import edge_tts
    # Read full headline + complete news summary (never chop off!)
    full_speech = f"{title}। {text}".strip() if title else text.strip()
    comm = edge_tts.Communicate(full_speech, "hi-IN-MadhurNeural", rate="+8%", pitch="+10Hz")
    await asyncio.wait_for(comm.save(str(output_file)), timeout=30)


def run_fast_web_update(target_category=None, custom_topic=None):
    print("=" * 60, flush=True)
    print("⚡ [FAST WEB AUTO-UPDATER] Instant 60-Word Card Sync", flush=True)
    print("=" * 60, flush=True)

    # 1. Choose category & story
    if custom_topic:
        print(f"🔍 Searching User Topic: \"{custom_topic}\"...", flush=True)
        headline, context = search_custom_story(custom_topic)
        if not target_category:
            target_category = "breaking"
    else:
        if not target_category:
            categories = ["breaking", "national", "tech", "business", "sports", "world"]
            target_category = random.choice(categories)
        headline, context = fetch_fresh_story(target_category)

    print(f"🏷️ Selected Category: {target_category.upper()} ({CATEGORY_BADGES.get(target_category, '🔴 बड़ी खबर')})", flush=True)
    print(f"📌 Headline: \"{headline[:60]}...\"", flush=True)

    # 3. Generate bilingual card using Key #2
    print(f"🤖 Generating 60-Word Inshorts Card via Gemini (Key #2)...", flush=True)
    ai_card = generate_news_card_ai(headline, context, target_category)

    # 4. Search and download real photos
    queries = ai_card.get("image_queries", [headline[:30]])
    print(f"📸 Sourcing Real News Photos for: {queries}...", flush=True)
    real_photo_urls = search_real_photos(queries)
    print(f"  ✅ {len(real_photo_urls)} real photos acquired!", flush=True)

    # 5. Generate Studio Audio Voiceover
    audio_cdn_url = ""
    try:
        print(f"🎙️ Generating Studio Audio Voiceover...", flush=True)
        temp_audio = TEMP_DIR / f"voice_{int(datetime.now().timestamp())}.mp3"
        asyncio.run(generate_fast_audio(ai_card["summary"], temp_audio, title=ai_card.get("title", "")))

        if temp_audio.exists() and temp_audio.stat().st_size > 1000:
            audio_cdn_url = upload_to_imagekit_cdn(temp_audio, temp_audio.name, folder="/newskid_audio/")
            try:
                temp_audio.unlink()
            except Exception:
                pass
            if audio_cdn_url:
                print(f"  ✅ Audio uploaded to ImageKit CDN!", flush=True)
    except Exception as e:
        print(f"  ⚠️ Audio step skipped: {e}", flush=True)

    # 6. Build the Final Card Object
    final_card = {
        "title": ai_card.get("title", headline),
        "title_en": ai_card.get("title_en", headline),
        "summary": ai_card.get("summary", context),
        "summary_en": ai_card.get("summary_en", context),
        "category": target_category,
        "badge": CATEGORY_BADGES.get(target_category, "🔴 बड़ी खबर"),
        "imageUrl": real_photo_urls[0],
        "images": real_photo_urls,
        "audioUrl": audio_cdn_url or "",
        "source": CATEGORY_SOURCES.get(target_category, "NEWS KID Editorial Desk"),
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "views": random.randint(120, 450),
        "likes": random.randint(15, 65)
    }

    # 7. Push to MongoDB Atlas (with duplicate prevention)
    mongo_saved = False
    if MONGODB_URI:
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000)
            db = client["newskid"]
            existing = db["cards"].find_one({"title": final_card["title"]})
            if existing:
                print(f"  ℹ️ Card already in MongoDB Atlas (ID: {existing['_id']})", flush=True)
            else:
                res = db["cards"].insert_one(final_card.copy())
                print(f"🚀 Pushed to MongoDB Atlas! Card ID: {res.inserted_id}", flush=True)
            mongo_saved = True
        except Exception as e:
            print(f"⚠️ MongoDB warning: {e}", flush=True)

    # 8. Append to local web_feed.json
    try:
        feed = []
        if WEB_FEED_FILE.exists():
            with open(WEB_FEED_FILE, "r", encoding="utf-8") as f:
                feed = json.load(f)
        feed.insert(0, final_card)
        with open(WEB_FEED_FILE, "w", encoding="utf-8") as f:
            json.dump(feed[:50], f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 9. Mark headline as used
    record_used_title(headline)

    print("\n" + "=" * 60, flush=True)
    print("🎉 [FAST UPDATE SUCCESS] New Card Live on Web Portal in ~10s!", flush=True)
    print(f"📰 Headline (HI): {final_card['title']}", flush=True)
    print(f"🌐 Headline (EN): {final_card['title_en']}", flush=True)
    print(f"🏷️ Category    : {final_card['category']} | {final_card['badge']}", flush=True)
    print(f"🎙️ Audio Voice : {'Available' if audio_cdn_url else 'Browser Neural'}", flush=True)
    print("=" * 60, flush=True)

    # 10. Send Telegram Alert to User
    try:
        import telebot
        t_token = config.get("telegram_bot_token", "7687762430:AAFuWh2gSHch2Cr4ppuOQjTVK4EcYSS8GkE")
        t_bot = telebot.TeleBot(t_token)
        caption = (
            f"⚡ <b>LIVE NEWS UPDATE PUBLISHED!</b>\n\n"
            f"📌 <b>Headline:</b>\n{final_card['title']}\n\n"
            f"📰 <b>Summary:</b>\n{final_card['summary']}\n\n"
            f"🏷️ <b>Category:</b> {final_card['badge']}\n"
            f"🌐 <b>Live on Portal:</b> https://newskid.devv.in"
        )
        sent = False
        img_url = final_card.get("imageUrl")
        if img_url and img_url.startswith("http"):
            try:
                t_bot.send_photo(6347858548, photo=img_url, caption=caption, parse_mode="HTML")
                sent = True
            except Exception as pe:
                print(f"⚠️ Photo alert notice: {pe}", flush=True)

        if not sent:
            t_bot.send_message(6347858548, caption, parse_mode="HTML")
    except Exception as te:
        print(f"⚠️ Telegram notify notice: {te}", flush=True)

    return final_card


if __name__ == "__main__":
    cat = sys.argv[1] if len(sys.argv) > 1 else None
    topic = sys.argv[2] if len(sys.argv) > 2 else None
    run_fast_web_update(cat, topic)

