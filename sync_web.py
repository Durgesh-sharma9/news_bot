import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

# Windows UTF-8 fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
SCRIPT_FILE = SCRIPT_DIR / "script.json"
IMAGE_FILE = SCRIPT_DIR / "images" / "scene_0.jpg"
WEB_FEED_FILE = SCRIPT_DIR / "web_feed.json"

# Load Config
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

MONGODB_URI = config.get("mongodb_uri", "")
IMAGEKIT_PUBLIC_KEY = config.get("imagekit_public_key", "")
IMAGEKIT_PRIVATE_KEY = config.get("imagekit_private_key", "")
IMAGEKIT_URL_ENDPOINT = config.get("imagekit_url_endpoint", "")
WEB_API_URL = config.get("web_api_url", "http://localhost:3000/api/news")


def upload_to_imagekit(file_path, file_name, folder="/newskid_cards/"):
    """Uploads a file (image or audio) to ImageKit.io CDN."""
    if not IMAGEKIT_PRIVATE_KEY:
        return None

    try:
        from imagekitio import ImageKit
        imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)

        with open(file_path, "rb") as f:
            upload = imagekit.files.upload(
                file=f,
                file_name=file_name,
                folder=folder,
                use_unique_file_name=True,
                tags=["newskid", "news_media"]
            )
            return getattr(upload, "url", None)
    except Exception as e:
        print(f"  ⚠️ ImageKit Upload warning: {e}")
        return None


def sync_card_to_web():
    print("\n" + "="*55)
    print("🌐 SYNCING NEWS CARD TO NEWS KID WEB PORTAL")
    print("="*55)

    if not SCRIPT_FILE.exists():
        print(f"❌ {SCRIPT_FILE} nahi mila! Pehle video generate karein.")
        return False

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    title = script_data.get("title", "Breaking News Update")
    badge = script_data.get("badge", "🔴 बड़ी खबर")
    category = script_data.get("category", "breaking")
    scenes = script_data.get("scenes", [])

    # Combine scenes into Inshorts 60-word summary
    summary_parts = [s.get("voice_text", "").strip() for s in scenes if s.get("voice_text")]
    full_summary = " ".join(summary_parts)

    # Clean out any trailing outro for web reading
    full_summary = full_summary.replace("ऐसी ही हर खबर के लिए देखते रहिए NEWS KID!", "").strip()

    # Step 1: Upload All Real Scene Photos to ImageKit CDN for Image Gallery
    cdn_images = []
    images_dir = SCRIPT_DIR / "images"
    candidates = sorted([images_dir / f"scene_{i}.jpg" for i in range(4)], key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
    valid_candidates = [p for p in candidates if p.exists() and p.stat().st_size > 20000]

    if not valid_candidates and IMAGE_FILE.exists():
        valid_candidates = [IMAGE_FILE]

    for idx, img_path in enumerate(valid_candidates[:3]):
        print(f"  📸 Uploading Real News Photo {idx+1}/{len(valid_candidates[:3])} ({img_path.name}) to ImageKit CDN...")
        file_slug = f"news_{int(datetime.now().timestamp())}_{idx}.jpg"
        url = upload_to_imagekit(img_path, file_slug, folder="/newskid_cards/")
        if url:
            cdn_images.append(url)

    if not cdn_images:
        cdn_images = ["https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1080&q=80"]

    cdn_image_url = cdn_images[0]
    print(f"  ✅ {len(cdn_images)} News Photos uploaded to ImageKit for Card Gallery!")

    # Step 1.5: Upload Studio AI Anchor Voiceover to ImageKit CDN
    cdn_audio_url = ""
    voice_file = SCRIPT_DIR / "voiceover.mp3"
    if voice_file.exists() and voice_file.stat().st_size > 5000:
        print(f"  🎙️ Uploading Studio AI Anchor Audio ({voice_file.name}) to ImageKit CDN...")
        audio_slug = f"voice_{int(datetime.now().timestamp())}.mp3"
        cdn_audio_url = upload_to_imagekit(voice_file, audio_slug, folder="/newskid_audio/")
        if cdn_audio_url:
            print(f"  ✅ Studio Audio uploaded to ImageKit: {cdn_audio_url}")

    # Build the Card Object (Bilingual ready)
    card_doc = {
      "title": title,
      "title_en": script_data.get("title_en", title),
      "summary": full_summary,
      "summary_en": script_data.get("summary_en", full_summary),
      "category": category,
      "badge": badge,
      "imageUrl": cdn_image_url,
      "images": cdn_images,
      "audioUrl": cdn_audio_url or "",
      "source": "NEWS KID Verified",
      "publishedAt": datetime.now(timezone.utc).isoformat(),
      "views": 1,
      "likes": 0
    }

    # Step 2: Push to MongoDB Atlas (if configured)
    mongo_synced = False
    if MONGODB_URI:
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
            db = client["newskid"]
            res = db["cards"].insert_one(card_doc.copy())
            print(f"  ✅ Saved to MongoDB Atlas (ID: {res.inserted_id})")
            mongo_synced = True
        except Exception as e:
            print(f"  ⚠️ MongoDB Atlas connection error: {e}")

    # Step 3: Send to local/live Next.js Web API (if server running)
    api_synced = False
    try:
        resp = requests.post(WEB_API_URL, json=card_doc, timeout=3)
        if resp.status_code == 200:
            print(f"  ✅ Synced directly to Next.js API ({WEB_API_URL})")
            api_synced = True
    except Exception:
        pass

    # Step 4: Always append to local web_feed.json for offline backup
    feed = []
    if WEB_FEED_FILE.exists():
        try:
            with open(WEB_FEED_FILE, "r", encoding="utf-8") as f:
                feed = json.load(f)
        except Exception:
            pass

    feed.insert(0, card_doc)
    if len(feed) > 50:
        feed = feed[:50]

    with open(WEB_FEED_FILE, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print("\n🎉 WEB SYNC COMPLETE!")
    print(f"📌 Headline: {title}")
    print(f"🏷️ Category: {category.upper()} ({badge})")
    print(f"📄 Local Feed Backup: {WEB_FEED_FILE.name}")

    if not (MONGODB_URI and IMAGEKIT_PUBLIC_KEY):
        print("\n💡 TIP: To enable 100% Cloud MongoDB Atlas & ImageKit sync, add:")
        print("   \"mongodb_uri\": \"mongodb+srv://...\"")
        print("   \"imagekit_public_key\": \"...\"")
        print("   to your news_bot/config.json!\n")

    return True


if __name__ == "__main__":
    sync_card_to_web()
