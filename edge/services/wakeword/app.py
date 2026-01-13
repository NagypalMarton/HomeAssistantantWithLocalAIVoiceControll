#!/usr/bin/env python3
"""
Wyoming-OpenWakeWord service
Alexa wake word detection
"""
import asyncio
import logging
import os
from functools import partial

from wyoming.event import Event
from wyoming.info import Attribution, Info, WakeModel, WakeProgram
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.wake import Detect, Detection
from wyoming.audio import AudioChunk

import numpy as np
from openwakeword.model import Model

_LOGGER = logging.getLogger(__name__)

# Alexa wake word
WAKE_WORD = os.getenv("WAKE_WORD", "alexa")
THRESHOLD = float(os.getenv("THRESHOLD", "0.5"))


class OpenWakeWordEventHandler(AsyncEventHandler):
    """Event handler for Wyoming protocol"""
    
    def __init__(self, wyoming_info: Info, model: Model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wyoming_info = wyoming_info
        self.model = model
        
    async def handle_event(self, event: Event) -> bool:
        if AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            
            # Convert audio to float32 for OpenWakeWord
            audio_array = np.frombuffer(chunk.audio, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Predict
            prediction = self.model.predict(audio_array)
            
            # Check if wake word detected
            for wake_word, score in prediction.items():
                if wake_word == WAKE_WORD and score >= THRESHOLD:
                    _LOGGER.info(f"Wake word detected: {wake_word} (score: {score:.2f})")
                    
                    # Send detection event
                    await self.write_event(
                        Detection(
                            name=wake_word,
                            timestamp=0,
                        ).event()
                    )
                    
        elif Detect.is_type(event.type):
            # Start detection (if needed)
            pass
            
        return True


async def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    _LOGGER.info(f"Loading OpenWakeWord model: {WAKE_WORD}")
    
    # Load model
    # If no custom models specified, will download default models including 'alexa'
    model = Model(wakeword_models=[WAKE_WORD] if WAKE_WORD else None)
    
    _LOGGER.info("Model loaded successfully")
    
    # Wyoming info
    wyoming_info = Info(
        wake=[
            WakeProgram(
                name="openwakeword",
                description="OpenWakeWord for Wyoming",
                attribution=Attribution(
                    name="David Scripka",
                    url="https://github.com/dscripka/openWakeWord"
                ),
                installed=True,
                models=[
                    WakeModel(
                        name=WAKE_WORD,
                        description=f"{WAKE_WORD} wake word",
                        attribution=Attribution(
                            name="David Scripka",
                            url="https://github.com/dscripka/openWakeWord"
                        ),
                        installed=True,
                        languages=["en"],
                    )
                ],
            )
        ],
    )
    
    # Start server
    server = AsyncServer.from_uri("tcp://0.0.0.0:10400")
    _LOGGER.info("Starting Wyoming OpenWakeWord server on tcp://0.0.0.0:10400")
    
    await server.run(partial(OpenWakeWordEventHandler, wyoming_info, model))


if __name__ == "__main__":
    asyncio.run(main())
