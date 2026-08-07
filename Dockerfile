# Multi-stage build with Alpine for minimal runtime size
FROM alpine:3.20 AS builder

# Install build dependencies
RUN apk add --no-cache \
    python3-dev \
    py3-pip \
    build-base \
    sdl2-dev \
    sdl2_image-dev \
    sdl2_ttf-dev \
    sdl2_mixer-dev \
    freetype-dev \
    libjpeg-turbo-dev \
    libpng-dev

WORKDIR /build

COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM alpine:3.20

# Install runtime libraries only
RUN apk add --no-cache \
    python3 \
    sdl2 \
    sdl2_image \
    sdl2_ttf \
    sdl2_mixer \
    freetype \
    libjpeg \
    libpng \
    ttf-dejavu

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN chmod +x entrypoint.sh

# Generated programs are written and run here
VOLUME ["/app/programs"]
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
