# Multi-stage build with Alpine for minimal runtime size
FROM alpine:3.20 AS builder

# Install build dependencies
# Alpine only ships python3; symlink python for compatibility with packages/scripts that call python
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
    libpng-dev \
    && ln -sf python3 /usr/local/bin/python

WORKDIR /build

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM alpine:3.20

# Install runtime libraries only
# Alpine only ships python3; symlink python for compatibility with packages/scripts that call python
RUN apk add --no-cache \
    python3 \
    py3-pip \
    sdl2 \
    sdl2_image \
    sdl2_ttf \
    sdl2_mixer \
    freetype \
    libjpeg \
    libpng \
    ttf-dejavu \
    && ln -sf python3 /usr/local/bin/python

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/lib/python3.12/site-packages /usr/lib/python3.12/site-packages

COPY . .

RUN chmod +x entrypoint.sh

VOLUME ["/app/programs"]
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
