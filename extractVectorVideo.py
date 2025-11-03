import os
import subprocess
import datetime
import textwrap
import time
import shutil
import whisper
import whisper.audio
import openai
import types
import numpy as np
import scipy.signal

# ===============================================================
# CONFIGURATION
# ===============================================================
VIDEO_PATH = r"D:\repos\VectorDB\camtasia\VectorDB.mp4"
OUTPUT_DIR = r"D:\repos\VectorDB\camtasia\transcripts"
FFMPEG_PATH = r"D:\ffmpeg\bin\ffmpeg.exe"
MODEL = "large-v3"
LANG = "en"

USE_OPENAI_SUMMARY = False  # off for now while debugging
openai.api_key = os.getenv("OPENAI_API_KEY")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===============================================================
# 1️⃣ Verify FFmpeg and print diagnostic info
# ===============================================================
print("==============================================================")
print("🔍 SYSTEM PATHS & ENVIRONMENT")
print("==============================================================")
print(f"Current Working Directory : {os.getcwd()}")
print(f"Python Executable         : {os.sys.executable}")
print(f"Video Path                : {VIDEO_PATH}")
print(f"Output Directory          : {OUTPUT_DIR}")
print(f"Audio Output Path         : {os.path.join(OUTPUT_DIR, 'VectorDB_audio.wav')}")
print(f"FFmpeg Expected Path      : {FFMPEG_PATH}")
print(f"FFmpeg Found (which)      : {shutil.which('ffmpeg')}")
print("--------------------------------------------------------------")

if not os.path.exists(FFMPEG_PATH):
    raise SystemExit(f"❌ FFmpeg not found at {FFMPEG_PATH}")
else:
    print(f"✔️ FFmpeg verified at {FFMPEG_PATH}")

os.environ["PATH"] = f"{os.path.dirname(FFMPEG_PATH)};{os.environ['PATH']}"
whisper.audio.FFMPEG_PATH = FFMPEG_PATH

print("\n🔧 PATH entries (top 3):")
for i, p in enumerate(os.environ['PATH'].split(';')[:3]):
    print(f"  [{i}] {p}")
print("==============================================================\n")

# ===============================================================
# 2️⃣ Extract Audio
# ===============================================================
AUDIO_PATH = os.path.join(OUTPUT_DIR, "VectorDB_audio.wav")

if os.path.exists(AUDIO_PATH):
    print(f"⚠️ Audio file already exists:\n   {AUDIO_PATH}")
    choice = input("Do you want to overwrite it? (Y/N): ").strip().lower()
    if choice == "y":
        print("🎧 Re-extracting audio...")
        subprocess.run([FFMPEG_PATH, "-y", "-i", VIDEO_PATH, "-ac", "1", "-ar", "16000", AUDIO_PATH], check=True)
    else:
        print("✅ Keeping existing audio file for processing.")
else:
    print("🎧 Extracting audio...")
    subprocess.run([FFMPEG_PATH, "-y", "-i", VIDEO_PATH, "-ac", "1", "-ar", "16000", AUDIO_PATH], check=True)

if not os.path.exists(AUDIO_PATH):
    raise FileNotFoundError(f"❌ Audio extraction failed: {AUDIO_PATH}")
else:
    print(f"✔️ Confirmed audio file exists: {AUDIO_PATH}")
    print(f"   Size: {os.path.getsize(AUDIO_PATH) / 1024 / 1024:.2f} MB")

time.sleep(2)

# ===============================================================
# 3️⃣ Safe patch: manual ffmpeg loader (Windows compatible)
# ===============================================================
def patched_load_audio(path, sr=16000, *args, **kwargs):
    norm = os.path.abspath(path).replace("\\", "/")
    print(f"🛠️  [Patched] Whisper loading (manual ffmpeg): {norm}")
    print(f"🛠️  [Patched] Using FFmpeg: {FFMPEG_PATH}")
    cmd = [
        FFMPEG_PATH, "-nostdin", "-threads", "0", "-i", norm,
        "-f", "f32le", "-ac", "1", "-ar", str(sr),
        "-acodec", "pcm_f32le", "-"
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        print("❌  ffmpeg failed to read the audio stream.")
        print("🔎  stderr (first 400 chars):")
        print(e.stderr.decode(errors="ignore")[:400])
        raise
    audio = np.frombuffer(out.stdout, np.float32).flatten()
    print(f"✔️  Loaded {len(audio)} samples at {sr} Hz from ffmpeg.")
    return audio

whisper.audio.load_audio = patched_load_audio

# ===============================================================
# 4️⃣ Transcription
# ===============================================================
print("\n==============================================================")
print("🧠 BEGINNING WHISPER TRANSCRIPTION")
print("==============================================================")
print(f"File Exists Check        : {os.path.isfile(AUDIO_PATH)}")
print(f"File Path Being Passed   : {AUDIO_PATH}")
print(f"Working Directory        : {os.getcwd()}")
print("--------------------------------------------------------------")

try:
    with open(AUDIO_PATH, "rb") as f:
        f.read(32)
    print(f"✔️ File readable: {AUDIO_PATH}")
except Exception as e:
    print(f"❌ Could not open audio file: {e}")
    raise

try:
    model = whisper.load_model(MODEL)
    print(f"✔️ Whisper model '{MODEL}' loaded successfully.")
except Exception as e:
    print(f"❌ Whisper model failed to load: {e}")
    raise

try:
    result = model.transcribe(AUDIO_PATH, language=LANG, fp16=False)
    print("✔️ Transcription completed successfully.")
except Exception as e:
    print(f"❌ Whisper error: {e}")
    raise

# ===============================================================
# 5️⃣ Save Outputs (Text + SRT + JSON)
# ===============================================================
if result and "text" in result:
    print("✅ Whisper returned transcript text successfully.")

    base_name = os.path.splitext(os.path.basename(AUDIO_PATH))[0]
    txt_path  = os.path.join(OUTPUT_DIR, f"{base_name}.txt")
    srt_path  = os.path.join(OUTPUT_DIR, f"{base_name}.srt")
    json_path = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    # --- Save plain text ---
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["text"])

    # --- Save JSON (for debug or analysis) ---
    import json
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # --- Save SRT if segments exist ---
    if "segments" in result:
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(result["segments"], start=1):
                start = str(datetime.timedelta(seconds=int(seg["start"])))
                end   = str(datetime.timedelta(seconds=int(seg["end"])))
                f.write(f"{i}\n{start} --> {end}\n{seg['text'].strip()}\n\n")

    print("--------------------------------------------------------------")
    print(f"💾 Saved transcript text  → {txt_path}")
    print(f"💾 Saved transcript SRT   → {srt_path}")
    print(f"💾 Saved transcript JSON  → {json_path}")
    print("--------------------------------------------------------------")

else:
    print("⚠️ Whisper returned no text; skipping file writes.")

print("✅ Transcription workflow complete.")
