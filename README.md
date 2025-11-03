(openAI key was accidentally committed and is now deleted)

# 🎬 VectorDB Video Transcription & Analysis Suite  
*Comprehensive Documentation & Commentary (2025 Edition)*

---

## 🧠 Introduction  

This repository automates the **conversion, transcription, and analysis** of technical videos — especially developer-oriented content like tutorials, architecture briefings, or conference talks.  

The workflow:
1. Extracts high-quality audio from `.mp4` files  
2. Transcribes it locally using **OpenAI Whisper**  
3. Analyzes the transcript with **GPT-4o**, producing:
   - A clean Markdown summary
   - Timestamped clarifications
   - Technical corrections (in table format)
   - Structured documentation for publishing

This system was designed and field-tested on **Windows Server 2019** and **Windows 11**, making it stable in mixed enterprise environments.

---

## ⚙️ High-Level Architecture

```
VectorDB.mp4 (input)
│
├─ extractVectorVideo.py
│   ↓
│   ├─ VectorDB_audio.wav
│   ├─ VectorDB_audio.txt
│   ├─ VectorDB_audio.srt
│   └─ VectorDB_audio.json
│
├─ analyzeVectorVideo.py
│   ↓
└─ VectorDB_review_summary.md
```

### Components
- **Whisper (large-v3)** → Accurate multilingual transcription  
- **FFmpeg** → Deterministic audio extraction  
- **GPT-4o** → Analytical summarization and error correction  
- **Markdown output** → Clean, portable documentation  

---

## 🧩 Step-by-Step Workflow  

### 🧱 1. Extract Audio & Transcribe  

**File:** `extractVectorVideo.py`

Performs:
- FFmpeg environment validation  
- Conditional overwrite check for `.wav`  
- Whisper-based transcription using `large-v3`  

#### 💻 Command
```
python extractVectorVideo.py
```

#### ✅ Outputs
| File | Description |
|------|--------------|
| `VectorDB_audio.wav` | Extracted 16 kHz mono audio |
| `VectorDB_audio.txt` | Whisper plain transcript |
| `VectorDB_audio.srt` | Subtitles with timestamps |
| `VectorDB_audio.json` | Raw Whisper structured output |

#### ⚙️ Whisper Configuration
- `fp16=False` for CPU-only compatibility  
- Custom FFmpeg path (`D:\ffmpeg\bin\ffmpeg.exe`)  
- Manual loader patch to avoid *WinError 2*  

> 💬 *Comment:* Whisper’s default loader can fail on Windows paths with spaces or missing quotes.  
> The patch ensures every FFmpeg call uses an **absolute, quoted path** to prevent subprocess failures.

---

### 🧠 2. Analyze Transcript  

**File:** `analyzeVectorVideo.py`

Uses the **OpenAI GPT API** to:
- Review the transcript text  
- Summarize and highlight technical ideas  
- Detect inaccurate or vague statements  
- Generate a Markdown document suitable for publication  

#### 💻 Command
```
python analyzeVectorVideo.py
```

#### 📄 Output Example
```
## Summary
This session covers how vector databases accelerate similarity search 
by embedding textual and numeric data into multidimensional vectors. 

## Clarifications and Corrections (Table)
| Timestamp | Type | Description |
|------------|------|--------------|
| 03m23s | Clarification | “NoSQL plus {X,Y} also yields {Z}” should specify that Z results from cosine distance < 0.3. |
| 08m17s | Correction | “Vectors replace indexes” → should be “Vectors *complement* traditional indexes.” |
```

#### 🧠 GPT Configuration
- Model: `gpt-4o` (can be changed to `gpt-4o-mini`)  
- Adjustable context length (`MAX_CHARS`)  
- Produces Markdown with timestamped table entries  

> 💬 *Comment:* GPT-4o is ideal here — it supports large context windows (128 K tokens) and consistent output formatting, perfect for long transcripts.

---

## 🔧 Installation  

Install dependencies once:
```
pip install openai openai-whisper numpy scipy
```

Confirm FFmpeg:
```
ffmpeg -version
```

