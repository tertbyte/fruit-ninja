"""Procedurally-generated fruit and bomb art.

Everything is drawn once with Pillow and cached as PNGs under assets/
so later runs start instantly and the game needs no downloaded or
licensed art. The game itself is played over the live webcam feed, so
this module only supplies the fruit/bomb sprites, not a background.
Sprites are stored/returned as BGRA NumPy arrays so they drop straight
into OpenCV's BGR frames via `overlay`.
"""

import os
import random

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(_HERE, "assets")

SPRITE_SIZE = 160  # px diameter of the canvas each fruit/bomb is drawn on
FRUIT_KINDS = ("watermelon", "orange", "apple", "plum")

_SPECS = {
    "watermelon": dict(rind=(30, 110, 45), rind_dark=(12, 70, 28),
                        flesh=(214, 47, 63), fleck=(35, 20, 20), stripes=True),
    "orange":     dict(rind=(235, 140, 20), rind_dark=(190, 100, 8),
                        flesh=(255, 178, 64), fleck=None, dimples=True),
    "apple":      dict(rind=(199, 30, 42), rind_dark=(132, 10, 20),
                        flesh=(247, 233, 195), fleck=(133, 82, 40), stem=True),
    "plum":       dict(rind=(112, 45, 132), rind_dark=(68, 20, 86),
                        flesh=(228, 191, 212), fleck=(95, 45, 35)),
}


def _ensure_dir() -> None:
    os.makedirs(ASSET_DIR, exist_ok=True)


