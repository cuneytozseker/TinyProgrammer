# Status Report: Tiny Programmer on RPi Zero 2 W (Bookworm)

**Date:** February 3, 2026
**Hardware:** Raspberry Pi Zero 2 W + Waveshare 4-inch LCD (A) [SPI, ILI9486]
**OS:** Raspberry Pi OS Lite (Bookworm 64-bit)

## Current State
- **Application Logic:** Fully functional (v0.3).
    - AI writes code (Qwen 2.5 0.5B via Ollama).
    - Self-correction loop works.
    - `tiny_canvas` API works.
- **Display Hardware:** Verified working.
    - Driver (`waveshare35a` overlay) loads.
    - `/dev/fb1` exists.
    - Console shows text (Login prompt).
    - `dd` to `/dev/fb1` produces static noise (HW path valid).
- **The Issue:**
    - We cannot get Python/Pygame to clear the screen or draw graphics over the console.
    - The screen stays stuck on the Login Prompt (sometimes cursor freezes).
    - Direct writes (`open().write()`) and `mmap` writes to `/dev/fb1` do not trigger a screen refresh in Python, even though `dd` works.

## Things We Tried (and Failed)

### 1. Pygame Drivers (SDL2)
- **`fbcon`**: Failed. "Video system not initialized". Deprecated in Bookworm SDL.
- **`kmsdrm`**: Failed. Defaults to HDMI (`card0`), ignores SPI display.
- **`dummy` + Direct Write**: Python script runs, but screen doesn't update (remains login text).
- **`linuxfb`**: Failed to init.

### 2. Kernel/Driver Config
- **`dtoverlay=waveshare35a`**: Works for console text.
- **Disabling `vc4-kms-v3d`**: Necessary for `fbcon` mapping, but SDL still hates it.
- **`con2fbmap 1 0`**: Attempted to move console to HDMI. Failed to clear `fb1` fully (text remains).
- **Unbinding Console (`vtcon1`)**: Stops cursor blink, but pixels remain stuck.

### 3. Other Tools
- **`rpi-fbcp`**: Failed to build/run (missing `libbcm_host` on Bookworm).
- **`fbcp-ili9341`**: Not attempted (complex build for ILI9486).

## Next Steps / Solution Path
To get this working, we likely need one of the following:
1.  **Downgrade OS (RECOMMENDED)**: Use **Raspberry Pi OS Bullseye (Legacy) Lite**. The old `fbcon` driver works perfectly there, and most Waveshare tutorials are designed for it. This is the fastest path to a working display.
2.  **Use `fbturbo`**: Manually install this legacy X11/FB driver to give SDL a valid target on Bookworm.
3.  **Kernel Force Refresh**: Find the specific `ioctl` call that triggers the Waveshare driver to flush the buffer (since `mmap` alone isn't doing it on Bookworm).

## How to Resume
1.  Check `STATUS.md`.
2.  Consider flashing **Bullseye Lite** for an easy win.
3.  Or continue debugging `fbtft` refresh triggers on Bookworm.
