"""Remove the OpenArt free-plan logo (white, semi-transparent) using a template taken from another sheet.
O = (1-a)*I + a*255 under the logo  =>  I = (O - a*255) / (1-a)."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
tm = np.asarray(Image.open("openart/tmpl_M.png")).astype(float) / 255
x0, x1, y0, y1, MW, MH = np.load("openart/tmpl_info.npy")
# template image tmpl_M.png is the region crop starting at (0.15W, 0.38H) of the mineral sheet
ox, oy = int(MW * 0.15), int(MH * 0.38)
im = np.asarray(Image.open(src).convert("RGB")).astype(float)
H, W = im.shape[:2]
gray = im.mean(2)

def place(scale, dx, dy):
    t = Image.fromarray((tm * 255).astype("uint8"))
    t = t.resize((int(t.width * scale), int(t.height * scale)), Image.BILINEAR)
    t = np.asarray(t).astype(float) / 255
    # template centre in M coordinates -> centre in this image
    cxM, cyM = (x0 + x1) / 2 - ox, (y0 + y1) / 2 - oy
    cx, cy = W / 2 + dx, H * ((y0 + y1) / 2 / MH) + dy
    left, top = int(round(cx - cxM * scale)), int(round(cy - cyM * scale))
    m = np.zeros((H, W))
    hh, ww = t.shape
    m[max(top, 0):top + hh, max(left, 0):left + ww] = t[max(-top, 0):H - top, max(-left, 0):W - left]
    return m

# lift toward white relative to a local base (min filter keeps dark base colours)
base = ndimage.median_filter(gray, size=61)
lift = (gray - base) / np.maximum(255 - base, 10)
best = None
s0 = W / MW
for scale in np.linspace(s0 * 0.985, s0 * 1.015, 7):
    for dx in range(-8, 9, 2):
        for dy in range(-8, 9, 2):
            m = place(scale, dx, dy)
            sc = (lift * (m - 0.5)).sum()
            if best is None or sc > best[0]:
                best = (sc, scale, dx, dy)
_, scale, dx, dy = best
m = place(scale, dx, dy)
m = ndimage.gaussian_filter(m, 0.8)
# estimate alpha: base colour under the logo from the nearest pixels just outside it
outside = m < 0.05
idx = ndimage.distance_transform_edt(~outside, return_distances=False, return_indices=True)
near = im[tuple(idx)]
core = ndimage.binary_erosion(m > 0.9, iterations=3)
nearg = near.mean(2)
sel = core & (nearg < 200) & (nearg > 20)
a_est = ((gray - nearg) / (255 - nearg))[sel]
alpha = float(np.median(a_est))
a = (alpha * m)[..., None]
rec = np.clip((im - a * 255) / (1 - a + 1e-6), 0, 255)
# the template edge is never perfect: smooth a thin band along the logo outline
hard = m > 0.5
edge = ndimage.binary_dilation(hard, iterations=4) & ~ndimage.binary_erosion(hard, iterations=4)
med = np.stack([ndimage.median_filter(rec[..., c], size=9) for c in range(3)], -1)
rec[edge] = med[edge]
Image.fromarray(rec.astype("uint8")).save(out)
print("scale", round(scale, 4), "shift", dx, dy, "alpha", round(alpha, 3), "samples", int(sel.sum()))
