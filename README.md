# 📰 FastNews AI Bot (@News998889bot)

High-retention AI Vertical News Video Generator that converts real-time breaking news into vertical video shorts in seconds using **real news photos + news anchor voiceover + safe-zone subtitles + zero video downloads**.

---

## ⚡ Key Highlights
- **Zero Video Downloads**: Uses real-life HD photos from live news events instead of heavy generic stock video clips.
- **News Anchor Voice**: Natural Hindi voiceover (`hi-IN-MadhurNeural`) tuned for news pacing.
- **TV Style Graphics**: Top breaking news red ticker banner (`🔴 BREAKING NEWS | FastNews AI`) and high-visibility subtitles.
- **Telegram Bot Integration**: Controlled directly via `@News998889bot`.

---

## 🚀 How to Run Locally

### 1. Run Pipeline from Command Line:
```bash
python run_news.py "Chandrayaan 4 Mission ISRO"
```
Or for breaking news:
```bash
python run_news.py "Latest Breaking News India"
```

### 2. Run Telegram Bot:
Double-click `start_news_bot.bat` or run:
```bash
python telegram_news_bot.py
```

### 3. Telegram Commands:
- `/start` : Open category menu (Breaking News, Tech, National, Business, Sports)
- `/news <topic>` : Generate news video on any topic
- `/breaking` : Auto-fetch #1 top headline from Google News RSS and create video

---

## 📁 Pipeline Components:
- `step1_news_script.py`: Google News RSS + Gemini AI script & scene builder.
- `step2_voiceover.py`: Edge-TTS audio generation & word-level timing mapping.
- `step3_download_images.py`: Fast real news photo downloader (DuckDuckGo / Pexels).
- `step4_merge_news_video.py`: MoviePy 1080x1920 compositor with Ken Burns zoom, subtitles, and SFX.
- `telegram_news_bot.py`: Telegram polling bot for `@News998889bot`.