Set your API key:
```
setx OPENAI_API_KEY "sk-yourapikeyhere"
```

> 💬 *Comment:* Credentials are read from the environment variable to avoid embedding sensitive data in code.

---

## 🗂️ Folder Structure  

```
D:\repos\VectorDB\
│
├─ camtasia\
│   ├─ VectorDB.mp4
│   └─ transcripts\
│        ├─ VectorDB_audio.wav
│        ├─ VectorDB_audio.txt
│        ├─ VectorDB_audio.srt
│        ├─ VectorDB_audio.json
│        └─ VectorDB_review_summary.md
│
├─ extractVectorVideo.py
└─ analyzeVectorVideo.py
```

> 💬 *Comment:* Keeping `transcripts` inside the `camtasia` folder provides a one-to-one mapping between input projects and generated outputs.

---

## 🧠 Example GPT Output (Condensed)

```
## Summary
This workshop details how embedding vectors improve semantic retrieval efficiency in SQL Server 2025.

## Technical Corrections
✅ Vector DBs augment, not replace, relational engines.  
✅ Cosine similarity yields a *score*, not a Boolean.  
✅ Indexing embeddings can leverage hybrid ANN + B-tree models.  

## Clarifications Table
| Time | Topic | Note |
|------|--------|------|
| 1m40s | Vector Context | Clarify that embeddings encode semantic meaning, not exact keywords. |
| 5m32s | ANN Search | Distinguish HNSW from LSH — the former is graph-based, not hash-based. |
```

---

## ⚙️ Key Implementation Details  

### 1️⃣ FFmpeg Patch
Ensures paths are normalized with forward slashes and fully quoted.
```python
def patched_load_audio(path, sr=16000, *args, **kwargs):
    norm = os.path.abspath(path).replace("\\", "/")
    cmd = [FFMPEG_PATH, "-nostdin", "-threads", "0", "-i", norm,
           "-f", "f32le", "-ac", "1", "-ar", str(sr),
           "-acodec", "pcm_f32le", "-"]
```

### 2️⃣ Whisper Invocation
```python
model = whisper.load_model("large-v3")
result = model.transcribe(AUDIO_PATH, language="en", fp16=False)
```

### 3️⃣ GPT Analysis
```python
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a technical reviewer..."},
        {"role": "user", "content": transcript_text[:MAX_CHARS]}
    ],
)
```

---

## ⚡ Troubleshooting  

| Symptom | Cause | Fix |
|----------|--------|-----|
| ❌ `WinError 2` | FFmpeg not quoted or not found | Update `FFMPEG_PATH` and ensure full path |
| ⚠️ No module named `whisper` | Wrong package installed | `pip install openai-whisper` |
| 🧩 FP16 not supported | CPU-only execution | Safe to ignore (auto fallback to FP32) |
| 🚫 Insufficient quota | Free-tier API exhausted | Add billing or use local LLM (Ollama / GPT4All) |

---

## 💬 Developer Comments  

- ✅ Designed for long-form educational recordings (30–90 min)  
- 🧱 Modular — each stage is stand-alone  
- 🧠 Ideal for indexing video corpora into vector databases  
- 📈 Extensible — integrates with Pinecone, FAISS, Qdrant  

> 💬 *Comment:* After generating transcripts, you can embed them into a **Vector DB**, making this the first step in building a searchable knowledge base.

---

## 🔮 Future Enhancements  

| Area | Planned Feature | Description |
|------|-----------------|-------------|
| 🧩 Chunked Processing | Split transcripts into 10 K-token segments |
| 📊 Topic Detection | Auto-label sections (“Intro to ANN”, “Cosine Math”) |
| 🪶 Lightweight Mode | Use `gpt-4o-mini` for fast analysis |
| 📈 Embedding Export | Generate vectors for semantic search |
| 🧱 Web Dashboard | Visualize transcript + corrections in-browser |

---

## 🧾 License  

**MIT License © 2025 Edmund Landgraf**  
You may modify, distribute, and use this workflow for both commercial and research purposes.  
Attribution is appreciated.

---

*End of file — VectorDB Video Transcription & Analysis Suite*
