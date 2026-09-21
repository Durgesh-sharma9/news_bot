import os
import sys
import json
import re
import random
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
USED_NEWS_FILE = SCRIPT_DIR / "used_news.json"

# Load Config
config = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception:
        pass

GEMINI_API_KEY = config.get("gemini_api_key", "AQ.Ab8RN6ISrNgLMM1eooye8FS0QTYH3DMTYT-SkWMKiZw8jrKcrg")
CHANNEL_NAME = config.get("news_channel_name", "NEWS KID")
genai.configure(api_key=GEMINI_API_KEY)

CATEGORY_FEEDS = {
    "breaking": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi",
    "national": "https://news.google.com/rss/headlines/section/topic/NATION?hl=hi&gl=IN&ceid=IN:hi",
    "tech": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=hi&gl=IN&ceid=IN:hi",
    "business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=hi&gl=IN&ceid=IN:hi",
    "sports": "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=hi&gl=IN&ceid=IN:hi",
    "world": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=hi&gl=IN&ceid=IN:hi"
}


def load_used_news():
    if USED_NEWS_FILE.exists():
        try:
            with open(USED_NEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_used_news(title):
    used = load_used_news()
    used.append(title)
    if len(used) > 100:
        used = used[-100:]
    with open(USED_NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def clean_headline_source(raw_title):
    """Strips trailing external news channel/source name (e.g. ' - Aaj Tak', ' - BBC', ' - News18')."""
    cleaned = re.sub(r'\s*[-–|]\s*[^-–|]+$', '', raw_title).strip()
    return cleaned if cleaned else raw_title


def fetch_single_breaking_story(category="breaking", custom_topic=None):
    """
    Inshorts Model: Extracts ONE single top real news story.
    Returns: (headline, description, source_url)
    """
    used = load_used_news()

    if custom_topic and custom_topic.lower() not in ["auto", "breaking", "breaking news", "latest breaking news india"]:
        # Custom topic search
        encoded = urllib.parse.quote(f"{custom_topic} news India")
        url = f"https://news.google.com/rss/search?q={encoded}&hl=hi&gl=IN&ceid=IN:hi"
    else:
        url = CATEGORY_FEEDS.get(category.lower(), CATEGORY_FEEDS["breaking"])

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = root.findall(".//item")

        # Pick top unused story
        for item in items[:10]:
            title_elem = item.find("title")
            desc_elem = item.find("description")
            raw_title = title_elem.text if title_elem is not None else ""
            desc = desc_elem.text if desc_elem is not None else ""
            clean_desc = re.sub(r'<[^>]+>', '', desc).strip()
            headline = clean_headline_source(raw_title)

            # Skip if already used recently
            if any(headline in u or u in headline for u in used):
                continue

            save_used_news(headline)
            return headline, clean_desc

        # If all used, pick first
        if items:
            t = clean_headline_source(items[0].find("title").text)
            d = re.sub(r'<[^>]+>', '', items[0].find("description").text or "").strip()
            return t, d

    except Exception as e:
        print(f"⚠️ RSS Fetch error: {e}")

    # Fallback if offline
    fallback_title = custom_topic if custom_topic else "भारत का नया वैज्ञानिक कीर्तिमान"
    return fallback_title, "देश में विज्ञान और तकनीक के क्षेत्र में एक नया मील का पत्थर हासिल हुआ है।"


def generate_news_script(topic="breaking", category="breaking"):
    print("\n" + "="*55)
    print(f"📰 INSHORTS REAL-TIME NEWS ENGINE")
    print(f"   Topic/Category: {topic}")
    print("="*55)

    headline, details = fetch_single_breaking_story(category=category, custom_topic=topic)
    print(f"\n⚡ TOP BREAKING STORY IDENTIFIED:")
    print(f"   👉 \"{headline}\"")
    print(f"   ℹ️ Context: {details[:120]}...\n")

    # Alternate or pick gender dynamically
    voice_gender = random.choice(["female", "male"])
    print(f"🎙️ Selected Anchor Gender: {voice_gender.upper()} ({'Swara' if voice_gender == 'female' else 'Madhur'})")

    research_data = {
        "story_headline": headline,
        "story_context": details,
        "category": category,
        "voice_gender": voice_gender
    }
    with open(RESEARCH_FILE, "w", encoding="utf-8") as f:
        json.dump(research_data, f, ensure_ascii=False, indent=2)

    prompt = f"""
You are a cute, smart, and soft-spoken Young News Anchor hosting '{CHANNEL_NAME}'.
Your persona is sweet, polite, curious, and engaging—explaining real breaking news clearly and delightfully for young viewers and adults alike!
Create a tight, crisp, high-impact 35-42 second Hindi News Video Script on THIS ONE SINGLE BREAKING STORY. Total video duration MUST NOT exceed 45 seconds!

STORY HEADLINE: {headline}
CONTEXT / FACTS: {details}

STRICT INSHORTS & NEWS KID RULES:
1. Cover ONLY THIS SINGLE NEWS STORY. Do not mix any other news.
2. ABSOLUTE FORBIDDEN RULE: NEVER mention, speak, or write the name of any other news channel, brand, app, or agency (NEVER say or write Aaj Tak, NDTV, BBC, Inshorts, ABP, Zee, News18, ANI, PTI, etc.). If you mention any channel name, ONLY use '{CHANNEL_NAME}'.
3. Tone: Cute, soft-spoken, clear, and friendly young anchor. Warm, pleasant, and delightful Hindi delivery.
4. STRICT LENGTH & WORD COUNT RULE (CRITICAL - MAX 45 SECONDS TOTAL):
   - Exactly 4 scenes.
   - Each scene's voice_text MUST be SHORT: only 15 to 18 Hindi words per scene! (Do NOT write long sentences).
   - Total words across all 4 scenes combined MUST be between 65 and 75 words!
   - Scene 1: Sweet young hook ("NEWS KID par badi khabar...").
   - Scene 2: Key fact or statement.
   - Scene 3: Impact or reaction.
   - Scene 4: Sweet sign-off / engaging question.
5. Caption text: Short 3-5 words in Devanagari Hindi for TV screen ticker.
6. image_query (SUPER IMPORTANT): MUST BE THE EXACT REAL ENGLISH NAME of the main person, organization, building, rocket, court, or city in this specific news story so real-life news press photos are downloaded.
   - Examples: "Narendra Modi speech", "Supreme Court of India New Delhi", "Donald Trump press conference", "ISRO rocket launch"
   - NEVER use generic words like "news" or "technology".
7. SFX per scene: choose from ["boom", "camera_click", "whoosh_deep", "ding"].

OUTPUT STRICTLY VALID JSON ONLY (No markdown, no extra text):
{{
  "topic": "{headline}",
  "title": "{headline[:55]}",
  "badge": "🔴 बड़ी खबर",
  "category": "{category}",
  "voice_gender": "{voice_gender}",
  "scenes": [
    {{
      "voice_text": "Hindi anchor narration for scene 1",
      "caption_text": "Short caption in Devanagari",
      "image_query": "specific real person place or event in english",
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
    script_data["voice_gender"] = voice_gender

    with open(SCRIPT_FILE, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ News Script Generated Successfully!")
    print(f"📌 Headline : {script_data.get('title')}")
    print(f"🏷️ Badge    : {script_data.get('badge')}")
    print(f"🎙️ Anchor   : {voice_gender.upper()} Voice")
    print(f"🎬 Scenes   : {len(script_data.get('scenes', []))} scenes ready\n")
    return script_data


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "breaking"
    c = sys.argv[2] if len(sys.argv) > 2 else "breaking"
    generate_news_script(t, c)
