import os
import sys
import json
import time
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# Windows console UTF-8 fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = SCRIPT_DIR / "youtube_token.json"
SCRIPT_FILE = SCRIPT_DIR / "script.json"
VIDEO_PATH = SCRIPT_DIR / "final_news.mp4"
OUTPUT_LOG = SCRIPT_DIR / "last_youtube_upload.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]


def upload_news_short(video_path=None, custom_title=None, custom_desc=None):
    if not video_path:
        video_path = VIDEO_PATH
    video_path = Path(video_path)

    if not video_path.exists():
        print(f"❌ Video file nahi mili: {video_path}", flush=True)
        return None

    if not TOKEN_FILE.exists():
        print(f"❌ YouTube Token nahi mila! Pehle 'python news_bot/setup_youtube.py' run karein.", flush=True)
        return None

    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    youtube = build("youtube", "v3", credentials=creds)

    # Load metadata from script.json
    title = "NEWS KID Breaking News #Shorts"
    summary = ""
    category = "breaking"
    if SCRIPT_FILE.exists():
        try:
            with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                title = sdata.get("title", title)
                scenes = sdata.get("scenes", [])
                summary = " ".join([s.get("voice_text", "") for s in scenes if s.get("voice_text")][:2])
                category = sdata.get("category", "breaking")
        except Exception:
            pass

    if custom_title:
        title = custom_title

    # YouTube Shorts Title constraint (max 100 chars, include #shorts)
    if "#shorts" not in title.lower() and "#short" not in title.lower():
        title = f"{title[:85]} #shorts"

    tags = [
        "newskid", "breaking news", "news shorts", "hindi news",
        "current affairs", "daily news", "shorts", category
    ]

    description = custom_desc or (
        f"⚡ {title}\n\n"
        f"📰 {summary[:200]}...\n\n"
        f"🌐 Read the full verified story 24/7 on our Live Web Portal:\n"
        f"👉 https://newskid.devv.in\n\n"
        f"📸 Instagram: https://instagram.com/news_kid_ig\n"
        f"📘 Facebook: https://facebook.com/profile.php?id=61594353583927\n"
        f"👉 Subscribe to NEWS KID for daily 60-second verified news updates!\n\n"
        f"#newskid #shorts #news #breakingnews #india"
    )

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "25"  # News & Politics
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    print("=" * 60, flush=True)
    print(f"📺 Uploading Short to NEW YouTube Channel (NEWS KID)...", flush=True)
    print(f"   Title: {title}", flush=True)
    print("=" * 60, flush=True)

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  ⏳ Upload Progress: {int(status.progress() * 100)}%", flush=True)

    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"

    print("=" * 60, flush=True)
    print(f"🎉 YOUTUBE SHORT PUBLISHED SUCCESSFULLY!", flush=True)
    print(f"👉 Watch Video: {video_url}", flush=True)
    print("=" * 60, flush=True)

    result_data = {
        "video_id": video_id,
        "video_url": video_url,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(OUTPUT_LOG, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

    return result_data


if __name__ == "__main__":
    upload_news_short()
