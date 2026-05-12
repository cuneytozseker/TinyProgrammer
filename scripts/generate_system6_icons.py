#!/usr/bin/env python3
"""Generate pixel-crisp System 6 chrome icons from editable source PNGs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = REPO_ROOT / "display" / "assets" / "system6" / "source"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "display" / "assets" / "system6" / "generated"

ICON_FILENAMES = (
    "icon-new-system6.png",
    "icon-open-system6.png",
    "icon-save-system6.png",
    "icon-run-system6.png",
    "icon-settings-system6.png",
    "logo-system6.png",
)
TOOLBAR_ICON_SIZES = (8, 12, 16, 24, 32, 40, 48, 56, 64)

# The menu logo is fit into the reference apple-icon slot before it is centered.
# Heights 15 and 23 are the exact fitted logo sizes for the 480x320 and 800x480
# chrome layouts; keeping those as generated rasters avoids one-pixel runtime
# scaling at the most common resolutions.
LOGO_ICON_SIZES = (8, 12, 15, 16, 23, 24, 32, 40, 48, 56, 64)

BLACK_RGBA = (0, 0, 0, 255)
WHITE_RGBA = (255, 255, 255, 255)

# The source artwork is 512px antialiased PNG, but the runtime chrome wants
# opaque black/white pixel art. A 96/255 coverage threshold keeps one-pixel
# strokes alive at 8-24px while avoiding the bloated strokes caused by treating
# every partially covered source pixel as opaque.
DEFAULT_COVERAGE_THRESHOLD = 96
BLACK_WHITE_LUMINANCE_SPLIT = 384


def visible_crop(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    bounds = rgba.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("source image has no visible pixels")
    return rgba.crop(bounds)


def fit_size(source_size: tuple[int, int], extent: int) -> tuple[int, int]:
    source_w, source_h = source_size
    scale = min(extent / source_w, extent / source_h)
    return (
        max(1, int(source_w * scale + 0.5)),
        max(1, int(source_h * scale + 0.5)),
    )


def rasterize_icon(
    source: Image.Image,
    extent: int,
    coverage_threshold: int,
) -> Image.Image:
    cropped = visible_crop(source)
    target_size = fit_size(cropped.size, extent)
    pixels = np.asarray(cropped)
    alpha = pixels[:, :, 3] > 0
    luminance = (
        pixels[:, :, 0].astype(np.uint16)
        + pixels[:, :, 1].astype(np.uint16)
        + pixels[:, :, 2].astype(np.uint16)
    )
    black_mask = (alpha & (luminance < BLACK_WHITE_LUMINANCE_SPLIT)).astype(np.uint8) * 255
    white_mask = (alpha & (luminance >= BLACK_WHITE_LUMINANCE_SPLIT)).astype(np.uint8) * 255

    resample = Image.Resampling.BOX
    black = np.asarray(Image.fromarray(black_mask, "L").resize(target_size, resample))
    white = np.asarray(Image.fromarray(white_mask, "L").resize(target_size, resample))

    black_pixels = (black >= coverage_threshold) & (black >= white)
    white_pixels = (white >= coverage_threshold) & (white > black)
    output = np.zeros((target_size[1], target_size[0], 4), dtype=np.uint8)
    output[white_pixels] = WHITE_RGBA
    output[black_pixels] = BLACK_RGBA
    return Image.fromarray(output, "RGBA")


def clear_generated_icons(output_dir: Path) -> None:
    if not output_dir.exists():
        return
    for filename in ICON_FILENAMES:
        for path in output_dir.glob(f"*/{filename}"):
            path.unlink()


def generate_icons(source_dir: Path, output_dir: Path, coverage_threshold: int) -> list[Path]:
    written: list[Path] = []
    clear_generated_icons(output_dir)
    for filename in ICON_FILENAMES:
        source_path = source_dir / filename
        if not source_path.exists():
            raise FileNotFoundError(f"missing source icon: {source_path}")

        sizes = LOGO_ICON_SIZES if filename == "logo-system6.png" else TOOLBAR_ICON_SIZES
        with Image.open(source_path) as source:
            for extent in sizes:
                target_dir = output_dir / str(extent)
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / filename
                rasterize_icon(source, extent, coverage_threshold).save(target_path)
                written.append(target_path)

    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Directory containing editable 512px source PNGs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated runtime icon rasters.",
    )
    parser.add_argument(
        "--coverage-threshold",
        type=int,
        default=DEFAULT_COVERAGE_THRESHOLD,
        choices=range(0, 256),
        metavar="[0-255]",
        help="Minimum mask coverage required to emit an opaque pixel.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = generate_icons(args.source_dir, args.output_dir, args.coverage_threshold)
    for path in written:
        print(path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
