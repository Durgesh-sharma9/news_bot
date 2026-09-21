import os
import sys
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Windows console UTF-8 fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = SCRIPT_DIR / "client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "youtube_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]


def authenticate_youtube():
    if not CLIENT_SECRET_FILE.exists():
        print(f"❌ Error: {CLIENT_SECRET_FILE.name} nahi mila!")
        return None

    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...", flush=True)
            creds.refresh(Request())
        else:
            print("\n" + "=" * 60, flush=True)
            print("🌐 BROWSER ME GOOGLE LOGIN WINDOW OPEN HO RAHI HAI...", flush=True)
            print("👉 Apne NEWS KID YouTube channel wale Google account se login karein aur 'Allow' karein!", flush=True)
            print("=" * 60 + "\n", flush=True)

            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"✅ Token successfully saved to: {TOKEN_FILE.name}!", flush=True)

    # Verify channel access
    try:
        youtube = build("youtube", "v3", credentials=creds)
        request = youtube.channels().list(part="snippet,contentDetails,statistics", mine=True)
        response = request.execute()
        items = response.get("items", [])
        if items:
            ch_title = items[0]["snippet"]["title"]
            ch_custom = items[0]["snippet"].get("customUrl", "")
            print("\n" + "=" * 60, flush=True)
            print("🎉 SUCCESS! Connected to YouTube Channel:", flush=True)
            print(f"   📺 Channel Name: {ch_title}", flush=True)
            print(f"   🔗 Handle: {ch_custom}", flush=True)
            print("🚀 Ab NEWS KID bot automatically YouTube Shorts upload karega!", flush=True)
            print("=" * 60 + "\n", flush=True)
            return youtube
        else:
            print("⚠️ Connected, but no channel found on this Google account.", flush=True)
    except Exception as e:
        print(f"⚠️ Channel verification note: {e}", flush=True)

    return None


if __name__ == "__main__":
    authenticate_youtube()
