import os
import sys
import time
import io
import queue
import threading
import asyncio
import numpy as np
import sounddevice as sd
import aiohttp
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydub import AudioSegment

SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8003/wake")
STT_URL = os.getenv("STT_URL", "http://stt:8002/transcribe")
WAKEWORD_MODEL_PATH = os.getenv("WAKEWORD_MODEL_PATH", "")
WAKEWORD_WORD = os.getenv("WAKEWORD_WORD", "mikrobi").lower()
DETECTION_WINDOW_MS = int(os.getenv("DETECTION_WINDOW_MS", "1200"))

# Magic constants
OWW_SCORE_THRESHOLD = 0.5
ENERGY_THRESHOLD = 0.2
DETECTION_COOLDOWN = 2.0  # seconds
HTTP_TIMEOUT = 30  # seconds

app = FastAPI()

try:
    from openwakeword import Model
    oww_model = Model(model_paths=[WAKEWORD_MODEL_PATH] if WAKEWORD_MODEL_PATH else None)
    use_oww = True
except Exception as e:
    print(f"[wakeword] openwakeword init failed or not configured: {e}")
    oww_model = None
    use_oww = False

_audio_q: queue.Queue[np.ndarray] = queue.Queue(maxsize=8)
_detect_thread: threading.Thread | None = None
_stop_flag = threading.Event()
_event_loop: asyncio.AbstractEventLoop | None = None

# rolling buffer ~ DETECTION_WINDOW_MS
_roll_buf = np.zeros(int(SAMPLE_RATE * DETECTION_WINDOW_MS / 1000), dtype=np.int16)
_roll_idx = 0


def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"[wakeword] audio status: {status}")
    audio = (indata.copy().reshape(-1)).astype(np.int16)
    # Update rolling buffer
    global _roll_idx
    n = audio.size
    if n >= _roll_buf.size:
        _roll_buf[:] = audio[-_roll_buf.size:]
        _roll_idx = 0
    else:
        end = _roll_idx + n
        if end <= _roll_buf.size:
            _roll_buf[_roll_idx:end] = audio
        else:
            part1 = _roll_buf.size - _roll_idx
            _roll_buf[_roll_idx:] = audio[:part1]
            _roll_buf[:n - part1] = audio[part1:]
        _roll_idx = (end) % _roll_buf.size
    try:
        _audio_q.put_nowait(audio.astype(np.float32) / 32768.0)
    except queue.Full:
        pass


async def notify_orchestrator():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(ORCHESTRATOR_URL, json={"wake": WAKEWORD_WORD}) as resp:
                print(f"[wakeword] orchestrator notify status: {resp.status}")
        except Exception as e:
            print(f"[wakeword] notify failed: {e}")


async def stt_contains_wakeword(pcm: np.ndarray) -> bool:
    seg = AudioSegment(
        pcm.tobytes(),
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
        try:
            async with session.post(STT_URL, data=form) as resp:
                js = await resp.json()
                text = js.get("text", "").lower()
                return WAKEWORD_WORD in text
        except Exception as e:
            print(f"[wakeword] STT check failed: {e}")
            return False


def detector_loop():
    print("[wakeword] detector loop started")
    last_trigger = 0.0
    cooldown = DETECTION_COOLDOWN
    while not _stop_flag.is_set():
        try:
            audio = _audio_q.get(timeout=0.5)
        except queue.Empty:
            continue
        if use_oww and oww_model is not None:
            scores = oww_model.predict(np.array(audio, dtype=np.float32), SAMPLE_RATE)
            if np.max(scores) > OWW_SCORE_THRESHOLD and (time.time() - last_trigger) > cooldown:
                last_trigger = time.time()
                sd.stop()  # free device for orchestrator
                if _event_loop:
                    asyncio.run_coroutine_threadsafe(notify_orchestrator(), _event_loop)
        else:
            energy = np.mean(np.abs(audio))
            if energy > ENERGY_THRESHOLD and (time.time() - last_trigger) > cooldown:
                # Run quick STT on rolling buffer
                if _event_loop:
                    future = asyncio.run_coroutine_threadsafe(stt_contains_wakeword(_roll_buf.copy()), _event_loop)
                    try:
                        if future.result(timeout=5.0):
                            last_trigger = time.time()
                            sd.stop()
                    except Exception as e:
                        print(f"[wakeword] STT check error: {e}")


@app.on_event("startup")
async def startup_event():
    global _detect_thread, _event_loop
    _event_loop = asyncio.get_event_loop()
    print(f"[wakeword] starting stream at {SAMPLE_RATE} Hz")
    sd.default.samplerate = SAMPLE_RATE
    sd.default.channels = 1
    sd.InputStream(callback=audio_callback, dtype='int16').start()
    _detect_thread = threading.Thread(target=detector_loop, daemon=True)
    _detect_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    _stop_flag.set()
    sd.stop()


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
