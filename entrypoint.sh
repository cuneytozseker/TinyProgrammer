#!/bin/sh
# Ensure bind-mounted files exist as files (not directories) and are writable.
# When lessons.md or config_overrides.json don't exist on the host before
# `docker compose up`, Docker may create them as root-owned directories,
# causing [Errno 13] Permission denied errors at runtime.

for f in /app/lessons.md /app/config_overrides.json; do
    if [ -d "$f" ]; then
        rmdir "$f" 2>/dev/null || rm -rf "$f"
    fi
done

touch /app/lessons.md

if [ ! -s /app/config_overrides.json ]; then
    echo '{}' > /app/config_overrides.json
fi

exec python -u main.py
