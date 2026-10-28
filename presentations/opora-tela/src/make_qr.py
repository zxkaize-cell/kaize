import sys, qrcode
from PIL import Image, ImageDraw


def styled_qr(data, path, color=(46, 42, 107), eye=(59, 47, 143), size=900):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    q.add_data(data)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    cell = size // n
    img = Image.new("RGB", (cell * n, cell * n), "white")
    d = ImageDraw.Draw(img)
    finder = lambda r, c: (r < 9 and c < 9) or (r < 9 and c >= n - 9) or (r >= n - 9 and c < 9)
    for r in range(n):
        for c in range(n):
            if m[r][c] and not finder(r, c):
                x, y = c * cell, r * cell
                p = 0
                d.rounded_rectangle([x + p, y + p, x + cell - p, y + cell - p], radius=cell * 0.18, fill=color)
    for (r0, c0) in [(2, 2), (2, n - 9), (n - 9, 2)]:
        x, y = c0 * cell, r0 * cell
        d.rounded_rectangle([x, y, x + 7 * cell, y + 7 * cell], radius=cell * 0.6, fill=color)
        d.rounded_rectangle([x + cell, y + cell, x + 6 * cell, y + 6 * cell], radius=cell * 0.4, fill="white")
        d.rounded_rectangle([x + 2 * cell, y + 2 * cell, x + 5 * cell, y + 5 * cell], radius=cell * 0.4, fill=eye)
    img.save(path)


styled_qr(sys.argv[1], sys.argv[2])
