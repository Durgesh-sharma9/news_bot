import os
import sys
import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
import google.generativeai as genai

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
SCRIPT_FILE = SCRIPT_DIR / "script.json"
RESEARCH_FILE = SCRIPT_DIR / "research.json"

# Load Config
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

GEMINI_API_KEY = config.get("gemini_api_key", "AQ.Ab8RN6ISrNgLMM1eooye8FS0QTYH3DMTYT-SkWMKiZw8jrKcrg")
genai.configure(api_key=GEMINI_API_KEY)


def fetch_google_news_rss(topic=None):
    """Fetch latest top headlines or topic news from Google News RSS."""
    try:
        if topic:
            encoded = urllib.parse.quote(f"{topic} news India")
            url = f"https://news.google.com/rss/search?q={encoded}&hl=hi&gl=IN&ceid=IN:hi"
        else:
            url = "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall(".//item")[:5]:
            title_elem = item.find("title")
            desc_elem = item.find("description")
            title = title_elem.text if title_elem is not None else ""
            desc = desc_elem.text if desc_elem is not None else ""
            clean_desc = re.sub(r'<[^>]+>', '', desc)
            items.append(f"- {title}: {clean_desc}")

        return "\n".join(items)
    except Exception as e:
        print(f"⚠️ RSS Fetch error: {e}")
        return ""


def generate_news_script(topic="Breaking News India", category="National"):
    print("\n" + "="*55)
    print(f"📰 FETCHING & GENERATING NEWS SCRIPT: {topic}")
    print("="*55)

    rss_context = fetch_google_news_rss(topic)
    research_data = {"topic": topic, "rss_context": rss_context}
    with open(RESEARCH_FILE, "w", encoding="utf-8") as f:
        json.dump(research_data, f, ensure_ascii=False, indent=2)

    prompt = f"""
You are a senior TV News Anchor and Inshorts lead editor.
Create an energetic, engaging 40-50 second Hindi News Short Video Script on this topic.

TOPIC: {topic}
LIVE CONTEXT / HEADLINES:
{rss_context if rss_context else "Cover the latest factual updates on this topic."}

RULES:
1. Language: Conversational, energetic Hindi (Devanagari script) like a TV News anchor (Aaj Tak, Inshorts, NDTV).
2. Badge: 2-3 words breaking alert (e.g. "🔴 बड़ी खबर", "🚀 टेक अपडेट", "🇮🇳 भारत का गौरव", "⚠️ चेतावनी").
3. Exactly 4 or 5 scenes. Total voiceover duration should be ~40-45 seconds.
4. Voice text: Clear, punchy, factual facts. No filler words.
5. Caption text: Short 4-7 words in Devanagari Hindi for screen captions.
6. Image query: MUST BE EXTREMELY ACCURATE for real news photos (person name, place, event, launch, building). English queries only.
7. SFX: choose from ["boom", "camera_click", "whoosh", "ding"].

OUTPUT STRICTLY VALID JSON ONLY (No markdown backticks, no other text):
{{
  "topic": "{topic}",
  "title": "Catcy News Headline in Hindi (under 60 chars)",
  "badge": "🔴 बड़ी खबर",
  "category": "{category}",
  "scenes": [
    {{
      "voice_text": "Hindi anchor narration for scene 1",
      "caption_text": "Short caption in Devanagari",
      "image_query": "specific real photo search query in english",
      "sfx": "boom"
    }}
  ]
}}
"""

    MODELS_TO_TRY = ['gemini-3.1-flash-lite', 'gemini-3.5-flash-lite', 'gemini-3.7-flash', 'gemini-3.6-flash']
    clean_text = None

    for m_name in MODELS_TO_TRY:
        try:
            print(f"  🤖 Connecting to Gemini model: {m_name}...")
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            clean_text = response.text.strip()
            if clean_text.startswith("```"):
                clean_text = re.sub(r"^```(?:json)?\n?", "", clean_text)
                clean_text = re.sub(r"\n?```$", "", clean_text)
            clean_text = clean_text.strip()
            break
        except Exception as e:
            print(f"  ⚠️ {m_name} failed ({e}), trying next...")
            continue

    if not clean_text:
        print("❌ Error: Koi bhi Gemini model connect nahi ho paya.")
        sys.exit(1)

    script_data = json.loads(clean_text)

    with open(SCRIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"✅ News Script Generated Successfully!")
    print(f"📌 Headline: {script_data.get('title')}")
    print(f"🏷️ Badge   : {script_data.get('badge')}")
    print(f"🎬 Scenes  : {len(script_data.get('scenes', []))} scenes ready\n")
    return script_data


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "ISRO Gaganyaan Mission 2026"
    generate_news_script(t)
