import os
import sys
import json
import asyncio
from pathlib import Path
import edge_tts
try:
    from moviepy import AudioFileClip, concatenate_audioclips
except ImportError:
    from moviepy.editor import AudioFileClip, concatenate_audioclips

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_FILE = SCRIPT_DIR / "script.json"
OUTPUT_AUDIO = SCRIPT_DIR / "voiceover.mp3"
TIMING_FILE = SCRIPT_DIR / "voiceover_timing.json"
TEMP_DIR = SCRIPT_DIR / "temp_audios"
TEMP_DIR.mkdir(exist_ok=True)

DEFAULT_VOICE = "hi-IN-MadhurNeural"  # Professional Hindi News Anchor


async def generate_scene_audio(text, voice, output_path):
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(text, voice, rate="+5%", pitch="+0Hz")
            await communicate.save(str(output_path))
            return
        except Exception as e:
            print(f"    ⚠️ Voice gen retry {attempt+1}/3: {e}")
            if attempt < 2:
                await asyncio.sleep(2)
            else:
                raise e


def create_voiceover(voice=DEFAULT_VOICE):
    print("\n" + "="*55)
    print("🎙️ GENERATING AI NEWS ANCHOR VOICEOVER")
    print("="*55)

    if not SCRIPT_FILE.exists():
        print(f"❌ {SCRIPT_FILE} nahi mila!")
        sys.exit(1)

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    scenes = script_data.get("scenes", [])
    if not scenes:
        print("❌ Scenes empty hain!")
        sys.exit(1)

    scene_audio_paths = []
    timings = []
    current_time = 0.0

    for idx, scene in enumerate(scenes):
        voice_text = scene.get("voice_text", "").strip()
        caption_text = scene.get("caption_text", "").strip()
        temp_path = TEMP_DIR / f"scene_{idx}.mp3"

        print(f"  🔊 Generating Scene {idx+1}/{len(scenes)}: \"{caption_text}\"")
        asyncio.run(generate_scene_audio(voice_text, voice, temp_path))

        # Get audio duration
        clip = AudioFileClip(str(temp_path))
        duration = clip.duration
        clip.close()

        timings.append({
            "scene_index": idx,
            "start": round(current_time, 2),
            "end": round(current_time + duration, 2),
            "duration": round(duration, 2),
            "caption": caption_text,
            "image_query": scene.get("image_query", ""),
            "sfx": scene.get("sfx", "whoosh")
        })

        scene_audio_paths.append(str(temp_path))
        current_time += duration

    # Merge audio clips into master voiceover
    print("\n🔄 Combining scene audio clips...")
    audio_clips = [AudioFileClip(p) for p in scene_audio_paths]
    final_audio = concatenate_audioclips(audio_clips)
    final_audio.write_audiofile(str(OUTPUT_AUDIO), fps=44100, logger=None)

    total_duration = final_audio.duration
    final_audio.close()
    for c in audio_clips:
        c.close()

    # Save timings
    timing_data = {
        "total_duration": round(total_duration, 2),
        "scenes": timings
    }
    with open(TIMING_FILE, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Voiceover Created: {OUTPUT_AUDIO.name} ({round(total_duration, 1)} seconds)")
    print(f"📄 Timings saved to: {TIMING_FILE.name}\n")
    return timing_data


if __name__ == "__main__":
    v = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VOICE
    create_voiceover(v)
