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

# Upgrade pip and install wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install av pre-built binary first to avoid compilation issues
RUN pip install --no-cache-dir --only-binary av av

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/

# Model storage
RUN mkdir -p /data

ENV PYTHONUNBUFFERED=1
EXPOSE 10300

CMD ["python", "app.py"]
