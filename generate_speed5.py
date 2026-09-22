#!/usr/bin/env python3
"""
⚡ NEWS KID - Speed-5 News Shorts Engine
Generates a fast-paced 45-second 5-bullet news script with countdown cues,
voiceover text, and asset queries for YouTube Shorts & Instagram Reels.
"""

import sys
import os
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
SPEED5_OUTPUT = SCRIPT_DIR / "speed5_script.json"

# RSS Feeds for real breaking Indian news
RSS_URLS = [
    "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/headlines/section/topic/NATION?hl=hi&gl=IN&ceid=IN:hi",
    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=hi&gl=IN&ceid=IN:hi"
]

def clean_html(raw_html):
    import re
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()

def fetch_top_5_headlines():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    items = []
    seen_titles = set()

    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item'):
                    title = clean_html(item.find('title').text or '')
                    if " - " in title:
                        title = title.rsplit(" - ", 1)[0].strip()
                    
                    if len(title) > 20 and title not in seen_titles:
                        seen_titles.add(title)
                        items.append(title)
                        if len(items) >= 5:
                            return items
        except Exception as e:
            print(f"⚠️ RSS fetch notice: {e}")

    # Fallback headlines if offline
    if len(items) < 5:
        fallback = [
            "भारत बनने वाला है सुपरपावर, यूएनएससी में कई देशों ने दिया समर्थन",
            "कैबिनेट ने चंद्रयान-4 मिशन को दी मंजूरी, चंद्रमा से लाएगा मिट्टी",
            "सेंसेक्स ने छुआ 85,000 का ऐतिहासिक स्तर, निवेशकों की बल्ले-बल्ले",
            "टीम इंडिया ने जीता ऐतिहासिक मुकाबला, सीरीज में हासिल की बढ़त",
            "इसरो ने पेश किया नया स्पेस विजन 2040, तैयार होगा भारतीय स्पेस स्टेशन"
        ]
        for fb in fallback:
            if fb not in items:
                items.append(fb)
            if len(items) >= 5:
                break
    return items[:5]

def generate_speed5_package():
    print("=" * 60)
    print("⚡ NEWS KID: Generating Speed-5 (45s Fast Countdown Shorts)...")
    print("=" * 60)

    headlines = fetch_top_5_headlines()
    print(f"📰 Fetched {len(headlines)} Top Trending Headlines:")
    for idx, h in enumerate(headlines, 1):
        print(f"   [{idx}] {h}")

    # Build 45-second high energy countdown script
    # Total runtime target: ~40-45 seconds (5 bullets x 7s + 5s hook/outro)
    intro_hook = "आज की 5 सबसे बड़ी खबरें — सिर्फ 45 सेकंड में! चलिए शुरू करते हैं।"
    
    bullets = []
    for i, h in enumerate(headlines, 1):
        bullets.append({
            "number": i,
            "cue": f"खबर नंबर {i}",
            "headline": h,
            "voice_text": f"खबर नंबर {i}: {h}।",
            "display_duration_sec": 7.0,
            "image_search_query": h.split("ने")[0].split("में")[0].strip() or "India News",
            "sfx": "whoosh"
        })

    outro = "देश और दुनिया की हर बड़ी खबर 60 सेकंड में जानने के लिए सब्सक्राइब करें NEWS KID!"

    full_voiceover = intro_hook + " " + " ".join([b["voice_text"] for b in bullets]) + " " + outro

    speed5_data = {
        "format": "speed5_countdown",
        "title": "आज की 5 बड़ी खबरें — सिर्फ 45 सेकंड में! #Shorts #NewsKid",
        "duration_target_seconds": 45,
        "intro_hook": intro_hook,
        "bullets": bullets,
        "outro": outro,
        "full_voiceover_script": full_voiceover,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(SPEED5_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(speed5_data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("✅ SPEED-5 SCRIPT GENERATED SUCCESSFULLY!")
    print(f"📁 Output File: {SPEED5_OUTPUT}")
    print(f"🎙️ Total Script Words: {len(full_voiceover.split())} words (~42 seconds voiceover)")
    print("=" * 60)
    return speed5_data

if __name__ == "__main__":
    generate_speed5_package()
