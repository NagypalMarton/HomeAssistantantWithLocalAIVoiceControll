import os
import io
import time
import json
import asyncio
import numpy as np
import sounddevice as sd
import webrtcvad
import threading
from pathlib import Path
from pydub import AudioSegment
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import aiohttp

# Configuration constants
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
RECORD_SECONDS = int(os.getenv("RECORD_SECONDS", "5"))
STT_URL = os.getenv("STT_URL", "http://stt:8002/transcribe")
PIPER_TTS_URL = os.getenv("PIPER_TTS_URL", "")
CONFIG_FILE = Path("/app/config/forward_url.json")

# Magic constants
HTTP_TIMEOUT = 30  # seconds
VAD_AGGRESSIVENESS = 2

app = FastAPI()

vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

# Thread-safe config management
class ConfigManager:
    def __init__(self):
        self.forward_url = ""
        self.lock = threading.RLock()
    
    def get(self) -> str:
        with self.lock:
            return self.forward_url
    
    def set(self, url: str):
        with self.lock:
            self.forward_url = url
    
    def load_from_file(self) -> str:
        with self.lock:
            if CONFIG_FILE.exists():
                try:
                    with open(CONFIG_FILE, "r") as f:
                        config = json.load(f)
                        self.forward_url = config.get("forward_url", "").strip()
                        print(f"[orchestrator] FORWARD_URL betöltve: {self.forward_url}")
                        return self.forward_url
                except Exception as e:
                    print(f"[orchestrator] Config betöltési hiba: {e}")
            return ""

config_mgr = ConfigManager()


def load_config():
    """Deprecated: use config_mgr instead"""
    return config_mgr.load_from_file()


def record_until_silence(max_seconds: int = RECORD_SECONDS) -> np.ndarray:
    sd.default.samplerate = SAMPLE_RATE
    sd.default.channels = 1
    frame_ms = 30
    frame_len = int(SAMPLE_RATE * frame_ms / 1000)
    frames = []
    start = time.time()
    with sd.InputStream(dtype='int16') as stream:
        while time.time() - start < max_seconds:
            buf, _ = stream.read(frame_len)
            audio = buf.reshape(-1)
            is_speech = vad.is_speech(audio.tobytes(), SAMPLE_RATE)
            frames.append(audio)
            if not is_speech and len(frames) > SAMPLE_RATE // frame_len:
                break
    return np.concatenate(frames) if frames else np.array([], dtype=np.int16)


async def transcribe_audio(raw_pcm: np.ndarray) -> tuple[str, bool]:
    """
    Transzkribál. Visszaad (text, success) tuple-t.
    Ha hiba: ('', False)
    """
    try:
        seg = AudioSegment(
            raw_pcm.tobytes(),
            frame_rate=SAMPLE_RATE,
            sample_width=2,
            channels=1,
        )
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        buf.seek(0)
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field("file", buf, filename="audio.wav", content_type="audio/wav")
            async with session.post(STT_URL, data=form, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    print(f"[orchestrator] STT error: {resp.status}")
                    return "", False
                js = await resp.json()
                text = js.get("text", "").strip()
                return text, True
    except Exception as e:
        print(f"[orchestrator] STT hiba: {e}")
        return "", False


async def forward_text(text: str) -> tuple[str, bool]:
    """
    Továbbít szöveget a külső konténernek.
    Visszaad (reply_text, success) tuple-t.
    Ha nem elérhető: ("Szolgáltatás átmenetileg nem elérhető!", False)
    """
    forward_url = config_mgr.get()
    if not forward_url:
        print("[orchestrator] FORWARD_URL nincs beállítva")
        return "Szolgáltatás átmenetileg nem elérhető!", False
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(forward_url, json={"text": text}, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)) as resp:
                if resp.status != 200:
                    print(f"[orchestrator] FORWARD_URL hiba: {resp.status}")
                    return "Szolgáltatás átmenetileg nem elérhető!", False
                js = await resp.json()
                return js.get("text", ""), True
        except aiohttp.ClientConnectorError as e:
            print(f"[orchestrator] FORWARD_URL kapcsolódási hiba: {e}")
            return "Szolgáltatás átmenetileg nem elérhető!", False
        except asyncio.TimeoutError:
            print(f"[orchestrator] FORWARD_URL timeout")
            return "Szolgáltatás átmenetileg nem elérhető!", False
        except Exception as e:
            print(f"[orchestrator] FORWARD_URL hiba: {e}")
            return "Szolgáltatás átmenetileg nem elérhető!", False


