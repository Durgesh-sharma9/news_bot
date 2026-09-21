import sys
import time
import subprocess
from pathlib import Path

# Windows UTF-8 stdout fix
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


def run_step(step_name, script_path, args=None):
    print("\n" + "="*55)
    print(f"🚀 RUNNING: {step_name}")
    print("="*55 + "\n")

    target = SCRIPT_DIR / script_path
    cmd = [PYTHON_EXE, str(target)]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, cwd=str(SCRIPT_DIR))
    if result.returncode != 0:
        print(f"\n❌ Error aya {step_name} mein! Pipeline ruk gayi.")
        sys.exit(1)


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "breaking"
    category = sys.argv[2] if len(sys.argv) > 2 else "breaking"

    start_time = time.time()
    print("\n" + "🔥"*25)
    print(f"🔥 NEWS KID VIDEO GENERATOR: \"{topic}\" (Category: {category.upper()})")
    print("🔥"*25)

    # Step 1: Script
    run_step("Step 1: Inshorts News Research & Anchor Script", "step1_news_script.py", [topic, category])

    # Step 2: Voiceover
    run_step("Step 2: Generating AI News Anchor Voice", "step2_voiceover.py")

    # Step 3: Images
    run_step("Step 3: Downloading Real News Photos (Zero Videos)", "step3_download_images.py")

    # Step 4: Render Video
    run_step("Step 4: Compositing 1080x1920 Fast News Video", "step4_merge_news_video.py")

    total_time = round(time.time() - start_time, 1)
    print("\n" + "="*55)
    print(f"🎉 PIPELINE FINISHED IN {total_time} SECONDS!")
    print(f"👉 Local File: {SCRIPT_DIR / 'final_news.mp4'}")
    print("="*55 + "\n")


if __name__ == "__main__":
    main()
