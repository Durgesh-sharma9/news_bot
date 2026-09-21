import os
import sys
import json
from pathlib import Path

# Windows terminal UTF-8 encoding fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    TwoFactorRequired,
    PleaseWaitFewMinutes,
)

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
SESSION_PATH = SCRIPT_DIR / "ig_session.json"


def challenge_code_handler(username, choice):
    print(f"\n📩 Instagram has sent a security verification code via {choice}!", flush=True)
    code = input("👉 Enter the 6-digit code received on your phone/email: ").strip()
    return code


def main():
    if not CONFIG_PATH.exists():
        print("❌ config.json not found!", flush=True)
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    username = config.get("instagram_username", "news_kid_ig")
    password = config.get("instagram_password", "")

    if not username or not password:
        print("❌ instagram_username or instagram_password missing in config.json!", flush=True)
        return

    print("=" * 60, flush=True)
    print(f"🔐 Logging into Instagram account: @{username}", flush=True)
    print("=" * 60, flush=True)

    # Bypass deprecated Instagram QE expose endpoint
    Client.expose = lambda self, *args, **kwargs: {}

    cl = Client()
    cl.challenge_code_handler = challenge_code_handler

    try:
        if SESSION_PATH.exists():
            print("🔄 Found existing session, verifying...", flush=True)
            try:
                cl.load_settings(SESSION_PATH)
                cl.login(username, password)
                info = cl.account_info()
                print(f"✅ Existing session is valid! Connected as: @{info.username} (ID: {info.pk})", flush=True)
                return
            except Exception as e:
                print(f"⚠️ Existing session invalid ({e}), logging in fresh...", flush=True)

        print("🔑 Authenticating with username & password...", flush=True)
        cl.login(username, password)
        cl.dump_settings(SESSION_PATH)
        info = cl.account_info()
        print("=" * 60, flush=True)
        print(f"🎉 SUCCESS! Logged into Instagram as @{info.username}!", flush=True)
        print(f"🆔 User ID: {info.pk}", flush=True)
        print(f"💾 Session file saved to: {SESSION_PATH.name}", flush=True)
        print("=" * 60, flush=True)

    except TwoFactorRequired:
        print("⚠️ 2-Factor Authentication required!", flush=True)
        code = input("👉 Enter 2FA code from authenticator app / SMS: ").strip()
        cl.login(username, password, verification_code=code)
        cl.dump_settings(SESSION_PATH)
        print(f"🎉 SUCCESS! Logged in as @{username}!", flush=True)
        print(f"💾 Session saved to {SESSION_PATH.name}", flush=True)
    except ChallengeRequired as e:
        print(f"⚠️ Instagram Checkpoint / Challenge required: {e}", flush=True)
    except BadPassword:
        print("❌ Incorrect password! Please verify the Instagram password.", flush=True)
    except PleaseWaitFewMinutes:
        print("⚠️ Instagram rate limit: Please wait a few minutes before trying again.", flush=True)
    except Exception as e:
        print(f"❌ Login error: {e}", flush=True)


if __name__ == "__main__":
    main()
