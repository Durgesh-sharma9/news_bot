import os
import sys
import json
import re
from pathlib import Path
import requests
from PIL import Image, ImageFilter

try:
    import ddgs
except ImportError:
    ddgs = None

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
TIMING_FILE = SCRIPT_DIR / "voiceover_timing.json"
IMAGES_DIR = SCRIPT_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

TARGET_W = 1080
TARGET_H = 1920

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def search_ddg_images(query, max_results=5):
    """Searches high-res news photos via DuckDuckGo."""
    if not ddgs:
        return []
    try:
        ddg = ddgs.DDGS()
        results = list(ddg.images(query, max_results=max_results))
        urls = []
        for r in results:
            img_url = r.get("image")
            if img_url and img_url.startswith("http"):
                urls.append(img_url)
        return urls
    except Exception:
        return []


def search_bing_images(query, max_results=5):
    """Fallback high-resolution image search via Bing Images Async API."""
    try:
        url = f"https://www.bing.com/images/async?q={requests.utils.quote(query)}&first=0&count={max_results}&mmasync=1"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', resp.text)
            if not murls:
                murls = re.findall(r'"murl":"(http[^"]+)"', resp.text)
            return murls[:max_results]
    except Exception:
        pass
    return []


def download_and_format_image(candidate_urls, output_path):
    """Tries candidate URLs, downloads valid photo, and formats to 1080x1920 with blurred cinematic backdrop."""
    raw_path = output_path.with_suffix(".raw.jpg")

    for url in candidate_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8, stream=True)
            if resp.status_code == 200:
                with open(raw_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)

                with Image.open(raw_path) as raw:
                    raw = raw.convert("RGB")
                    w, h = raw.size
                    if w < 250 or h < 250:
                        continue

                    # Create blurred backdrop to fill 1080x1920
                    bg_scale = max(TARGET_W / w, TARGET_H / h)
                    bg = raw.resize((int(w * bg_scale), int(h * bg_scale)), Image.LANCZOS)
                    bg_w, bg_h = bg.size
                    bg = bg.crop(((bg_w - TARGET_W) // 2, (bg_h - TARGET_H) // 2,
                                  (bg_w + TARGET_W) // 2, (bg_h + TARGET_H) // 2))
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=25))

                    # Foreground scaled to fit width cleanly
                    fg_scale = min(TARGET_W / w, (TARGET_H * 0.75) / h)
                    fg_w = int(w * fg_scale)
                    fg_h = int(h * fg_scale)
                    fg = raw.resize((fg_w, fg_h), Image.LANCZOS)

                    pos_x = (TARGET_W - fg_w) // 2
                    pos_y = (TARGET_H - fg_h) // 2
                    bg.paste(fg, (pos_x, pos_y))

                    bg.save(output_path, quality=95)

                if raw_path.exists():
                    raw_path.unlink()
                return True
        except Exception:
            continue

    if raw_path.exists():
        raw_path.unlink()
    return False


def download_news_images():
    print("\n" + "="*55)
    print("📸 DOWNLOADING REAL NEWS IMAGES (ZERO VIDEOS)")
    print("="*55)

    if not TIMING_FILE.exists():
        print(f"❌ {TIMING_FILE} nahi mila!")
        sys.exit(1)

    with open(TIMING_FILE, "r", encoding="utf-8") as f:
        timing_data = json.load(f)

    scenes = timing_data.get("scenes", [])
    ready_images = []

    for idx, scene in enumerate(scenes):
        query = scene.get("image_query", f"news topic {idx}")
        out_path = IMAGES_DIR / f"scene_{idx}.jpg"

        print(f"  🔍 Searching photos for Scene {idx+1}: \"{query}\"")
        candidates = search_ddg_images(query)
        if not candidates:
            candidates = search_bing_images(query)

        if candidates:
            print(f"    ⬇️ Downloading high-res photo ({len(candidates)} candidates)...")
            success = download_and_format_image(candidates, out_path)
            if success:
                print(f"    ✅ Scene {idx+1} photo ready: {out_path.name}")
                ready_images.append(str(out_path))
                continue

        # Solid news graphic fallback
        print(f"    ⚠️ Creating news graphic fallback for scene {idx+1}")
        fallback = Image.new("RGB", (TARGET_W, TARGET_H), color=(20, 24, 33))
        fallback.save(out_path)
        ready_images.append(str(out_path))

    print(f"\n✅ All {len(ready_images)} News Images Prepared!")
    return ready_images


if __name__ == "__main__":
    download_news_images()
