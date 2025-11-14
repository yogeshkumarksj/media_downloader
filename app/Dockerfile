FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install ffmpeg + NodeJS (required for yt-dlp + YouTube JS player)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg curl gnupg ca-certificates && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy all project files (including cookies)
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --upgrade yt-dlp

EXPOSE 8000

# Run the Telegram bot using FastAPI + uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
