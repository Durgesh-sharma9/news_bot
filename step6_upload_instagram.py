import os
import sys
import json
import time
from pathlib import Path

# Windows terminal UTF-8 encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

from instagrapi import Client

SCRIPT_DIR = Path(__file__).resolve().parent
SESSION_PATH = SCRIPT_DIR / "ig_session.json"
SCRIPT_JSON_PATH = SCRIPT_DIR / "script.json"
VIDEO_PATH = SCRIPT_DIR / "final_news.mp4"
OUTPUT_LOG = SCRIPT_DIR / "last_instagram_upload.json"
COVER_PATH = SCRIPT_DIR / "reel_cover.jpg"


def upload_news_reel(video_path=None, custom_caption=None):
    if not video_path:
        video_path = VIDEO_PATH
    video_path = Path(video_path)

    if not video_path.exists():
        print(f"❌ Video not found at {video_path}!", flush=True)
        return None

    if not SESSION_PATH.exists():
        print(f"❌ Instagram session not found ({SESSION_PATH.name})! Run setup_instagram.py first.", flush=True)
        return None

    # Load script metadata for caption
    title = "NEWS KID Breaking Update"
    summary = ""
    category = "breaking"
    if SCRIPT_JSON_PATH.exists():
        try:
            with open(SCRIPT_JSON_PATH, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                title = sdata.get("title", title)
                scenes = sdata.get("scenes", [])
                summary = " ".join([s.get("voice_text", "") for s in scenes if s.get("voice_text")][:2])
                category = sdata.get("category", "breaking")
        except Exception:
            pass

    # Category-Specific High-Traffic Hashtag Bank (Instagram Search Optimized)
    CATEGORY_TAGS = {
        "breaking": ["#breakingnews", "#latestnews", "#viralreels", "#india", "#currentaffairs", "#newsupdate", "#trendingreels"],
        "national": ["#nationalnews", "#indianpolitics", "#bharat", "#delhi", "#upsc", "#currentaffairs2026", "#indiaelection", "#modi"],
        "tech": ["#technews", "#technology", "#artificialintelligence", "#ai", "#gadgets", "#futuretech", "#smartphone", "#apple"],
        "business": ["#businessnews", "#stockmarket", "#sensex", "#nifty", "#finance", "#money", "#indianeconomy", "#marketcrash"],
        "sports": ["#sportsnews", "#cricket", "#teamindia", "#ipl", "#viratkohli", "#rohitsharma", "#bcci", "#sportsupdate"],
        "world": ["#worldnews", "#internationalnews", "#globalnews", "#geopolitics", "#worldaffairs", "#america", "#russia"]
    }

    # Universal Discovery Anchors
    discovery_anchors = ["#newskid", "#reelsindia", "#reels", "#explorepage", "#viral", "#shorts"]

    # Build editorial news caption
    if not custom_caption:
        niche_tags = CATEGORY_TAGS.get(category, CATEGORY_TAGS["breaking"])
        all_tags = list(dict.fromkeys(discovery_anchors + niche_tags))
        hashtags_str = " ".join(all_tags)

        custom_caption = (
            f"⚡ {title}\n\n"
            f"📰 {summary[:150]}...\n\n"
            f"🌐 Read full story 24/7 on our Live Portal:\n"
            f"👉 https://newskid.devv.in\n\n"
            f"📘 Facebook: https://facebook.com/profile.php?id=61594353583927\n"
            f"👉 Follow @news_kid_ig for daily 60-second verified news! 🚀\n"
            f"📌 Save this Reel & share with friends!\n"
            f"💬 Is par aapki kya rai hai? Comment mein batayein! 👇\n\n"
            f".\n.\n"
            f"{hashtags_str}"
        )

    # Extract high-definition cover frame
    if not COVER_PATH.exists() and video_path.exists():
        try:
            import subprocess
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [
                ffmpeg_bin, "-y", "-ss", "00:00:01", "-i", str(video_path),
                "-vframes", "1", "-q:v", "2", str(COVER_PATH)
            ]
            subprocess.run(cmd, capture_output=True)
        except Exception as e:
            print(f"⚠️ Cover extraction notice: {e}", flush=True)

    thumbnail_arg = COVER_PATH if (COVER_PATH.exists() and COVER_PATH.stat().st_size > 0) else None

    print("=" * 60, flush=True)
    print(f"📸 Uploading News Reel to Instagram: @news_kid_ig", flush=True)
    print(f"   Headline: {title}", flush=True)
    if thumbnail_arg:
        print(f"   Cover Frame: {thumbnail_arg.name} ({thumbnail_arg.stat().st_size // 1024} KB)", flush=True)
    print("=" * 60, flush=True)

    # Bypass deprecated Instagram QE expose endpoint
    Client.expose = lambda self, *args, **kwargs: {}

    cl = Client()
    try:
        cl.load_settings(SESSION_PATH)
        print("🔄 Uploading video as Reel to @news_kid_ig (+ Auto Share to Facebook Page News KID)...", flush=True)
        try:
            media = cl.clip_upload(
                path=video_path,
                caption=custom_caption,
                thumbnail=thumbnail_arg,
                share_to_facebook=True,
                fb_destination_id="61594353583927",
                fb_destination_type="PAGE"
            )
        except Exception as fb_err:
            print(f"⚠️ Direct fb_destination notice ({fb_err}), proceeding with standard clip_upload...", flush=True)
            media = cl.clip_upload(
                path=video_path,
                caption=custom_caption,
                thumbnail=thumbnail_arg
            )
        reel_code = media.code
        reel_url = f"https://www.instagram.com/reel/{reel_code}/"
        print("=" * 60, flush=True)
        print(f"🎉 INSTAGRAM REEL PUBLISHED SUCCESSFULLY!", flush=True)
        print(f"👉 Reel URL: {reel_url}", flush=True)
        print("=" * 60, flush=True)

        # Algorithm Booster: Creator comment to spur audience discussion
        try:
            cl.media_comment(media.id, "⚡ देश और दुनिया की हर ताज़ा खबर 60 सेकंड में जानने के लिए @news_kid_ig को फॉलो करें! इस खबर पर आपकी क्या राय है? 👇")
            print("💬 Algorithm comment booster posted!", flush=True)
        except Exception:
            pass

        result_data = {
            "reel_code": reel_code,
            "reel_url": reel_url,
            "media_pk": media.pk,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)

        return result_data
    except Exception as e:
        print(f"❌ Instagram upload failed: {e}", flush=True)
        return None


if __name__ == "__main__":
    upload_news_reel()
