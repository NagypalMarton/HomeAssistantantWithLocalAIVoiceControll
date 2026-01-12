FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt
COPY app.py /app/app.py
COPY index.html /app/index.html

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "app.py"]