async def speak_text(text: str):
    if not PIPER_TTS_URL:
        print(f"[orchestrator] TTS disabled: {text}")
        return
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(PIPER_TTS_URL, json={"text": text, "language": "auto"}, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)) as resp:
                if resp.status != 200:
                    print(f"[orchestrator] TTS error: HTTP {resp.status}")
                    return
                wav = await resp.read()
                if not wav:
                    print(f"[orchestrator] TTS returned empty response")
                    return
                audio = AudioSegment.from_file(io.BytesIO(wav))
                audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1)
                pcm = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
                sd.play(pcm, samplerate=SAMPLE_RATE)
                sd.wait()
        except asyncio.TimeoutError:
            print(f"[orchestrator] TTS timeout")
        except Exception as e:
            print(f"[orchestrator] TTS failed: {e}")


@app.post("/wake")
async def wake():
    print("[orchestrator] wake received, recording...")
    
    # Ellenőrizzük, hogy van-e beállított FORWARD_URL
    forward_url = config_mgr.get()
    if not forward_url:
        print("[orchestrator] FORWARD_URL nincs beállítva!")
        await speak_text("Rendszer nincs konfigurálva. Nyisson meg egy weboldalt a konfiguráláshoz.")
        return JSONResponse({"status": "error", "message": "FORWARD_URL not configured"}, status_code=503)
    
    audio = record_until_silence()
    if audio.size == 0:
        print("[orchestrator] No audio detected, aborting")
        return JSONResponse({"status": "error", "message": "No audio detected"}, status_code=400)
    
    # STT hívás
    text, stt_ok = await transcribe_audio(audio)
    print(f"[orchestrator] STT: {text} (ok={stt_ok})")
    
    # Ha STT hiba
    if not stt_ok:
        await speak_text("Ismeretlen hibát kaptam! Próbálja meg később!")
        return JSONResponse({"status": "error", "message": "STT transcription failed"}, status_code=500)
    
    # Továbbítás a külső konténernek
    reply, forward_ok = await forward_text(text)
    print(f"[orchestrator] reply: {reply} (ok={forward_ok})")
    
    # TTS lejátszása (akár sikeres, akár hibaüzenet)
    await speak_text(reply)
    
    return JSONResponse({"status": "ok", "text": text, "reply": reply})


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

@app.on_event("startup")
async def startup_event():
    """
    Startup: betöltjük a FORWARD_URL-t a config fájlból.
    Ha üres, vár a konfigurációra.
    """
    print("[orchestrator] Indulás...")
    print("[orchestrator] Konfigurációfájl keresése...")
    
    # Összes 2 másodpercen belül betöltjük a config-ot
    max_wait = 20
    waited = 0
    
    while waited < max_wait:
        forward_url = config_mgr.load_from_file()
        if forward_url:
            print("[orchestrator] ✅ FORWARD_URL betöltve, indulás...")
            break
        
        print(f"[orchestrator] ⏳ FORWARD_URL nincs konfigurálva. Nyisson meg a config weboldalt.")
        print(f"[orchestrator]    (Várakozás... {waited}/{max_wait}s)")
        await asyncio.sleep(2)
        waited += 2
    
    if not config_mgr.get():
        print("[orchestrator] ❌ FORWARD_URL nem lett beállítva a config weboldal útján!")
        print("[orchestrator] Az orchestrator működik, de nem fog válaszolni az első wake-ig amíg nincs konfiguráció.")


@app.get("/config-status")
async def config_status():
    """Config állapot lekérdezés"""
    forward_url = config_mgr.get()
    is_configured = bool(forward_url)
    return JSONResponse({
        "configured": is_configured,
        "forward_url": forward_url if is_configured else None
    })