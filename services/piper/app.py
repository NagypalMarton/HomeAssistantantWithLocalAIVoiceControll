import os
import io
import subprocess
import tempfile
from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Voice paths
VOICES_DIR = os.getenv("VOICES_DIR", "/app/voices")
VOICE_HU = os.path.join(VOICES_DIR, "hu_HU-berta-medium.onnx")
VOICE_EN = os.path.join(VOICES_DIR, "en_US-lessac-medium.onnx")


class SpeakRequest(BaseModel):
    text: str
    language: str = "auto"  # auto, hu, en


@app.post("/speak")
async def speak(req: SpeakRequest):
    # Auto-detect language based on first characters
    lang = req.language.lower()
    if lang == "auto":
        # Simple heuristic: check if text contains Hungarian-specific characters
        if any(c in req.text for c in "áéíóöőúüű"):
            lang = "hu"
        else:
            lang = "en"
    
    voice_path = VOICE_HU if lang == "hu" else VOICE_EN
    
    if not os.path.exists(voice_path):
        print(f"[piper] Voice file not found: {voice_path}")
        return JSONResponse({"error": f"Voice file not found: {lang}"}, status_code=500)
    
    # Create temporary file for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "output.wav")
        
        try:
            # Run piper binary
            result = subprocess.run(
                ["piper", "--model", voice_path, "--output_file", output_path],
                input=req.text.encode('utf-8'),
                capture_output=True,
                check=True
            )
            
            # Read generated WAV
            with open(output_path, "rb") as f:
                wav_data = f.read()
            
            return Response(content=wav_data, media_type="audio/wav")
        
        except subprocess.CalledProcessError as e:
            print(f"[piper] TTS error: {e.stderr.decode('utf-8')}")
            return JSONResponse({"error": "TTS failed"}, status_code=500)
        except FileNotFoundError:
            print(f"[piper] Output file not created")
            return JSONResponse({"error": "TTS processing failed"}, status_code=500)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "voices": ["hu", "en"]})
