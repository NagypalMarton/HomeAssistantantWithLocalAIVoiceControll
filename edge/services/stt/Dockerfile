FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

# Upgrade pip, install av pre-built binary, then requirements
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --only-binary av av && \
    pip install --no-cache-dir -r requirements.txt

COPY app.py /app/

# Model storage
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
EXPOSE 10300

CMD ["python", "app.py"]
