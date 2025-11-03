"""
analyzeVectorVideo.py  —  OpenAI v1+ compatible
---------------------------------------------------------------
Analyzes a Whisper transcript and generates a Markdown summary
and technical corrections report using GPT-4.
"""

import os
import textwrap
from openai import OpenAI   # ✅ new import style

# ===============================================================
# CONFIGURATION
# ===============================================================
OUTPUT_DIR = r"D:\repos\VectorDB\camtasia\transcripts"
TRANSCRIPT_FILE = os.path.join(OUTPUT_DIR, "VectorDB_audio.txt")
REVIEW_FILE = os.path.join(OUTPUT_DIR, "VectorDB_review_summary.md")

MODEL = "gpt-4o"        # ✅ full GPT-4o for best accuracy
MAX_CHARS = 120_000      # ✅ safe for large transcripts (~40–45 pages of text)
TEMPERATURE = 0.4

# Initialize new-style OpenAI client
client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

# ===============================================================
# 1️⃣ Verify input file
# ===============================================================
print("==============================================================")
print("📂 ANALYZING VECTOR VIDEO TRANSCRIPT")
print("==============================================================")
print(f"Transcript File : {TRANSCRIPT_FILE}")
print(f"Output Markdown : {REVIEW_FILE}")
print("--------------------------------------------------------------")

if not os.path.exists(TRANSCRIPT_FILE):
    raise FileNotFoundError(f"❌ Transcript file not found: {TRANSCRIPT_FILE}")

with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
    transcript_text = f.read().strip()

if len(transcript_text) == 0:
    raise ValueError("❌ Transcript file is empty.")

if len(transcript_text) > MAX_CHARS:
    transcript_excerpt = transcript_text[:MAX_CHARS]
    print(f"✂️  Transcript truncated to {MAX_CHARS:,} characters.")
else:
    transcript_excerpt = transcript_text

# ===============================================================
# 2️⃣ Build GPT prompt
# ===============================================================
prompt = textwrap.dedent(f"""
You are a senior technical editor specializing in AI, databases, and vector search.
Analyze the following transcript and produce a clear, accurate Markdown report.

### Tasks
1. Identify and correct any factual inaccuracies or oversimplifications.
2. Write a **3-paragraph summary** preserving all key technical content.
3. Provide **5–10 corrected statements**, each beginning with ✅ Corrected:.

### Output Format
## Summary
<3 concise paragraphs>

## Technical Corrections
✅ Corrected: <item 1>  
✅ Corrected: <item 2>  


## Notes
- Optional commentary about clarity or pacing.

Transcript:
{transcript_excerpt}
""")

# ===============================================================
# 3️⃣ Send to GPT-4 (new client API)
# ===============================================================
print("🧠 Sending transcript to GPT-4 for analysis...")

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    review_content = response.choices[0].message.content

    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        f.write(review_content)

    print("--------------------------------------------------------------")
    print(f"📘 Review + summary written to:\n   {REVIEW_FILE}")
    print("==============================================================")

except Exception as e:
    print(f"⚠️ GPT-4 analysis failed: {e}")

