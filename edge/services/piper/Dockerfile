# Dockerfile
FROM python:3.11-slim-bookworm

# 1. Rendszer csomagok telepítése (hanghoz és letöltéshez)
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    alsa-utils \
    libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Piper letöltése (32-bites verzió a biztos kompatibilitásért)
# Ha biztosan 64-bites a Docker környezeted, átírhatod arm64-re, de az armv7 mindenen fut.
RUN wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz && \
    tar -xvf piper_arm64.tar.gz && \
    rm piper_arm64.tar.gz

# 3. Magyar hang (Tamás) letöltése közvetlenül a képbe
RUN mkdir -p piper_voices && \
    wget -O piper_voices/hu_HU-imre-medium.onnx https://huggingface.co/rhasspy/piper-voices/blob/main/hu/hu_HU/imre/medium/hu_HU-imre-medium.onnx && \
    wget -O piper_voices/hu_HU-imre-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/blob/main/hu/hu_HU/imre/medium/hu_HU-imre-medium.onnx.json

# 4. A Python kód bemásolása
COPY app.py .

# Indításkor ez fut le
ENTRYPOINT ["python3", "app.py"]
