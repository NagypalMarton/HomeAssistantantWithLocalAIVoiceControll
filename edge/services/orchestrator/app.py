#!/usr/bin/env python3
"""
Orchestrator service
Integrates Wyoming services with Home Assistant Conversation API
"""
import asyncio
import logging
import os
import io
import json
import wave
from pathlib import Path
import numpy as np
import sounddevice as sd

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient
from wyoming.tts import Synthesize
from wyoming.wake import Detect, Detection

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Configuration
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
RECORD_SECONDS = int(os.getenv("RECORD_SECONDS", "5"))
STT_URI = os.getenv("STT_URI", "tcp://stt:10300")
TTS_URI = os.getenv("TTS_URI", "tcp://piper:10200")
WAKEWORD_URI = os.getenv("WAKEWORD_URI", "tcp://wakeword:10400")
CONFIG_FILE = Path(os.getenv("CONFIG_FILE", "/app/config/ha_config.json"))

# These will be loaded from config file
HA_URL = ""
HA_TOKEN = ""


def load_ha_config():
    """Load Home Assistant configuration from file"""
    global HA_URL, HA_TOKEN
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                HA_URL = config.get("ha_url", "").strip()
                HA_TOKEN = config.get("ha_token", "").strip()
                _LOGGER.info(f"Home Assistant config loaded: {HA_URL}")
                return True
    except Exception as e:
        _LOGGER.error(f"Error loading HA config: {e}")
    return False


async def record_audio(duration: float) -> bytes:
    """Record audio from microphone"""
    _LOGGER.info(f"Recording for {duration} seconds...")
    
    # Record audio
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16'
    )
    sd.wait()
    
    # Convert to WAV format
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio.tobytes())
    
    return wav_io.getvalue()


async def transcribe_with_stt(audio_bytes: bytes) -> str:
    """Transcribe audio using Wyoming STT"""
    _LOGGER.info("Transcribing audio...")
    
    try:
        async with AsyncClient.from_uri(STT_URI) as client:
            # Send audio
            await client.write_event(AudioStart(rate=SAMPLE_RATE, width=2, channels=1).event())
            
            # Send audio in chunks
            chunk_size = 8192
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                await client.write_event(
                    AudioChunk(audio=chunk, rate=SAMPLE_RATE, width=2, channels=1).event()
                )
            
            await client.write_event(AudioStop().event())
            await client.write_event(Transcribe().event())
            
            # Wait for transcript
            while True:
                event = await client.read_event()
                if event is None:
                    break
                    
                if Transcript.is_type(event.type):
                    transcript = Transcript.from_event(event)
                    _LOGGER.info(f"Transcript: {transcript.text}")
                    return transcript.text
                    
        return ""
    except Exception as e:
        _LOGGER.error(f"STT error: {e}")
        return ""


async def send_to_home_assistant(text: str) -> str:
    """Send text to Home Assistant Conversation API"""
    _LOGGER.info(f"Sending to Home Assistant: {text}")
    
    if not HA_TOKEN:
        _LOGGER.error("HA_TOKEN not configured!")
        return "Rendszer nincs konfigurálva. Nyisson meg egy weboldalt a konfiguráláshoz: http://localhost:8000"
    
    if not HA_URL:
        _LOGGER.error("HA_URL not configured!")
        return "Home Assistant URL nincs beállítva."
    
    url = f"{HA_URL}/api/conversation/process"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "text": text,
        "language": "hu"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    _LOGGER.error(f"Home Assistant error: {resp.status}")
                    text = await resp.text()
                    _LOGGER.error(f"Response: {text}")
                    return "Sajnálom, a Home Assistant nem válaszolt megfelelően."
                
                result = await resp.json()
                
                # Extract response text
                response_text = result.get("response", {}).get("speech", {}).get("plain", {}).get("speech", "")
                
                if not response_text:
                    _LOGGER.warning("Empty response from Home Assistant")
                    return "Nem kaptam választ a Home Assistant-tól."
                
                _LOGGER.info(f"Home Assistant response: {response_text}")
                return response_text
                
    except aiohttp.ClientConnectorError as e:
        _LOGGER.error(f"Cannot connect to Home Assistant: {e}")
        return "Nem tudok csatlakozni a Home Assistant-hoz."
    except asyncio.TimeoutError:
        _LOGGER.error("Home Assistant timeout")
        return "A Home Assistant nem válaszolt időben."
    except Exception as e:
        _LOGGER.error(f"Home Assistant error: {e}")
        return "Hiba történt a Home Assistant kommunikáció során."


