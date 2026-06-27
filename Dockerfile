FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

# system deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    antiword \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app and worker
COPY app ./app
COPY worker ./worker

# Cloud Run uses 8080
ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
