import os
import sys
import json
import re
import gc
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import (
        AudioFileClip, CompositeAudioClip,
        ImageClip, concatenate_videoclips, concatenate_audioclips
    )
except ImportError:
    from moviepy.editor import (
        AudioFileClip, CompositeAudioClip,
        ImageClip, concatenate_videoclips, concatenate_audioclips
    )

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
TIMING_FILE = SCRIPT_DIR / "voiceover_timing.json"
SCRIPT_FILE = SCRIPT_DIR / "script.json"
VOICEOVER_AUDIO = SCRIPT_DIR / "voiceover.mp3"
BGM_AUDIO = SCRIPT_DIR / "news_bgm.wav"
FONTS_DIR = SCRIPT_DIR / "fonts"
SFX_DIR = SCRIPT_DIR / "sfx"
IMAGES_DIR = SCRIPT_DIR / "images"
OUTPUT_VIDEO = SCRIPT_DIR / "final_news.mp4"

TARGET_W = 1080
TARGET_H = 1920
FPS = 24


def set_clip_duration(clip, dur):
    return clip.with_duration(dur) if hasattr(clip, "with_duration") else clip.set_duration(dur)

def set_clip_start(clip, st):
    return clip.with_start(st) if hasattr(clip, "with_start") else clip.set_start(st)

def set_audio_volume(clip, vol):
    return clip.with_volume_scaled(vol) if hasattr(clip, "with_volume_scaled") else clip.volumex(vol)

def set_clip_audio(clip, aud):
    return clip.with_audio(aud) if hasattr(clip, "with_audio") else clip.set_audio(aud)


def get_font(size=42):
    hindi_font = FONTS_DIR / "NotoSansDevanagari-Bold.ttf"
    if hindi_font.exists():
        try:
            return ImageFont.truetype(str(hindi_font), size)
        except Exception:
            pass
    return ImageFont.load_default()


def clean_caption_text(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff\uD800-\uDBFF\uDC00-\uDFFF"
        "\u2600-\u26FF\u2700-\u27BF\u2300-\u23FF\u2B50\u200D\uFE0F]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub("", text).strip()
    return re.sub(r'\s+', ' ', cleaned).strip()


import textwrap

def get_english_font(size=26):
    imp_font = FONTS_DIR / "impact.ttf"
    if imp_font.exists():
        try:
            return ImageFont.truetype(str(imp_font), size)
        except Exception:
            pass
    return ImageFont.load_default()

def bake_scene_frame(img_path, badge="बड़ी खबर", headline="", caption="", output_path=None):
    """Pre-composites the entire scene into an edge-to-edge broadcast television graphics frame in Pillow."""
    if not img_path.exists():
        canvas = Image.new("RGB", (TARGET_W, TARGET_H), color=(15, 20, 28))
    else:
        canvas = Image.open(img_path).convert("RGB")
        if canvas.size != (TARGET_W, TARGET_H):
            canvas = canvas.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    draw = ImageDraw.Draw(canvas, "RGBA")

    # =========================================================================
    # 📺 1. TV BROADCAST TOP BANNER (Edge-to-Edge Television Aesthetic)
    # =========================================================================
    bar_y1 = 70
    bar_y2 = 135

    # Full width background for top strip
    draw.rectangle([0, bar_y1, TARGET_W, bar_y2], fill=(12, 18, 30, 250))

    # Left Red Breaking Tab (width = 400px)
    tab_w = 400
    draw.rectangle([0, bar_y1, tab_w, bar_y2], fill=(225, 20, 30, 255))

    # Live Glowing Red/White Radar Beacon inside Red Tab
    draw.ellipse([35, bar_y1 + 18, 65, bar_y1 + 48], fill=(255, 255, 255))
    draw.ellipse([40, bar_y1 + 23, 60, bar_y1 + 43], fill=(225, 20, 30))
    draw.ellipse([45, bar_y1 + 28, 55, bar_y1 + 38], fill=(255, 255, 255))

    font_badge = get_font(34)
    badge_clean = clean_caption_text(badge) or "बड़ी खबर"
    draw.text((75, bar_y1 + 14), badge_clean.upper(), font=font_badge, fill="#FFFFFF")

    # Right Channel Name Tab: Bold Gold text for NEWS KID
    font_tag = get_english_font(34)
    tag_text = "NEWS KID"
    t_box = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw = t_box[2] - t_box[0]
    draw.text((TARGET_W - tw - 45, bar_y1 + 15), tag_text, font=font_tag, fill="#FFE600")

    # --- Headline Bar: Row 2 (Full Width Edge-to-Edge) ---
    if headline:
        head_clean = clean_caption_text(headline)
        font_head = get_font(44)
        lines = textwrap.wrap(head_clean, width=30)
        if not lines:
            lines = [head_clean]

        line_h = 58
        head_box_h = len(lines) * line_h + 32
        h_y1 = bar_y2
        h_y2 = h_y1 + head_box_h

        # Full width translucent deep crystal glass background
        draw.rectangle([0, h_y1, TARGET_W, h_y2], fill=(6, 10, 18, 240))
        # Gold divider stripe at bottom of headline plate
        draw.rectangle([0, h_y2 - 5, TARGET_W, h_y2], fill=(255, 225, 0, 255))

        # Centered bold white text with sharp drop shadow
        for i, line in enumerate(lines):
            ly = h_y1 + 16 + i * line_h
            l_box = draw.textbbox((0, 0), line, font=font_head)
            lw = l_box[2] - l_box[0]
            lx = (TARGET_W - lw) // 2
            draw.text((lx + 2, ly + 2), line, font=font_head, fill=(0, 0, 0, 200))
            draw.text((lx, ly), line, font=font_head, fill="#FFFFFF", stroke_width=2, stroke_fill="black")

    # =========================================================================
    # 📺 2. TV BROADCAST LOWER THIRD CAPTION (y=1420)
    # =========================================================================
    if caption:
        cap_clean = clean_caption_text(caption)
        font_cap = get_font(42)
        bbox = draw.textbbox((0, 0), cap_clean, font=font_cap)
        t_w = bbox[2] - bbox[0]
        t_h = bbox[3] - bbox[1]

        pad_x, pad_y = 36, 16
        box_w = min(t_w + pad_x * 2, TARGET_W - 80)
        box_h = t_h + pad_y * 2
        box_x1 = (TARGET_W - box_w) // 2
        box_y1 = 1420
        box_x2 = box_x1 + box_w
        box_y2 = box_y1 + box_h

        draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=18,
                               fill=(8, 12, 22, 235), outline="#FFE600", width=3)

        text_x = box_x1 + (box_w - t_w) // 2
        text_y = box_y1 + (box_h - t_h) // 2 - 4
        draw.text((text_x, text_y), cap_clean, font=font_cap, fill="#FFFFFF",
                  stroke_width=2, stroke_fill="black")

    if output_path:
        canvas.save(output_path, quality=95)
    return canvas


