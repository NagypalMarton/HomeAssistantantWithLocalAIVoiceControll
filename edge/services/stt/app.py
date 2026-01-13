#!/usr/bin/env python3
"""
Wyoming-Whisper STT service
Magyar nyelv támogatással, tiny model
"""
import asyncio
import logging
import os
from functools import partial

from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import AsrModel, AsrProgram, Attribution, Info
from wyoming.server import AsyncEventHandler, AsyncServer

from faster_whisper import WhisperModel

_LOGGER = logging.getLogger(__name__)

# Magyar nyelv + tiny model
MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
LANGUAGE = os.getenv("WHISPER_LANGUAGE", "hu")
BEAM_SIZE = int(os.getenv("BEAM_SIZE", "1"))

class WhisperEventHandler(AsyncEventHandler):
    """Event handler for Wyoming protocol"""
    
    def __init__(self, wyoming_info: Info, model: WhisperModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wyoming_info = wyoming_info
        self.model = model
        self.audio_buffer = bytes()
        
    async def handle_event(self, event: Event) -> bool:
        if AudioStart.is_type(event.type):
            self.audio_buffer = bytes()
            _LOGGER.debug("Audio stream started")
            
        elif AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            self.audio_buffer += chunk.audio
            
        elif AudioStop.is_type(event.type):
            _LOGGER.debug("Audio stream stopped, transcribing...")
            
            # Convert to format Whisper expects
            import io
            import wave
            import numpy as np
            
            # Audio buffer to numpy array (16-bit PCM to float32)
            audio_array = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            segments, info = await asyncio.get_event_loop().run_in_executor(
                None,
                partial(
                    self.model.transcribe,
                    audio_array,
                    language=LANGUAGE,
                    beam_size=BEAM_SIZE,
                    vad_filter=True,
                )
            )
            
            # Collect all segments
            text = " ".join([segment.text for segment in segments]).strip()
            _LOGGER.info(f"Transcription: {text}")
            
            # Send transcript
            await self.write_event(Transcript(text=text).event())
            
        elif Transcribe.is_type(event.type):
            # Direct transcription request (not streaming)
            pass
            
        return True


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info(f"Loading Whisper model: {MODEL_NAME} (language: {LANGUAGE})")
    
    # Load model (CPU)
    model = WhisperModel(
        MODEL_NAME,
        device="cpu",
        compute_type="int8",
        download_root="/data"
    )
    
    _LOGGER.info("Model loaded successfully")
    
    # Wyoming info
    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="faster-whisper",
                description="Whisper ASR for Wyoming",
                attribution=Attribution(
                    name="Systran",
                    url="https://github.com/SYSTRAN/faster-whisper"
                ),
                installed=True,
                models=[
                    AsrModel(
                        name=MODEL_NAME,
                        description=f"Whisper {MODEL_NAME} model",
                        attribution=Attribution(
                            name="OpenAI",
                            url="https://github.com/openai/whisper"
                        ),
                        installed=True,
                        version="1.0.0",
                        languages=[LANGUAGE],
                    )
                ],
            )
        ],
    )
    
    # Start server
    server = AsyncServer.from_uri("tcp://0.0.0.0:10300")
    _LOGGER.info("Starting Wyoming Whisper server on tcp://0.0.0.0:10300")
    
    await server.run(partial(WhisperEventHandler, wyoming_info, model))


if __name__ == "__main__":
    asyncio.run(main())