async def speak_with_tts(text: str):
    """Speak text using Wyoming TTS"""
    _LOGGER.info(f"Speaking: {text}")
    
    try:
        async with AsyncClient.from_uri(TTS_URI) as client:
            # Request synthesis
            await client.write_event(Synthesize(text=text).event())
            
            # Collect audio
            audio_bytes = bytearray()
            
            while True:
                event = await client.read_event()
                if event is None:
                    break
                    
                if AudioChunk.is_type(event.type):
                    chunk = AudioChunk.from_event(event)
                    audio_bytes.extend(chunk.audio)
                    
                elif AudioStop.is_type(event.type):
                    break
            
            if audio_bytes:
                # Play audio
                audio_array = np.frombuffer(bytes(audio_bytes), dtype=np.int16).astype(np.float32) / 32768.0
                sd.play(audio_array, samplerate=SAMPLE_RATE)
                sd.wait()
                _LOGGER.info("Playback finished")
            else:
                _LOGGER.warning("No audio received from TTS")
                
    except Exception as e:
        _LOGGER.error(f"TTS error: {e}")


async def listen_for_wake_word():
    """Listen for wake word from Wyoming WakeWord service"""
    _LOGGER.info("Listening for wake word...")
    
    # Open microphone stream
    chunk_size = 1024
    
    try:
        async with AsyncClient.from_uri(WAKEWORD_URI) as client:
            # Start detection
            await client.write_event(Detect().event())
            
            # Stream audio from microphone
            def audio_callback(indata, frames, time_info, status):
                if status:
                    _LOGGER.warning(f"Audio status: {status}")
                # Queue audio for Wyoming
                audio_bytes = indata.copy().tobytes()
                asyncio.create_task(
                    client.write_event(
                        AudioChunk(
                            audio=audio_bytes,
                            rate=SAMPLE_RATE,
                            width=2,
                            channels=1
                        ).event()
                    )
                )
            
            # Start audio stream
            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16',
                blocksize=chunk_size,
                callback=audio_callback
            )
            
            with stream:
                # Wait for detection
                while True:
                    event = await client.read_event()
                    if event is None:
                        break
                        
                    if Detection.is_type(event.type):
                        detection = Detection.from_event(event)
                        _LOGGER.info(f"Wake word detected: {detection.name}")
                        stream.stop()
                        return True
                        
    except Exception as e:
        _LOGGER.error(f"Wake word detection error: {e}")
        return False


async def handle_wake_event():
    """Handle wake word event: record -> transcribe -> HA -> speak"""
    _LOGGER.info("Wake word detected! Starting interaction...")
    
    # Record audio
    audio_bytes = await record_audio(RECORD_SECONDS)
    
    # Transcribe
    text = await transcribe_with_stt(audio_bytes)
    
    if not text:
        await speak_with_tts("Sajnálom, nem értettem.")
        return
    
    # Send to Home Assistant
    response = await send_to_home_assistant(text)
    
    # Speak response
    await speak_with_tts(response)


async def main():
    """Main loop"""
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info("Orchestrator starting...")
    
    # Load Home Assistant configuration
    _LOGGER.info(f"Config file: {CONFIG_FILE}")
    
    # Wait for config file
    max_wait = 30
    waited = 0
    while waited < max_wait:
        if load_ha_config():
            break
        _LOGGER.info(f"Waiting for HA config ({waited}/{max_wait}s)...")
        await asyncio.sleep(2)
        waited += 2
    
    if not HA_TOKEN or not HA_URL:
        _LOGGER.error("Home Assistant configuration not found!")
        _LOGGER.error("Please configure at http://localhost:8000")
        # Continue anyway - might get configured later
    
    _LOGGER.info(f"STT URI: {STT_URI}")
    _LOGGER.info(f"TTS URI: {TTS_URI}")
    _LOGGER.info(f"Wake word URI: {WAKEWORD_URI}")
    _LOGGER.info(f"Home Assistant URL: {HA_URL}")
    
    # Main loop: listen for wake word
    while True:
        try:
            detected = await listen_for_wake_word()
            if detected:
                await handle_wake_event()
        except KeyboardInterrupt:
            _LOGGER.info("Shutting down...")
            break
        except Exception as e:
            _LOGGER.error(f"Error in main loop: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)