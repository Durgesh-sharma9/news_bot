import os
import sys
import json
import re
from pathlib import Path
import requests
from PIL import Image, ImageFilter, ImageOps

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}


def search_bing_images(query, max_results=8):
    """Direct publisher high-resolution news photo search via Bing Images."""
    try:
        clean_q = f"{query} news photo hd"
        url = f"https://www.bing.com/images/async?q={requests.utils.quote(clean_q)}&first=0&count={max_results}&mmasync=1"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            murls = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', resp.text)
            if not murls:
                murls = re.findall(r'"murl":"(http[^"]+)"', resp.text)
            # Filter out generic clipart or tiny icons
            filtered = [u for u in murls if not any(x in u.lower() for x in ["icon", "logo", "clipart", "avatar", "vector"])]
            return filtered[:max_results]
    except Exception:
        pass
    return []


def search_ddg_images(query, max_results=8):
    """High-res news photos via DuckDuckGo."""
    if not ddgs:
        return []
    try:
        ddg = ddgs.DDGS()
        clean_q = f"{query} news"
        results = list(ddg.images(clean_q, max_results=max_results))
        urls = []
        for r in results:
            img_url = r.get("image")
            if img_url and img_url.startswith("http"):
                if not any(x in img_url.lower() for x in ["icon", "logo", "clipart", "avatar", "vector"]):
                    urls.append(img_url)
        return urls
    except Exception:
        return []


def search_google_images(query, max_results=6):
    """Fallback photo search via Google Images."""
    try:
        clean_q = f"{query} news press photo"
        url = f"https://www.google.com/search?tbm=isch&q={requests.utils.quote(clean_q)}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            urls = re.findall(r'(https?://[^"]+\.(?:jpg|jpeg|png))', resp.text)
            valid = [u for u in urls if "gstatic" not in u and "google" not in u]
            return valid[:max_results]
    except Exception:
        pass
    return []


def download_and_format_image(candidate_urls, output_path):
    """Downloads original high-res photo and formats to broadcast TV vertical standard (1080x1920)."""
    raw_path = output_path.with_suffix(".raw.jpg")

    for url in candidate_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10, stream=True)
            if resp.status_code == 200 and int(resp.headers.get("content-length", 10000)) > 15000:
                with open(raw_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16384):
                        if chunk:
                            f.write(chunk)

                with Image.open(raw_path) as raw:
                    raw = raw.convert("RGB")
                    w, h = raw.size

                    # Enforce high-definition quality (reject low-res thumbnails)
                    if w < 450 or h < 350:
                        continue

                    # If already vertical with good aspect ratio, smart crop
                    aspect = h / w
                    if 1.5 <= aspect <= 1.85:
                        final_img = ImageOps.fit(raw, (TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
                        final_img.save(output_path, quality=95)
                        if raw_path.exists():
                            raw_path.unlink()
                        return True

                    # Broadcast TV Style: Blurred backdrop with centered sharp foreground
                    bg_scale = max(TARGET_W / w, TARGET_H / h)
                    bg = raw.resize((int(w * bg_scale), int(h * bg_scale)), Image.LANCZOS)
                    bg_w, bg_h = bg.size
                    bg = bg.crop(((bg_w - TARGET_W) // 2, (bg_h - TARGET_H) // 2,
                                  (bg_w + TARGET_W) // 2, (bg_h + TARGET_H) // 2))
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=28))

                    # Foreground scaled to fill width
                    fg_scale = min(TARGET_W / w, (TARGET_H * 0.80) / h)
                    fg_w = int(w * fg_scale)
                    fg_h = int(h * fg_scale)
                    fg = raw.resize((fg_w, fg_h), Image.LANCZOS)

                    # Center foreground
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
    print("📸 DOWNLOADING ORIGINAL NEWS PHOTOS (ACCURATE & HD)")
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

        print(f"  🔍 Searching Original Photos for Scene {idx+1}: \"{query}\"")
        candidates = search_bing_images(query)
        if len(candidates) < 3:
            candidates.extend(search_ddg_images(query))
        if len(candidates) < 3:
            candidates.extend(search_google_images(query))

        if candidates:
            print(f"    ⬇️ Downloading original HD photo ({len(candidates)} candidates)...")
            success = download_and_format_image(candidates, out_path)
            if success:
                print(f"    ✅ Scene {idx+1} photo ready: {out_path.name}")
                ready_images.append(str(out_path))
                continue

        # Solid graphic fallback only if all engines fail
        print(f"    ⚠️ Graphic fallback for scene {idx+1}")
        fallback = Image.new("RGB", (TARGET_W, TARGET_H), color=(18, 22, 30))
        fallback.save(out_path)
        ready_images.append(str(out_path))

    print(f"\n✅ All {len(ready_images)} Accurate News Photos Ready!")
    return ready_images


if __name__ == "__main__":
    download_news_images()
