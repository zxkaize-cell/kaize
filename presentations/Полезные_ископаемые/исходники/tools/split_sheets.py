"""Split OpenART sheets into single images.
characters/minerals: background removed on the whole sheet, figures grouped by grid cell of their centroid.
scenes: panels separated by the white gaps, then trimmed."""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
os.environ.setdefault("U2NET_HOME", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CUT = os.path.join(ROOT, "img", "cut"); RAW = os.path.join(ROOT, "img", "raw")
os.makedirs(CUT, exist_ok=True); os.makedirs(RAW, exist_ok=True)

def figures(sheet, cols, rows, codes, aspect, bottom):
    from rembg import remove, new_session
    s = new_session("isnet-general-use")
    im = Image.open(sheet).convert("RGB")
    cut = np.array(remove(im, session=s, post_process_mask=True))
    a = cut[..., 3]
    lab, n = ndimage.label(a > 100)
    W, H = im.size
    groups = {i: [] for i in range(cols * rows)}
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    coms = ndimage.center_of_mass(a > 100, lab, range(1, n + 1))
    for k in range(n):
        if sizes[k] < 600:
            continue
        cy, cx = coms[k]
        cell = min(int(cy / (H / rows)), rows - 1) * cols + min(int(cx / (W / cols)), cols - 1)
        groups[cell].append(k + 1)
    for cell, code in enumerate(codes):
        if not code:
            continue
        mask = np.isin(lab, groups[cell])
        # keep soft edges: dilate the label mask a little and use original alpha inside it
        mask = ndimage.binary_dilation(mask, iterations=3)
        rgba = cut.copy(); rgba[..., 3] = np.where(mask, a, 0)
        img = Image.fromarray(rgba)
        bb = img.getbbox(); img = img.crop(bb)
        w, h = img.size
        pad = 0.04
        if aspect:
            CW = max(w, int(h * aspect)); CH = max(h, int(w / aspect))
        else:
            CW, CH = w, h
        CW, CH = int(CW * (1 + 2 * pad)), int(CH * (1 + 2 * pad))
        canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        y = CH - h - int(CH * pad * 0.5) if bottom else (CH - h) // 2
        canvas.paste(img, ((CW - w) // 2, y), img)
        canvas.save(os.path.join(CUT, code + ".png"), optimize=True)
        print("figure", code, canvas.size, "parts", len(groups[cell]))

def panels(sheet, codes):
    im = Image.open(sheet).convert("RGB"); a = np.asarray(im).astype(int)
    white = (a.min(axis=2) > 235)
    H, W = white.shape
    def gap(profile, n, lo, hi):
        idx = np.arange(int(n * lo), int(n * hi))
        best = idx[np.argmax(profile[idx])]
        # widen to the run of near-white lines
        l = best
        while l > 0 and profile[l - 1] > 0.9: l -= 1
        r = best
        while r < n - 1 and profile[r + 1] > 0.9: r += 1
        return l, r
    cl, cr = gap(white.mean(axis=0), W, 0.4, 0.6)
    rl, rr = gap(white.mean(axis=1), H, 0.4, 0.6)
    boxes = [(0, 0, cl, rl), (cr + 1, 0, W, rl), (0, rr + 1, cl, H), (cr + 1, rr + 1, W, H)]
    for box, code in zip(boxes, codes):
        p = im.crop(box); pa = np.asarray(p).astype(int); nw = pa.min(axis=2) <= 235
        ys, xs = np.where(nw); p = p.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        # shave a few pixels of anti-aliased border
        p = p.crop((4, 4, p.width - 4, p.height - 4))
        p.save(os.path.join(RAW, code + ".png"), optimize=True)
        print("panel", code, p.size, "gaps", (cl, cr), (rl, rr))

if __name__ == "__main__":
    kind, sheet = sys.argv[1], sys.argv[2]
    codes = sys.argv[3].split(",")
    if kind == "chars":
        figures(sheet, 2, 2, codes, 2 / 3, True)
    elif kind == "minerals":
        figures(sheet, 4, 2, codes, 1.0, False)
    else:
        panels(sheet, codes)
