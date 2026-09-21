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


ANCHOR_STATE_FILE = SCRIPT_DIR / "last_anchor.json"


def get_next_anchor_gender():
    """Strictly alternates between 'male' (Young Boy) and 'female' (Young Girl) every single video."""
    last_gender = "female"
    if ANCHOR_STATE_FILE.exists():
        try:
            with open(ANCHOR_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_gender = data.get("last_gender", "female")
        except Exception:
            pass

    next_gender = "male" if last_gender == "female" else "female"

    try:
        with open(ANCHOR_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_gender": next_gender}, f, indent=2)
    except Exception:
        pass

    return next_gender


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

    # Strictly alternate between Boy and Girl anchor on each video
    voice_gender = get_next_anchor_gender()
    anchor_title = "Cute & Soft Boy Anchor (स्मार्ट किड रिपोर्टर - Madhur)" if voice_gender == "male" else "Cute & Soft Girl Anchor (क्यूट किड रिपोर्टर - Swara)"
    print(f"🎙️ Selected Anchor: {voice_gender.upper()} -> {anchor_title}")

    if voice_gender == "male":
        anchor_persona = f"You are a cute, smart, and soft-spoken Young Boy News Anchor (Boy Reporter) hosting '{CHANNEL_NAME}'."
    else:
        anchor_persona = f"You are a cute, sweet, and soft-spoken Young Girl News Anchor (Girl Reporter) hosting '{CHANNEL_NAME}'."

    research_data = {
        "story_headline": headline,
        "story_context": details,
        "category": category,
        "voice_gender": voice_gender,
        "anchor_title": anchor_title
    }
    with open(RESEARCH_FILE, "w", encoding="utf-8") as f:
        json.dump(research_data, f, ensure_ascii=False, indent=2)

    prompt = f"""
{anchor_persona}
Your persona is polite, curious, and engaging—explaining real breaking news clearly and delightfully for young viewers and adults alike!
Create a tight, crisp, high-impact 35-42 second Hindi News Video Script on THIS ONE SINGLE BREAKING STORY. Total video duration MUST NOT exceed 45 seconds!

STORY HEADLINE: {headline}
CONTEXT / FACTS: {details}

STRICT INSHORTS & NEWS KID RULES:
1. Cover ONLY THIS SINGLE NEWS STORY. Do not mix any other news.
2. ABSOLUTE FORBIDDEN RULE: NEVER mention, speak, or write the name of any other news channel, brand, app, or agency (NEVER say or write Aaj Tak, NDTV, BBC, Inshorts, ABP, Zee, News18, ANI, PTI, etc.). If you mention any channel name, ONLY use '{CHANNEL_NAME}'.
3. ZERO INTRO AT START (SUPER CRITICAL):
   - In Scene 1: NEVER say "Namaskar", "Hello dosto", "Swagat hai", or "NEWS KID par badi khabar".
   - START DIRECTLY with the news bombshell in the very first second! (e.g. "सोनिया गांधी को कोर्ट से लगा बड़ा कानूनी झटका...", "आईआईटी बॉम्बे में छात्र की मौत पर मचा भारी बवाल...").
4. OUTRO & WEBSITE REDIRECTION AT THE VERY END (SCENE 4 ONLY):
   - In Scene 4, the anchor MUST invite viewers to read the full report on the official website:
   - Example voiceover: "...इस खबर की पूरी रिपोर्ट और लाइव अपडेट्स के लिए अभी विजिट करें newskid.devv.in!"
   - Scene 4 caption_text MUST be: "विजिट करें: newskid.devv.in"
5. Tone: Fast, crisp, smart young anchor. Direct, punchy, high-retention delivery.
6. STRICT LENGTH & WORD COUNT RULE (MAX 35 SECONDS TOTAL):
   - Exactly 4 scenes.
   - Each scene's voice_text MUST be SHORT: only 14 to 17 Hindi words per scene!
   - Total words across all 4 scenes combined MUST be between 55 and 68 words!
   - Scene 1: Direct news bombshell (Starts immediately with the incident).
   - Scene 2: Exact key fact, decision, or statement.
   - Scene 3: Impact or reaction.
   - Scene 4: Question + Call-to-Action to visit website ("...पूरी रिपोर्ट के लिए अभी विजिट करें newskid.devv.in!").
7. Caption text: Short 3-5 words in Devanagari Hindi for TV screen ticker.
8. image_query (SUPER IMPORTANT): MUST BE THE EXACT REAL ENGLISH NAME of the main person, organization, building, rocket, court, or city in this specific news story so real-life news press photos are downloaded.
   - Examples: "Narendra Modi speech", "Supreme Court of India New Delhi", "Donald Trump press conference", "ISRO rocket launch"
   - NEVER use generic words like "news" or "technology".
9. SFX per scene: choose from ["boom", "camera_click", "whoosh_deep", "ding"].
10. PRONUNCIATION & SCRIPTING RULE FOR AI ANCHOR (SUPER CRITICAL):
    - All numbers MUST be written in natural Hindi words (e.g. write 'पचासी हज़ार' instead of '85000', 'दो-शून्य' instead of '2-0', 'एक सौ अस्सी' instead of '180', 'दो हज़ार अट्ठाईस' instead of '2028', 'चार' instead of '4').
    - English acronyms and names MUST be written in natural Devanagari Hindi for flawless TV anchor pronunciation (e.g. write 'इसरो' instead of 'ISRO', 'एआई' instead of 'AI', 'ओपन-एआई' instead of 'OpenAI', 'सीएम' instead of 'CM', 'पीएम' instead of 'PM', 'कैबिनेट' instead of 'Cabinet', 'सेशन कोर्ट' instead of 'Sessions Court').

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

    api_keys = config.get("gemini_api_keys", [GEMINI_API_KEY])
    if isinstance(api_keys, str):
        api_keys = [api_keys]

    MODELS_TO_TRY = ['gemini-3.6-flash', 'gemini-3.1-flash-lite', 'gemini-3.7-flash', 'gemini-3.5-flash-lite']
    clean_text = None

    for k_idx, key in enumerate(api_keys, 1):
        genai.configure(api_key=key)
        for m_name in MODELS_TO_TRY:
            try:
                print(f"  🤖 Connecting to Gemini ({m_name}) using Key #{k_idx}...")
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt)
                clean_text = response.text.strip()
                if clean_text.startswith("```"):
                    clean_text = re.sub(r"^```(?:json)?\n?", "", clean_text)
                    clean_text = re.sub(r"\n?```$", "", clean_text)
                clean_text = clean_text.strip()
                break
            except Exception as e:
                print(f"  ⚠️ Key #{k_idx} with {m_name} failed ({e}), trying next...")
                continue
        if clean_text:
            break

    if not clean_text:
        print("❌ Error: Koi bhi Gemini key ya model connect nahi ho paya.")
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