def build_news_video():
    print("\n" + "="*55)
    print("🎬 FAST NEWS VIDEO RENDERER (PRE-BAKED FRAMES)")
    print("="*55)

    if not TIMING_FILE.exists() or not VOICEOVER_AUDIO.exists():
        print("❌ Audio ya Timings missing hain!")
        sys.exit(1)

    with open(TIMING_FILE, "r", encoding="utf-8") as f:
        timing_data = json.load(f)

    badge = "🔴 BREAKING NEWS"
    headline = ""
    if SCRIPT_FILE.exists():
        try:
            with open(SCRIPT_FILE, "r", encoding="utf-8") as sf:
                sdata = json.load(sf)
                badge = sdata.get("badge", badge)
                headline = sdata.get("title", "")
        except Exception:
            pass

    scenes = timing_data.get("scenes", [])
    voice_audio = AudioFileClip(str(VOICEOVER_AUDIO))
    total_duration = voice_audio.duration

    scene_clips = []
    sfx_clips = []

    print(f"  🎨 Pre-baking {len(scenes)} TV news scene frames with Pillow...")
    for idx, scene in enumerate(scenes):
        img_path = IMAGES_DIR / f"scene_{idx}.jpg"
        baked_path = IMAGES_DIR / f"baked_scene_{idx}.jpg"
        cap_text = scene.get("caption", "")
        dur = scene.get("duration", 8.0)

        # Pre-bake in 0.01 seconds
        bake_scene_frame(img_path, badge, headline, cap_text, baked_path)

        # Single ImageClip (no slow multi-layer alpha blending!)
        img_clip = ImageClip(str(baked_path))
        img_clip = set_clip_duration(img_clip, dur)
        scene_clips.append(img_clip)

        # Sound Effect
        sfx_name = scene.get("sfx", "whoosh")
        sfx_file = SFX_DIR / f"{sfx_name}.wav"
        if not sfx_file.exists():
            sfx_file = SFX_DIR / "whoosh.wav"
        if sfx_file.exists():
            try:
                sfx_c = AudioFileClip(str(sfx_file))
                sfx_c = set_audio_volume(sfx_c, 0.12)
                sfx_c = set_clip_start(sfx_c, scene.get("start", 0.0))
                sfx_clips.append(sfx_c)
            except Exception:
                pass

    print(f"  🎞️ Concatenating {len(scene_clips)} scene clips...")
    final_video = concatenate_videoclips(scene_clips, method="compose")

    # Audio Mixing
    print("  🎵 Mixing Voiceover, News BGM, and Sound Effects...")
    audio_tracks = [voice_audio]

    if BGM_AUDIO.exists():
        try:
            bgm = AudioFileClip(str(BGM_AUDIO))
            if bgm.duration < total_duration:
                repeats = int(total_duration // bgm.duration) + 1
                bgm = concatenate_audioclips([bgm] * repeats)
            bgm = bgm.subclipped(0, total_duration) if hasattr(bgm, 'subclipped') else bgm.subclip(0, total_duration)
            bgm = set_audio_volume(bgm, 0.035)
            audio_tracks.append(bgm)
        except Exception as e:
            print(f"  ⚠️ BGM mixing skipped: {e}")

    audio_tracks.extend(sfx_clips)
    final_audio = CompositeAudioClip(audio_tracks)
    final_video = set_clip_audio(final_video, final_audio)

    print("\n⚡ Rendering final 1080x1920 News Video (ultrafast)...")
    final_video.write_videofile(
        str(OUTPUT_VIDEO),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None
    )

    final_video.close()
    voice_audio.close()
    gc.collect()

    print(f"\n🎉 NEWS VIDEO READY: {OUTPUT_VIDEO.name} ({round(total_duration, 1)}s)")
    return str(OUTPUT_VIDEO)


if __name__ == "__main__":
    build_news_video()
