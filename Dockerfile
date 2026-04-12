FROM python:3.11-slim

# Install SDL2 and system deps needed by pygame + Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-ttf-dev \
    libsdl2-mixer-dev \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

# Generated programs are written and run here
VOLUME ["/app/programs"]

EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
