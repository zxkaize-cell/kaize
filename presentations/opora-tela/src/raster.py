"""Typography and labelled shapes rendered to PNG, so the deck looks the same in every viewer
without embedding fonts (PowerPoint, Keynote, Google Slides, phone previews)."""
import hashlib
import os
import re

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "img", "text")
os.makedirs(CACHE, exist_ok=True)
DPI = 220

FILES = {
    ("Unbounded", False): "~/.fonts/Unbounded-Regular.ttf",
    ("Unbounded", True): "~/.fonts/Unbounded-Regular.ttf",
    ("Caveat", False): "~/.fonts/Caveat-Regular.ttf",
    ("Caveat", True): "~/.fonts/Caveat-Regular.ttf",
    ("Nunito", False): "~/.fonts/Nunito-Regular.ttf",
    ("Nunito", True): "~/.fonts/Nunito-Bold.ttf",
    ("Arial", False): "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ("Arial", True): "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
}
_fonts = {}


def font(face, bold, px):
    key = (face, bold, px)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(os.path.expanduser(FILES[(face, bold)]), px)
    return _fonts[key]


def rgba(hexstr, alpha=255):
    h = hexstr.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def _layout(paras, width_px, default, dpi):
    """Greedy word wrap. Returns lines: (pieces, width, ascent, descent, line_height)."""
    lines = []
    for runs in paras:
        tokens = []
        for t, o in runs:
            st = dict(default)
            st.update(o)
            for piece in re.split(r"(\s+)", t):
                if piece:
                    tokens.append((piece, st))
        cur, cur_w = [], 0.0

        def flush():
            while cur and cur[-1][0].isspace():
                cur.pop()
            lines.append(list(cur))

        for piece, st in tokens:
            f = font(st["face"], st["bold"], int(round(st["size"] / 72 * dpi)))
            pw = f.getlength(piece)
            if piece.isspace():
                if cur:
                    cur.append((piece, st, pw))
                    cur_w += pw
                continue
            if cur and cur_w + pw > width_px:
                flush()
                cur, cur_w = [], 0.0
            cur.append((piece, st, pw))
            cur_w += pw
        if not tokens:
            cur = [("", dict(default, **(runs[0][1] if runs else {})), 0.0)]
        flush()
    out = []
    for pieces in lines:
        sizes = [p[1] for p in pieces] or [default]
        asc = max(font(s["face"], s["bold"], int(round(s["size"] / 72 * dpi))).getmetrics()[0] for s in sizes)
        desc = max(font(s["face"], s["bold"], int(round(s["size"] / 72 * dpi))).getmetrics()[1] for s in sizes)
        lh = max(s["size"] / 72 * dpi * 1.2 * s.get("spacing", 1.0) for s in sizes)
        out.append((pieces, sum(p[2] for p in pieces), asc, desc, lh))
    return out


def render(paras, w_in, h_in, default, align="l", anchor="t", pad_in=0.0, extrude=None, shadow=None, dpi=DPI):
    """paras: [[(text, {face,size,color,bold}), ...], ...] → RGBA image of (w+2pad)×(h+2pad) inches."""
    W, H, P = int(round(w_in * dpi)), int(round(h_in * dpi)), int(round(pad_in * dpi))
    lines = _layout(paras, W, default, dpi)
    total = sum(l[4] for l in lines)
    y0 = {"t": 0, "m": (H - total) / 2, "b": H - total}[anchor]
    layer = Image.new("RGBA", (W + 2 * P, H + 2 * P), (0, 0, 0, 0))

    def draw_text(img, dx, dy, color_override=None):
        d = ImageDraw.Draw(img)
        y = y0 + P
        for pieces, lw, asc, desc, lh in lines:
            x = {"l": 0, "c": (W - lw) / 2, "r": W - lw}[align] + P
            base = y + (lh - (asc + desc)) / 2 + asc
            for piece, st, pw in pieces:
                if piece and not piece.isspace():
                    f = font(st["face"], st["bold"], int(round(st["size"] / 72 * dpi)))
                    d.text((x + dx, base + dy), piece, font=f, anchor="ls",
                           fill=color_override or rgba(st["color"], st.get("alpha", 255)))
                x += pw
            y += lh

    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        draw_text(sh, shadow.get("dx", 0) * dpi, shadow.get("dy", 0.03) * dpi, rgba(shadow.get("color", "1C1650"), shadow.get("alpha", 110)))
        layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow.get("blur", 0.03) * dpi)))
    if extrude:
        depth = int(extrude.get("depth", 0.05) * dpi)
        col = rgba(extrude.get("color", "140F3C"))
        for k in range(depth, 0, -1):
            draw_text(layer, k * 0.7, k, col)
    draw_text(layer, 0, 0)
    return layer


