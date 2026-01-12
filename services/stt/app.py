import io
import tempfile
import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydub import AudioSegment
import whisper
import torch

app = FastAPI()

# 🇭🇺 Magyar-specifikus STT optimalizáció Pi 4-hez (ARM64/aarch64)
MODEL_SIZE = "tiny"          # legkisebb, leggyorsabb (~400 MB RAM)
LANGUAGE = "hu"              # MAGYAR FIX (nem auto)
SAMPLE_RATE = 16000          # Whisper native: 16 kHz (8 kHz upsampling veszteség)

# CPU-only mode (ARM64 Raspberry Pi)
torch.set_num_threads(2)      # CPU thread limit
model = whisper.load_model(MODEL_SIZE, device="cpu")

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    try:
        raw = await file.read()
        if not raw:
            return JSONResponse({"error": "Empty file"}, status_code=400)
        
        audio = AudioSegment.from_file(io.BytesIO(raw))
    except Exception as e:
        print(f"[stt] Audio format error: {e}")
        return JSONResponse({"error": "Invalid audio format"}, status_code=400)
    
    try:
        # Whisper native: 16 kHz, mono
        audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1)

        # OpenAI Whisper fájl path-ot vár (nem BytesIO)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio.export(tmp.name, format="wav")
            tmp_path = tmp.name
        
        try:
            # Magyar-specifikus transzkripció (ARM64 optimalizált)
            result = model.transcribe(
                tmp_path,
                language=LANGUAGE,
                fp16=False,           # CPU mode (no FP16 on ARM)
                condition_on_previous_text=False,  # gyorsabb
                temperature=0.0,      # deterministic
            )
            
            text = result["text"].strip()
            return JSONResponse({
                "text": text,
                "language": "hu",
                "sample_rate": SAMPLE_RATE
            })
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        print(f"[stt] Transcription error: {e}")
        return JSONResponse({"error": "Transcription failed"}, status_code=500)

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "ok",
        "language": "hu",
        "sample_rate": f"{SAMPLE_RATE} Hz",
        "model": MODEL_SIZE,
        "backend": "openai-whisper (ARM64)"
    })
