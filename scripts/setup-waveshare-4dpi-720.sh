#!/usr/bin/env bash
# Configure the Waveshare 4inch DPI LCD (C) 720x720 panel.
#
# Run this on the Raspberry Pi from the TinyProgrammer checkout, after the
# normal TinyProgrammer setup has created the repo and .env:
#   ./scripts/setup-waveshare-4dpi-720.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Override both values together when intentionally testing a newer vendor bundle.
DTBO_URL="${TINYPROGRAMMER_DTBO_URL:-https://files.waveshare.com/upload/8/8a/4DPIC-DTBO.zip}"
DTBO_SHA256="${TINYPROGRAMMER_DTBO_SHA256:-b09a4934ca48d873ba00aed8b087698854538477787f56c19b4c1edfae080c1d}"
DISPLAY_PROFILE="${TINYPROGRAMMER_DISPLAY_PROFILE:-waveshare-4dpi-720}"

BOOT_BLOCK_BEGIN="# BEGIN TinyProgrammer Waveshare 4inch DPI LCD (C)"
BOOT_BLOCK_END="# END TinyProgrammer Waveshare 4inch DPI LCD (C)"
TMP_DIR=""

DISPLAY_BLOCK_BASE="$(cat <<'EOF'
dtparam=spi=off
dtoverlay=vc4-kms-DPI-4inch
dtoverlay=waveshare-4dpi
EOF
)"

fail() {
    echo "$*" >&2
    exit 1
}

as_root() {
    if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

cleanup() {
    if [[ -n "$TMP_DIR" ]]; then
        rm -rf "$TMP_DIR"
    fi
}

sha256_file() {
    local file="$1"

    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        fail "sha256sum or shasum is required to verify Waveshare overlays."
    fi
}

verify_dtbo_zip() {
    local zip_file="$1"
    local actual_sha256

    actual_sha256="$(sha256_file "$zip_file")"
    if [[ "$actual_sha256" != "$DTBO_SHA256" ]]; then
        fail "Waveshare overlay checksum mismatch. Expected $DTBO_SHA256, got $actual_sha256."
    fi
}

replace_managed_block() {
    local file="$1"
    local begin="$2"
    local end="$3"
    local block="$4"
    local tmp
    local out

    tmp="$(mktemp)"
    out="$(mktemp)"

    awk -v begin="$begin" -v end="$end" '
        $0 == begin {skip=1; next}
        $0 == end {skip=0; next}
        !skip {print}
    ' "$file" > "$tmp"

    {
        cat "$tmp"
        printf '\n%s\n' "$begin"
        printf '%s\n' "$block"
        printf '%s\n' "$end"
    } > "$out"

    as_root install -m 0644 "$out" "$file"
    rm -f "$tmp" "$out"
}

set_env() {
    local key="$1"
    local value="$2"
    local env_file="$REPO_DIR/.env"

    if [[ ! -f "$env_file" ]]; then
        cp "$REPO_DIR/.env.example" "$env_file"
    fi

    if grep -qE "^${key}=" "$env_file"; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
    else
        printf '%s=%s\n' "$key" "$value" >> "$env_file"
    fi
}

build_display_block() {
    local boot_config="$1"

    if grep -Eq '^[[:space:]]*dtoverlay=vc4-kms-v3d([,[:space:]]|$)' "$boot_config"; then
        printf '%s' "$DISPLAY_BLOCK_BASE"
    else
        printf 'dtoverlay=vc4-kms-v3d\n%s' "$DISPLAY_BLOCK_BASE"
    fi
}

install_waveshare_overlays() {
    local overlay_dir="$1"

    TMP_DIR="$(mktemp -d)"
    trap cleanup EXIT

    curl -fsSL "$DTBO_URL" -o "$TMP_DIR/4DPIC-DTBO.zip"
    verify_dtbo_zip "$TMP_DIR/4DPIC-DTBO.zip"
    unzip -q -o "$TMP_DIR/4DPIC-DTBO.zip" -d "$TMP_DIR/dtbo"

    while IFS= read -r dtbo; do
        as_root install -m 0644 "$dtbo" "$overlay_dir/$(basename "$dtbo")"
    done < <(find "$TMP_DIR/dtbo" -type f -name '*.dtbo' | sort)
}

# Main procedure

if [[ "${EUID:-$(id -u)}" -ne 0 ]] && ! command -v sudo >/dev/null 2>&1; then
    fail "sudo is required when not running as root."
fi

BOOT_DIR="/boot/firmware"
if [[ ! -d "$BOOT_DIR" ]]; then
    BOOT_DIR="/boot"
fi

BOOT_CONFIG="$BOOT_DIR/config.txt"
OVERLAY_DIR="$BOOT_DIR/overlays"

if [[ ! -f "$BOOT_CONFIG" || ! -d "$OVERLAY_DIR" ]]; then
    fail "Could not find Raspberry Pi boot files under /boot/firmware or /boot."
fi

echo "[TinyProgrammer] Configuring Waveshare 4inch DPI LCD (C)"
echo "  boot dir: $BOOT_DIR"
echo "  profile:  $DISPLAY_PROFILE"

if command -v curl >/dev/null 2>&1 && command -v unzip >/dev/null 2>&1; then
    echo "[1/4] curl/unzip already available"
else
    echo "[1/4] Installing curl/unzip..."
    as_root apt-get update
    as_root apt-get install -y --no-install-recommends curl unzip
fi

echo "[2/4] Installing Waveshare display overlays..."
install_waveshare_overlays "$OVERLAY_DIR"

echo "[3/4] Updating boot config..."
replace_managed_block \
    "$BOOT_CONFIG" \
    "$BOOT_BLOCK_BEGIN" \
    "$BOOT_BLOCK_END" \
    "$(build_display_block "$BOOT_CONFIG")"

echo "[4/4] Updating TinyProgrammer profile..."
set_env "DISPLAY_PROFILE" "$DISPLAY_PROFILE"

echo
echo "Waveshare display configuration complete."
echo "Reboot for the boot overlays to take effect:"
echo "  sudo reboot"