def save(img, key_parts):
    h = hashlib.sha1(repr(key_parts).encode()).hexdigest()[:16]
    path = os.path.join(CACHE, h + ".png")
    if not os.path.exists(path):
        img.save(path, optimize=True)
    return path


def rounded_rect(w_px, h_px, radius_px, fill, line=None, line_px=0, gloss=True, ss=3):
    """Anti-aliased rounded rectangle with a soft 'puffy' top light."""
    big = Image.new("RGBA", (w_px * ss, h_px * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    r = int(radius_px * ss)
    if line:
        d.rounded_rectangle([0, 0, w_px * ss - 1, h_px * ss - 1], radius=r, fill=line)
        inset = int(line_px * ss)
        d.rounded_rectangle([inset, inset, w_px * ss - 1 - inset, h_px * ss - 1 - inset], radius=max(0, r - inset), fill=fill)
    else:
        d.rounded_rectangle([0, 0, w_px * ss - 1, h_px * ss - 1], radius=r, fill=fill)
    img = big.resize((w_px, h_px), Image.LANCZOS)
    if gloss and fill[3] == 255:
        # light from the top, a touch of depth at the bottom
        hl = Image.new("L", (w_px, h_px), 0)
        hd = ImageDraw.Draw(hl)
        for i in range(h_px):
            t = i / max(1, h_px - 1)
            v = int(46 * max(0, 1 - t * 2.2)) if t < 0.45 else 0
            hd.line([(0, i), (w_px, i)], fill=v)
        white = Image.new("RGBA", (w_px, h_px), (255, 255, 255, 255))
        white.putalpha(Image.composite(hl, Image.new("L", (w_px, h_px), 0), img.getchannel("A")))
        img.alpha_composite(white)
        dk = Image.new("L", (w_px, h_px), 0)
        dd = ImageDraw.Draw(dk)
        for i in range(h_px):
            t = i / max(1, h_px - 1)
            v = int(40 * max(0, (t - 0.72) / 0.28)) if t > 0.72 else 0
            dd.line([(0, i), (w_px, i)], fill=v)
        black = Image.new("RGBA", (w_px, h_px), (20, 12, 60, 255))
        black.putalpha(Image.composite(dk, Image.new("L", (w_px, h_px), 0), img.getchannel("A")))
        img.alpha_composite(black)
    return img


def box_image(w_in, h_in, fill, radius_in, paras=None, default=None, align="c", anchor="m", margins=(0.12, 0.06),
              alpha=255, line=None, line_in=0.0, shadow=True, gloss=True, oval=False, dpi=DPI):
    """A labelled shape as one picture (with room for its shadow). Returns (image, pad_in)."""
    pad = 0.16 if shadow else 0.0
    W, H, P = int(round(w_in * dpi)), int(round(h_in * dpi)), int(round(pad * dpi))
    canvas = Image.new("RGBA", (W + 2 * P, H + 2 * P), (0, 0, 0, 0))
    radius = min(W, H) / 2 if oval else radius_in * dpi
    shape = rounded_rect(W, H, radius, rgba(fill, alpha), rgba(line) if line else None, line_in * dpi, gloss=gloss)
    if shadow:
        sm = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        mask = shape.getchannel("A").point(lambda v: int(v * 0.22))
        tint = Image.new("RGBA", shape.size, (43, 34, 110, 255))
        tint.putalpha(mask)
        sm.alpha_composite(tint, (P, P + int(0.05 * dpi)))
        canvas.alpha_composite(sm.filter(ImageFilter.GaussianBlur(0.07 * dpi)))
    canvas.alpha_composite(shape, (P, P))
    if paras:
        txt = render(paras, w_in - 2 * margins[0], h_in - 2 * margins[1], default, align, anchor, dpi=dpi)
        canvas.alpha_composite(txt, (P + int(round(margins[0] * dpi)), P + int(round(margins[1] * dpi))))
    return canvas, pad