def _clip_to_circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def _sphere(size: int, base: tuple, dark: tuple) -> Image.Image:
    """A shaded circle: flat base color plus a soft dark crescent and a highlight."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, size - 1, size - 1), fill=base + (255,))
    circle_mask = _clip_to_circle_mask(size)

    shade = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shade).ellipse(
        (size * 0.16, size * 0.16, size * 1.05, size * 1.05), fill=dark + (255,))
    shade = shade.filter(ImageFilter.GaussianBlur(size * 0.10))
    shade.putalpha(ImageChops.multiply(shade.split()[3], circle_mask))
    img = Image.alpha_composite(img, shade)

    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(highlight).ellipse(
        (size * 0.18, size * 0.14, size * 0.55, size * 0.48), fill=(255, 255, 255, 130))
    highlight = highlight.filter(ImageFilter.GaussianBlur(size * 0.05))
    highlight.putalpha(ImageChops.multiply(highlight.split()[3], circle_mask))
    img = Image.alpha_composite(img, highlight)
    return img


def _flesh_disc(size: int, flesh: tuple, fleck) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((0, 0, size - 1, size - 1), fill=flesh + (255,))
    if fleck is not None:
        rng = random.Random(hash(flesh) & 0xFFFF)
        draw = ImageDraw.Draw(img)
        cx = cy = size / 2
        r = size / 2
        for _ in range(10):
            ang = rng.uniform(0, 6.28318)
            dist = rng.uniform(0.15, 0.72) * r
            px, py = cx + dist * np.cos(ang), cy + dist * np.sin(ang)
            s = rng.uniform(2.5, 5.0)
            draw.ellipse((px - s, py - s * 1.5, px + s, py + s * 1.5), fill=fleck + (255,))
    return img


def _make_whole(spec: dict) -> Image.Image:
    size = SPRITE_SIZE
    img = _sphere(size, spec["rind"], spec["rind_dark"])
    circle_mask = _clip_to_circle_mask(size)

    if spec.get("stripes"):
        stripe_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stripe_layer)
        for i in range(-2, 3):
            offset = i * size * 0.22
            sd.line((size * 0.5 + offset - size * 0.6, 0,
                     size * 0.5 + offset + size * 0.6, size),
                    fill=spec["rind_dark"] + (200,), width=int(size * 0.07))
        stripe_layer.putalpha(ImageChops.multiply(stripe_layer.split()[3], circle_mask))
        img = Image.alpha_composite(img, stripe_layer)

    if spec.get("dimples"):
        rng = random.Random(3)
        dimple_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dimple_layer)
        for _ in range(26):
            px, py = rng.uniform(size * 0.15, size * 0.85), rng.uniform(size * 0.15, size * 0.85)
            r = rng.uniform(1.2, 2.4)
            dd.ellipse((px - r, py - r, px + r, py + r), fill=spec["rind_dark"] + (110,))
        dimple_layer.putalpha(ImageChops.multiply(dimple_layer.split()[3], circle_mask))
        img = Image.alpha_composite(img, dimple_layer)

    if spec.get("stem"):
        stem_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stem_layer)
        sd.line((size * 0.5, size * 0.06, size * 0.56, size * -0.02),
                 fill=(90, 60, 25, 255), width=int(size * 0.045))
        sd.ellipse((size * 0.53, size * -0.08, size * 0.7, size * 0.05), fill=(70, 130, 50, 255))
        img = Image.alpha_composite(img, stem_layer)

    return img


def _make_halves(spec: dict) -> tuple:
    size = SPRITE_SIZE
    flesh = _flesh_disc(size, spec["flesh"], spec["fleck"])

    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, size - 1, size - 1), fill=spec["rind"] + (255,))
    inner_hole = Image.new("L", (size, size), 255)
    pad = size * 0.16
    ImageDraw.Draw(inner_hole).ellipse((pad, pad, size - pad, size - pad), fill=0)
    ring.putalpha(ImageChops.multiply(ring.split()[3], inner_hole))

    face = Image.alpha_composite(flesh, ring)

    cut_line = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(cut_line).line(
        (size / 2, size * 0.08, size / 2, size * 0.92), fill=(255, 255, 255, 160),
        width=max(1, int(size * 0.015)))
    face = Image.alpha_composite(face, cut_line)

    left_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(left_mask).pieslice((0, 0, size - 1, size - 1), 90, 270, fill=255)
    right_mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(right_mask).pieslice((0, 0, size - 1, size - 1), 270, 450, fill=255)

    left = face.copy()
    left.putalpha(ImageChops.multiply(left.split()[3], left_mask))
    right = face.copy()
    right.putalpha(ImageChops.multiply(right.split()[3], right_mask))
    return left, right


def _make_bomb() -> Image.Image:
    size = SPRITE_SIZE
    img = _sphere(size, (25, 25, 28), (0, 0, 0))
    circle_mask = _clip_to_circle_mask(size)

    fuse = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fuse)
    fd.line((size * 0.52, size * 0.06, size * 0.62, size * -0.04, size * 0.58, size * -0.14),
            fill=(120, 80, 40, 255), width=int(size * 0.035), joint="curve")
    img = Image.alpha_composite(img, fuse)

    spark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spark)
    sd.ellipse((size * 0.52, size * -0.20, size * 0.68, size * -0.04), fill=(255, 200, 60, 255))
    spark = spark.filter(ImageFilter.GaussianBlur(size * 0.01))
    img = Image.alpha_composite(img, spark)
    return img


def _pil_rgba_to_bgra(img: Image.Image) -> np.ndarray:
    arr = np.array(img.convert("RGBA"))
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    return np.dstack([b, g, r, a])


def load_or_generate():
    """Load cached PNGs from assets/, generating any that are missing.

    Returns (fruit_sprites, bomb_sprite) where fruit_sprites maps
    kind -> {"whole", "left", "right"} BGRA arrays.
    """
    _ensure_dir()

    fruit_sprites = {}
    for kind in FRUIT_KINDS:
        paths = {part: os.path.join(ASSET_DIR, f"{kind}_{part}.png")
                 for part in ("whole", "left", "right")}
        if not all(os.path.exists(p) for p in paths.values()):
            spec = _SPECS[kind]
            whole = _make_whole(spec)
            left, right = _make_halves(spec)
            whole.save(paths["whole"])
            left.save(paths["left"])
            right.save(paths["right"])
        fruit_sprites[kind] = {
            part: _pil_rgba_to_bgra(Image.open(path)) for part, path in paths.items()
        }

    bomb_path = os.path.join(ASSET_DIR, "bomb.png")
    if not os.path.exists(bomb_path):
        _make_bomb().save(bomb_path)
    bomb_sprite = _pil_rgba_to_bgra(Image.open(bomb_path))

    return fruit_sprites, bomb_sprite


def overlay(frame: np.ndarray, sprite: np.ndarray, cx: float, cy: float,
            angle: float = 0.0, scale: float = 1.0) -> None:
    """Alpha-blend a BGRA sprite onto `frame` centered at (cx, cy), in place."""
    h, w = sprite.shape[:2]
    if scale != 1.0:
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        sprite = cv2.resize(sprite, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        h, w = new_h, new_w
    if angle != 0.0:
        m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        sprite = cv2.warpAffine(sprite, m, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    x1, y1 = x0 + w, y0 + h
    fh, fw = frame.shape[:2]

    sx0, sy0 = max(0, -x0), max(0, -y0)
    sx1, sy1 = w - max(0, x1 - fw), h - max(0, y1 - fh)
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(fw, x1), min(fh, y1)
    if x1c <= x0c or y1c <= y0c or sx1 <= sx0 or sy1 <= sy0:
        return

    region = frame[y0c:y1c, x0c:x1c].astype(np.float32)
    patch = sprite[sy0:sy1, sx0:sx1]
    alpha = patch[:, :, 3:4].astype(np.float32) / 255.0
    blended = region * (1 - alpha) + patch[:, :, :3].astype(np.float32) * alpha
    frame[y0c:y1c, x0c:x1c] = blended.astype(np.uint8)
