"""
Convert a photo (or a text monogram) into ASCII art for the profile card.

Usage:
    python ascii_art.py photo.jpg            # your headshot -> ascii.txt
    python ascii_art.py --text HZ            # monogram placeholder -> ascii.txt
Options:
    --cols 42      width in characters (default 42; keep 38-44 to fit the card)
    --invert       flip light/dark (try it if your face comes out as a negative)
Tip: a tightly cropped, well-lit headshot on a plain background works best.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

# dark -> light (on a dark card, dense characters = bright pixels)
RAMP = " .'`^,:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
CHAR_ASPECT = 0.51
  # monospace glyphs are ~2x taller than wide
CROP = 1.0   # keep the top fraction of the photo (head & shoulders)
ZOOM = 1.0   # keep the centre fraction of the width


def image_to_ascii(img: Image.Image, cols: int, invert: bool) -> str:
    alpha = None
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        img = img.convert("RGBA")
        bbox = img.getchannel("A").getbbox()  # trim empty transparent margins
        if bbox:
            img = img.crop(bbox)
        alpha = True
    if CROP < 1 or ZOOM < 1:
        m = int(img.width * (1 - ZOOM) / 2)
        img = img.crop((m, 0, img.width - m, int(img.height * CROP)))
    if alpha:
        alpha = img.getchannel("A")
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img, cutoff=1, mask=alpha if alpha else None)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    if invert:
        img = ImageOps.invert(img)
    w, h = img.size
    rows = max(1, int(h / w * cols * CHAR_ASPECT))
    img = img.resize((cols, rows), Image.LANCZOS)
    px = img.load()
    ap = alpha.resize((cols, rows), Image.LANCZOS).load() if alpha else None
    n = len(RAMP) - 1
    lines = []
    for y in range(rows):
        lines.append("".join(" " if ap and ap[x, y] < 100 else RAMP[max(1, int(px[x, y] / 255 * n))]
                             for x in range(cols)).rstrip())
    return "\n".join(lines)


def monogram(text: str) -> Image.Image:
    size = 900
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    # outer ring + inner ring
    d.ellipse((30, 30, size - 30, size - 30), outline=200, width=34)
    d.ellipse((95, 95, size - 95, size - 95), outline=90, width=10)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 380)
    except OSError:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]), text, fill=255, font=font)
    # small "circuit" ticks around the ring
    for i in range(0, 360, 30):
        import math
        a = math.radians(i)
        r1, r2 = size / 2 - 30, size / 2 - 2
        cx = cy = size / 2
        d.line((cx + r1 * math.cos(a), cy + r1 * math.sin(a),
                cx + r2 * math.cos(a), cy + r2 * math.sin(a)), fill=160, width=14)
    return img


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("photo", nargs="?")
    p.add_argument("--text")
    p.add_argument("--cols", type=int, default=64)
    p.add_argument("--invert", action="store_true")
    p.add_argument("--out", default="ascii.txt")
    p.add_argument("--crop", type=float, default=0.66, help="keep top fraction of photo")
    p.add_argument("--zoom", type=float, default=0.7, help="keep centre fraction of width")
    a = p.parse_args()
    CROP, ZOOM = a.crop, a.zoom
    if a.text:
        art = image_to_ascii(monogram(a.text), a.cols, a.invert)
    elif a.photo:
        art = image_to_ascii(Image.open(a.photo), a.cols, a.invert)
    else:
        p.error("give a photo path or --text")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(art + "\n")
    print(art)
