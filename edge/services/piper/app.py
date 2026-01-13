#!/usr/bin/env python3
"""
Wyoming-Piper TTS service
Magyar anna hang
"""
import asyncio
import logging
import os
from functools import partial

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Attribution, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.tts import Synthesize

import wave
import io
from piper import PiperVoice

_LOGGER = logging.getLogger(__name__)

# Magyar anna hang
VOICE_MODEL = os.getenv("PIPER_VOICE", "hu_HU-anna-medium")


class PiperEventHandler(AsyncEventHandler):
    """Event handler for Wyoming protocol"""
    
    def __init__(self, wyoming_info: Info, voice: PiperVoice, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wyoming_info = wyoming_info
        self.voice = voice
        
    async def handle_event(self, event: Event) -> bool:
        if Synthesize.is_type(event.type):
            synthesize = Synthesize.from_event(event)
            _LOGGER.debug(f"Synthesizing: {synthesize.text}")
            
            # Send audio start
            await self.write_event(
                AudioStart(
                    rate=self.voice.config.sample_rate,
                    width=2,  # 16-bit
                    channels=1,
                ).event()
            )
            
            # Generate audio in chunks
            audio_bytes = bytes()
            for audio_chunk in self.voice.synthesize_stream_raw(synthesize.text):
                audio_bytes += audio_chunk
                
                # Send in chunks
                await self.write_event(
                    AudioChunk(
                        audio=audio_chunk,
                        rate=self.voice.config.sample_rate,
                        width=2,
                        channels=1,
                    ).event()
                )
            
            # Send audio stop
            await self.write_event(AudioStop().event())
            _LOGGER.info(f"Synthesized {len(audio_bytes)} bytes")
            
        return True


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info(f"Loading Piper voice: {VOICE_MODEL}")
    
    # Load voice
    voice = PiperVoice.load(
        model_path=f"/data/{VOICE_MODEL}.onnx",
        config_path=f"/data/{VOICE_MODEL}.onnx.json",
    )
    
    _LOGGER.info("Voice loaded successfully")
    
    # Wyoming info
    wyoming_info = Info(
        tts=[
            TtsProgram(
                name="piper",
                description="Piper TTS for Wyoming",
                attribution=Attribution(
                    name="Rhasspy",
                    url="https://github.com/rhasspy/piper"
                ),
                installed=True,
                voices=[
                    TtsVoice(
                        name=VOICE_MODEL,
                        description="Hungarian Anna voice",
                        attribution=Attribution(
                            name="Rhasspy",
                            url="https://github.com/rhasspy/piper"
                        ),
                        installed=True,
                        languages=["hu"],
                    )
                ],
            )
        ],
    )
    
    # Start server
    server = AsyncServer.from_uri("tcp://0.0.0.0:10200")
    _LOGGER.info("Starting Wyoming Piper server on tcp://0.0.0.0:10200")
    
    await server.run(partial(PiperEventHandler, wyoming_info, voice))


if __name__ == "__main__":
    asyncio.run(main())
