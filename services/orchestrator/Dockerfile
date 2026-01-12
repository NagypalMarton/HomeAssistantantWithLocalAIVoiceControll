FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libportaudio2 libsndfile1 ffmpeg \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt
COPY app.py /app/app.py

ENV PYTHONUNBUFFERED=1
EXPOSE 8003
CMD ["python", "app.py"]
