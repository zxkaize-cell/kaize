"""Builds «Опора тела и движение» — interactive lesson deck (python-pptx + hand-written timing XML)."""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt
from pptx.enum.text import PP_ALIGN

import kit
from kit import (C, E, FONT, FONT_BLACK, ASSETS, IMG, box, emoji, picture, text, shape_text, shadow, bevel,
                 transparent_fill, set_name, set_descr, link_slide, link_url, notes, text_3d, text_shadow, rgb,
                 text_width_in, fill_alpha, glow)
from pptx_fx import Timeline, Fx, set_transition

OUT = sys.argv[1] if len(sys.argv) > 1 else "deck.pptx"
GAME_URL = os.environ.get("GAME_URL", "https://kostik-skeleton.lovable.app")
VIDEO_URL = "https://youtu.be/6C_RWeZtCNg?si=fnJgUxPPG3wl2pDA"
SW, SH = 13.333, 7.5
SOUNDS = {k: os.path.join(ASSETS, k + ".wav") for k in ("correct", "wrong", "win", "flip", "pop")}
PLACEHOLDERS = []

ASPECT = {"jelly": 16 / 9, "tent": 16 / 9, "museum": 16 / 9, "skeleton": 3 / 4, "mannequin": 1, "arm": 4 / 3,
          "posture_good": 1, "posture_bad": 1, "records": 1, "food": 4 / 3, "sport": 16 / 9, "cinema": 16 / 9}


def img(key):
    for ext in (".png", ".jpg"):
        p = os.path.join(IMG, key + ext)
        if os.path.exists(p):
            return p
    PLACEHOLDERS.append(key)
    os.makedirs(os.path.join(IMG, "ph"), exist_ok=True)
    p = os.path.join(IMG, "ph", key + ".png")
    if key.startswith("mascot"):
        im = Image.new("RGBA", (720, 1000), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([160, 20, 560, 420], fill=(255, 248, 236, 255), outline=(255, 159, 67, 255), width=14)
        d.rounded_rectangle([250, 400, 470, 900], radius=90, fill=(255, 248, 236, 255), outline=(255, 159, 67, 255), width=14)
        d.text((260, 180), key[7:], fill=(43, 42, 90, 255))
    else:
        a = ASPECT.get(key, 1)
        w = 1200
        im = Image.new("RGB", (w, int(w / a)), (214, 228, 255))
        d = ImageDraw.Draw(im)
        d.text((40, 40), "PLACEHOLDER " + key, fill=(43, 42, 90))
    im.save(p)
    return p


prs = Presentation()
prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
LAYOUT_TITLE_ONLY = prs.slide_layouts[5]
N = 31
S = [None] + [prs.slides.add_slide(LAYOUT_TITLE_ONLY) for _ in range(N)]
HOME, HUB, GAMES = 5, 7, 16


# ---------------------------------------------------------------- frame bits
def bg(slide, name):
    p = slide.shapes.add_picture(os.path.join(ASSETS, name), 0, 0, prs.slide_width, prs.slide_height)
    set_name(p, "!!bg")
    set_descr(p, "")
    # keep background at the back of the z-order
    tree = slide.shapes._spTree
    tree.remove(p._element)
    tree.insert(2, p._element)
    return p


def title(slide, txt, color=None, size=34, x=0.6, y=0.86, w=11.2, h=0.8, face=FONT_BLACK, align="l"):
    ph = slide.shapes.title
    ph.left, ph.top, ph.width, ph.height = E(x), E(y), E(w), E(h)
    shape_text(ph, txt, size, color or C["ink"], face, False, align, "t", margins=(0, 0), label="title " + txt[:25])
    set_name(ph, "Title")
    return ph


def kicker(slide, txt, fill, color="FFFFFF", x=0.6, y=0.38, name=None):
    w = text_width_in(txt, 12, FONT, True) + len(txt) * 1.2 / 72 + 0.5
    b = box(slide, x, y, w, 0.38, fill=fill, kind="pill", name=name or "kicker")
    shape_text(b, txt, 12, color, FONT, True, margins=(0.1, 0.02), check=False)
    for r in b._element.iter(qn("a:rPr")):
        r.set("spc", "120")
    return b


def home_btn(slide):
    c = box(slide, 12.33, 0.38, 0.6, 0.6, fill="FFFFFF", kind="oval", name="!!home")
    shadow(c, blur=0.12, dist=0.04, alpha=20)
    i = emoji(slide, "home", 12.44, 0.49, 0.38, name="!!home icon")
    for s in (c, i):
        link_slide(s, S[HOME])
    return c


def museum_btn(slide):
    b = box(slide, 10.45, 0.38, 1.75, 0.6, fill="FFFFFF", kind="pill", name="!!museum")
    shadow(b, blur=0.12, dist=0.04, alpha=20)
    i = emoji(slide, "museum", 10.6, 0.48, 0.4, name="!!museum icon")
    t = text(slide, 11.08, 0.38, 1.05, 0.6, "В музей", 15, C["ink"], FONT, True, anchor="m", name="!!museum label")
    for s in (b, i, t):
        link_slide(s, S[HUB])


def next_btn(slide, label, target, x=None, y=6.62, fill=None, name="!!next", w=None):
    fill = fill or C["sun"]
    w = w or (text_width_in(label, 16, FONT_BLACK) + 1.05)
    x = x if x is not None else 12.73 - w
    b = box(slide, x, y, w, 0.58, fill=fill, kind="pill", name=name)
    bevel(b, w=0.06, h=0.025)
    shadow(b, blur=0.12, dist=0.05, alpha=25)
    t = text(slide, x + 0.25, y, w - 0.8, 0.58, label, 16, C["ink"], FONT_BLACK, anchor="m", name=name + " label")
    i = emoji(slide, "next", x + w - 0.55, y + 0.11, 0.36, name=name + " icon")
    for s in (b, t, i):
        link_slide(s, S[target])
    return [b, t, i]


def hit(slide, x, y, w, h, name, target=None, url=None):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, E(x), E(y), E(w), E(h))
    st = r._element.find(qn("p:style"))
    if st is not None:
        r._element.remove(st)
    transparent_fill(r)
    set_name(r, name)
    if target:
        link_slide(r, S[target])
    if url:
        link_url(r, url)
    return r


def mascot(slide, key, cx, bottom, h, name=None):
    p = img(key)
    w_px, h_px = Image.open(p).size
    w = h * w_px / h_px
    pic = picture(slide, p, cx - w / 2, bottom - h, h=h, name=name or key, descr="Костик — весёлый скелетик-экскурсовод")
    return pic


def icon_circle(slide, key, x, y, d, fill, icon_scale=0.62, name=None):
    c = box(slide, x, y, d, d, fill=fill, kind="oval", name=(name or key) + " circle")
    s = d * icon_scale
    i = emoji(slide, key, x + (d - s) / 2, y + (d - s) / 2, s, name=(name or key) + " icon")
    return c, i


def card(slide, x, y, w, h, fill="FFFFFF", name="card", radius=0.22, sh=True):
    b = box(slide, x, y, w, h, fill=fill, radius=radius, name=name)
    if sh:
        shadow(b, blur=0.22, dist=0.06, alpha=16)
    return b


def remove_style(shape):
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


# make every autoshape style-free (no theme shadows / fonts)
_orig_box = kit.box


def _box(*a, **k):
    s = _orig_box(*a, **k)
    remove_style(s)
    return s


kit.box = _box
box = _box


def fx(shape, kind, dur=500, delay=0, sound=None, **kw):
    return Fx(shape, kind, dur, delay, sound, **kw)


def timeline(slide):
    return Timeline(slide, SOUNDS)


# ================================================================ SLIDE 1
s = S[1]
bg(s, "bg_dark.jpg")
g1 = box(s, 8.05, 0.95, 5.0, 5.0, fill=None, kind="oval", name="glow ring")
fill_alpha(g1, "FFFFFF", 9)
g2 = box(s, 8.6, 1.5, 3.9, 3.9, fill=None, kind="oval", name="glow core")
fill_alpha(g2, "FFFFFF", 11)
k = kicker(s, "ОКРУЖАЮЩИЙ МИР · 3 КЛАСС", C["sun"], C["ink"], x=0.75, y=1.15)
ttl = title(s, "", x=0.75, y=1.7, w=7.4, h=2.5)
tf = ttl.text_frame
for i, (line, col) in enumerate([("Опора тела", "FFFFFF"), ("и движение", C["sun"])]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.line_spacing = 0.95
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = line
    kit._style_run(r, 68, col, FONT_BLACK, False)
kit.check_fit("title slide", "Опора тела", 68, 7.4, 1.2, FONT_BLACK)
text_3d(ttl, extrusion_color="1A1450", depth=0.07)
sub = text(s, 0.75, 4.3, 7.0, 0.9, "Путешествие в музей «Тело человека» вместе с Костиком",
           22, "E4DEFF", FONT, True, name="subtitle")
auth = box(s, 0.75, 5.5, 5.3, 1.05, fill=None, kind="round", radius=0.3, name="author card")
fill_alpha(auth, "FFFFFF", 13)
auth.line.color.rgb = rgb("FFFFFF")
auth.line.width = E(0.015)
ac, ai = icon_circle(s, "pencil", 0.95, 5.67, 0.72, C["sun"], name="author")
at = text(s, 1.85, 5.6, 4.1, 0.85, [[("Автор: Шелешко А.И.", {"size": 20, "bold": True, "color": "FFFFFF"})],
                                    [("Группа П-31", {"size": 16, "color": "D9D2FF"})]],
          name="author text", anchor="m")
m1 = mascot(s, "mascot_wave", 10.55, 6.95, 5.6, name="!!mascot")
e1 = emoji(s, "bone", 7.75, 0.75, 0.75, name="float bone")
e2 = emoji(s, "muscle", 12.25, 5.55, 0.8, name="float muscle")
e3 = emoji(s, "star", 8.0, 5.75, 0.55, name="float star")
e4 = emoji(s, "sparkles", 12.35, 0.7, 0.6, name="float sparkles")
tl = timeline(s)
tl.begin([fx(k, "fade", 500), fx(ttl, "pop", 800, delay=150), fx(g1, "zoom", 900), fx(g2, "zoom", 900, delay=150),
          fx(m1, "bounce", 1200, delay=300)])
tl.then([fx(sub, "float_up", 600), fx(e1, "spin_in", 700, delay=100), fx(e4, "spin_in", 700, delay=250)])
tl.then([fx(auth, "float_up", 500), fx(ac, "float_up", 500), fx(ai, "float_up", 500), fx(at, "float_up", 500),
         fx(e2, "spin_in", 700, delay=150), fx(e3, "spin_in", 700, delay=300)])
tl.then([fx(m1, "bob", 1600, dy="-0.02")])
tl.apply()
set_transition(s, "curtains", 2200)
notes(s, "Здравствуйте, ребята! Сегодня у нас необычный урок: мы отправимся в путешествие в музей «Тело человека». "
         "А экскурсоводом будет весёлый скелетик Костик. Посмотрите, как он нам машет! Помашем ему в ответ.\n"
         "Тему урока пока не называем — дети отгадают её сами на следующих слайдах.")

# ================================================================ SLIDE 2 — riddle
s = S[2]
bg(s, "bg_light.jpg")
kicker(s, "РАЗМИНКА ДЛЯ УМА", C["violet"])
title(s, "Отгадайте загадку")
cd = card(s, 0.6, 1.95, 7.7, 4.6, name="riddle card")
q1 = emoji(s, "speech", 1.05, 2.3, 0.7, name="riddle icon")
rid = text(s, 1.05, 3.1, 6.9, 2.2, "Он внутри у нас таится,\nПомогает не свалиться,\nДержит тело, как каркас.\nЧто же это есть у нас?",
           26, C["ink"], FONT, True, spacing=1.12, name="riddle")
ans = box(s, 1.05, 5.45, 3.4, 0.82, fill=C["sun"], kind="pill", name="answer")
shape_text(ans, "СКЕЛЕТ", 30, C["ink"], FONT_BLACK, margins=(0.1, 0.02))
bevel(ans)
shadow(ans, alpha=25)
ab = emoji(s, "bone", 4.65, 5.38, 0.95, name="answer bone")
m2 = mascot(s, "mascot_think", 10.6, 6.95, 5.3, name="!!mascot")
tl = timeline(s)
tl.begin([fx(cd, "float_up", 600), fx(q1, "float_up", 600), fx(rid, "fade", 800, delay=300), fx(m2, "fly_right", 800, delay=200)])
tl.click([fx(ans, "pop", 700, sound="correct"), fx(ab, "spin_in", 800, delay=200)])
tl.apply()
set_transition(s, "gallery", 1600, dir="l")
notes(s, "Костик приготовил для вас загадку. Послушайте внимательно (учитель читает загадку).\n"
         "Ответ детей: скелет. По щелчку появляется ответ «СКЕЛЕТ».\n"
         "— Правильно! Скелет — это каркас нашего тела. А зачем он нам нужен? Сейчас разберёмся.")

# ================================================================ SLIDE 3 — problem question
s = S[3]
bg(s, "bg_light.jpg")
kicker(s, "ПРОБЛЕМНЫЙ ВОПРОС", C["coral"])
title(s, "Почему медуза растекается, а мальчик прыгает?", size=32, w=11.4)
home_btn(s)
pj = picture(s, img("jelly"), 0.6, 1.95, name="jelly", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(7.3, 4.1), descr="Медуза растеклась на песке, а мальчик высоко прыгает")
ca = card(s, 8.2, 1.95, 4.53, 1.95, name="card jelly")
ci1, ii1 = icon_circle(s, "jelly", 8.45, 2.2, 0.85, C["lilac_soft"], name="jelly")
ta = text(s, 9.5, 2.12, 3.05, 1.65, "У медузы нет скелета — на суше её мягкое тело не держит форму", 16, C["ink"], FONT, False,
          anchor="m", name="text jelly")
cb = card(s, 8.2, 4.15, 4.53, 1.9, name="card human")
ci2, ii2 = icon_circle(s, "bone", 8.45, 4.4, 0.85, C["sun_soft"], name="human")
tb = text(s, 9.5, 4.3, 3.05, 1.6, [[("У человека есть ", {}), ("скелет", {"bold": True, "color": C["violet"]}),
                                     (" и ", {}), ("мышцы", {"bold": True, "color": C["coral"]}),
                                     (" — это опора тела и движение!", {})]], 16, name="text human", anchor="m")
kit.check_fit("problem B", "У человека есть скелет и мышцы — это опора тела и движение!", 16, 3.05, 1.6)
tl = timeline(s)
tl.begin([fx(pj, "zoom", 700)])
tl.click([fx(ca, "float_up", 500), fx(ci1, "float_up", 500), fx(ii1, "float_up", 500), fx(ta, "float_up", 500)])
tl.click([fx(cb, "float_up", 500, sound="pop"), fx(ci2, "float_up", 500), fx(ii2, "float_up", 500), fx(tb, "float_up", 500)])
tl.apply()
set_transition(s, "ripple", 1400, dir="center")
notes(s, "Посмотрите на картинку. Медуза в море плавает красиво, а на берегу растекается, как желе. "
         "А мальчик прыгает, бегает и стоит ровно. Почему так?\n"
         "Выслушать версии детей. 1-й щелчок: у медузы нет скелета. 2-й щелчок: у человека есть скелет и мышцы.\n"
         "— Значит, тема нашего урока — «Опора тела и движение».")

# ================================================================ SLIDE 4 — topic, goal, tasks
s = S[4]
bg(s, "bg_light.jpg")
kicker(s, "ТЕМА УРОКА", C["mint"])
title(s, "Опора тела и движение")
home_btn(s)
gc = box(s, 0.6, 1.95, 4.5, 4.75, fill=C["indigo"], radius=0.3, name="goal card")
shadow(gc, alpha=28)
gi = emoji(s, "target", 0.95, 2.3, 1.05, name="goal icon")
gh = text(s, 0.95, 3.5, 3.8, 0.6, "Цель урока", 26, C["sun"], FONT_BLACK, name="goal head")
gt = text(s, 0.95, 4.15, 3.85, 2.3, "Узнать, что помогает нашему телу держать форму и двигаться", 21, "FFFFFF", FONT, True,
          spacing=1.1, name="goal text")
th = text(s, 5.5, 1.95, 7.0, 0.5, "Задачи:", 22, C["ink"], FONT_BLACK, name="tasks head")
tasks = [("Познакомиться со скелетом и его частями", C["sky"]), ("Узнать, как работают суставы и мышцы", C["coral"]),
         ("Выяснить, что такое осанка и как её беречь", C["mint"]), ("Проверить свои знания в играх", C["sun"])]
tl = timeline(s)
tl.begin([fx(gc, "zoom", 700), fx(gi, "spin_in", 800, delay=300), fx(gh, "fade", 500, delay=300), fx(gt, "fade", 600, delay=400),
          fx(th, "fade", 500, delay=500)])
for i, (t, col) in enumerate(tasks):
    y = 2.6 + i * 1.03
    c = card(s, 5.5, y, 7.23, 0.88, name="task %d" % (i + 1))
    n = box(s, 5.68, y + 0.14, 0.6, 0.6, fill=col, kind="oval", name="task num %d" % (i + 1))
    shape_text(n, str(i + 1), 20, C["ink"] if col == C["sun"] else "FFFFFF", FONT_BLACK, margins=(0, 0))
    bevel(n, w=0.05, h=0.02)
    tt = text(s, 6.5, y, 6.05, 0.88, t, 19, C["ink"], FONT, True, anchor="m", name="task text %d" % (i + 1))
    tl.click([fx(c, "fly_right", 500), fx(n, "fly_right", 500), fx(tt, "fly_right", 500)])
tl.apply()
set_transition(s, "prism", 1500, isContent="1")
notes(s, "Тема урока: «Опора тела и движение».\nЦель: узнать, что помогает нашему телу держать форму и двигаться.\n"
         "Задачи появляются по щелчку: 1) познакомиться со скелетом и его частями; 2) узнать, как работают суставы и мышцы; "
         "3) выяснить, что такое осанка и как её беречь; 4) проверить свои знания в играх.\n"
         "Для учителя (цели урока): образовательная — сформировать представление об опорно-двигательной системе человека "
         "(скелет, суставы, мышцы, осанка); развивающая — развивать наблюдательность, умение сравнивать и делать выводы; "
         "воспитательная — воспитывать бережное отношение к своему здоровью.")

# ================================================================ SLIDE 5 — contents (route)
s = S[5]
bg(s, "bg_light.jpg")
kicker(s, "СОДЕРЖАНИЕ", C["violet"])
title(s, "Маршрут нашего урока")
hint = text(s, 0.6, 1.62, 8.0, 0.42, "Нажми на остановку — и мы сразу туда отправимся!", 17, C["muted"], FONT, True, name="route hint")
stations = [("film", "Видео-\nэкскурсия", 6, C["coral"]), ("museum", "Виртуальная экскурсия", 7, C["sky"]),
            ("cartwheel", "Физминутка", 15, C["mint"]), ("puzzle", "Игры «Проверь себя»", 16, C["violet"]),
            ("globe", "Онлайн-\nзадание", 24, C["orange"]), ("trophy", "Итоги урока", 25, C["sun"]),
            ("rainbow", "Рефлексия", 28, C["lilac"])]
xs = [1.55 + i * 1.705 for i in range(7)]
ys = [3.05 if i % 2 == 0 else 4.55 for i in range(7)]
# dashed winding road through the stations (decorative picture)
road = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
pts = [(x * 144, y * 144) for x, y in zip(xs, ys)]
import numpy as np


def catmull(pts, n=40):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, P[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(np.array(pts[-1]))
    return out


SC = 2  # draw at 2x, then downsample for smooth edges
curve = np.array(catmull([(x * SC, y * SC) for x, y in pts], 120))
seg = np.linalg.norm(np.diff(curve, axis=0), axis=1)
dist = np.concatenate([[0], np.cumsum(seg)])
big = Image.new("RGBA", (1920 * SC, 1080 * SC), (0, 0, 0, 0))


def stamp(img, r, fill, offset=(0, 0), d_from=0, d_to=None):
    dd = ImageDraw.Draw(img)
    d_to = dist[-1] if d_to is None else d_to
    for d0 in np.arange(d_from, d_to, 3):
        x, y = np.interp(d0, dist, curve[:, 0]) + offset[0], np.interp(d0, dist, curve[:, 1]) + offset[1]
        dd.ellipse([x - r, y - r, x + r, y + r], fill=fill)


sh = Image.new("RGBA", big.size, (0, 0, 0, 0))
stamp(sh, 27 * SC, (108, 92, 231, 55), offset=(0, 8 * SC))
big.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 * SC)))
stamp(big, 25 * SC, (255, 255, 255, 255))
for d0 in np.arange(18 * SC, dist[-1] - 18 * SC, 46 * SC):
    stamp(big, 5 * SC, (185, 169, 255, 255), d_from=d0, d_to=d0 + 22 * SC)
road = big.resize((1920, 1080), Image.LANCZOS)
road_path = os.path.join(IMG, "road.png")
os.makedirs(IMG, exist_ok=True)
road.save(road_path)
rp = s.shapes.add_picture(road_path, 0, 0, prs.slide_width, prs.slide_height)
set_name(rp, "route road")
set_descr(rp, "")
tl = timeline(s)
tl.begin([fx(rp, "wipe_right", 1200)])
step = []
for i, (key, label, target, col) in enumerate(stations):
    cx, cy = xs[i], ys[i]
    ring = box(s, cx - 0.66, cy - 0.66, 1.32, 1.32, fill="FFFFFF", kind="oval", name="station %d" % (i + 1))
    ring.line.color.rgb = rgb(col)
    ring.line.width = E(0.07)
    bevel(ring, w=0.08, h=0.03)
    shadow(ring, alpha=22)
    ic = emoji(s, key, cx - 0.38, cy - 0.38, 0.76, name="station icon %d" % (i + 1))
    num = box(s, cx + 0.3, cy - 0.72, 0.44, 0.44, fill=col, kind="oval", name="station num %d" % (i + 1))
    shape_text(num, str(i + 1), 15, C["ink"] if col in (C["sun"], C["lilac"]) else "FFFFFF", FONT_BLACK, margins=(0, 0))
    lb = text(s, cx - 0.85, cy + 0.75, 1.7, 0.75, label, 15, C["ink"], FONT_BLACK, align="c", name="station label %d" % (i + 1),
              spacing=0.95, check=False)
    kit.check_fit("station %d" % i, label, 15, 1.7, 0.75, FONT_BLACK, spacing=0.95)
    h = hit(s, cx - 0.85, cy - 0.75, 1.7, 2.3, "station link %d" % (i + 1), target=target)
    d = i * 220
    step += [fx(ring, "pop", 600, delay=d), fx(ic, "pop", 600, delay=d), fx(num, "zoom", 400, delay=d + 250),
             fx(lb, "fade", 400, delay=d + 200)]
tl.then(step)
m5 = mascot(s, "mascot_point", 12.15, 7.2, 2.75, name="!!mascot")
tl.then([fx(m5, "bounce", 900)])
tl.apply()
set_transition(s, "flythrough", 1300)
notes(s, "Это маршрут нашего урока. Каждая остановка — кнопка: нажмите на неё, и презентация перейдёт к этой части урока.\n"
         "На всех следующих слайдах есть кнопка с домиком — она возвращает сюда, к маршруту.\n"
         "1 — Видеоэкскурсия, 2 — Виртуальная экскурсия по музею, 3 — Физминутка, 4 — Игры «Проверь себя», "
         "5 — Онлайн-задание, 6 — Итоги урока, 7 — Рефлексия.")

# ================================================================ SLIDE 6 — video excursion
s = S[6]
bg(s, "bg_dark.jpg")
kicker(s, "ВИДЕОЭКСКУРСИЯ", C["sun"], C["ink"])
title(s, "Смотрим и запоминаем!", color="FFFFFF")
home_btn(s)
cin = picture(s, img("cinema"), 0.6, 1.9, name="cinema", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
              crop_to=(7.55, 4.25), descr="Уютный детский кинозал с большим экраном")
pl = box(s, 0.6 + 7.55 / 2 - 0.7, 1.9 + 4.25 / 2 - 0.95, 1.4, 1.4, fill=C["coral"], kind="oval", name="play circle")
bevel(pl)
glow(pl, "FFFFFF", 0.18, 45)
tri = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, E(0.6 + 7.55 / 2 - 0.22), E(1.9 + 4.25 / 2 - 0.6), E(0.62), E(0.7))
remove_style(tri)
tri.rotation = 90
tri.fill.solid()
tri.fill.fore_color.rgb = rgb("FFFFFF")
tri.line.fill.background()
set_name(tri, "play triangle")
cap = box(s, 2.0, 5.4, 4.75, 0.5, fill=None, kind="pill", name="video caption")
fill_alpha(cap, "1E1856", 70)
shape_text(cap, "Нажми на экран — откроется видео", 15, "FFFFFF", FONT, True, margins=(0.1, 0.02))
hv = hit(s, 0.6, 1.9, 7.55, 4.25, "video link", url=VIDEO_URL)
qc = card(s, 8.5, 1.9, 4.23, 3.0, name="questions card")
qh = text(s, 8.8, 2.1, 3.7, 0.5, "Найди ответы в фильме:", 19, C["ink"], FONT_BLACK, name="questions head")
qs = text(s, 8.8, 2.68, 3.75, 2.1, "1. Что служит опорой тела?\n2. Какие кости защищают мозг, сердце и лёгкие?\n3. Что помогает нам двигаться?",
          16, C["ink"], FONT, True, para_space=6, name="questions")
qr_bg = card(s, 8.5, 5.15, 1.55, 1.55, name="qr card")
qr = picture(s, os.path.join(ASSETS, "qr_video.png"), 8.6, 5.25, w=1.35, h=1.35, name="qr video", descr="QR-код на видеоэкскурсию")
link_url(qr, VIDEO_URL)
qt = text(s, 10.25, 5.2, 2.5, 1.45, "Или отсканируй QR-код телефоном", 15, "FFFFFF", FONT, True, anchor="m", name="qr text")
m6 = mascot(s, "mascot_popcorn", 1.15, 7.3, 2.35, name="!!mascot")
tl = timeline(s)
tl.begin([fx(cin, "zoom", 700), fx(m6, "fly_left", 700, delay=300)])
tl.then([fx(pl, "pop", 600, sound="pop"), fx(tri, "pop", 600), fx(cap, "fade", 400, delay=300)])
tl.then([fx(qc, "float_up", 500), fx(qh, "float_up", 500), fx(qs, "float_up", 500), fx(qr_bg, "float_up", 500, delay=200),
         fx(qr, "float_up", 500, delay=200), fx(qt, "float_up", 500, delay=200)])
tl.then([fx(pl, "pulse", 400, scale=110000)])
tl.apply()
set_transition(s, "warp", 1400, dir="in")
notes(s, "Перед просмотром дайте детям задание: найти в фильме ответы на три вопроса (они на слайде).\n"
         "Видео открывается по нажатию на экран (нужен интернет): " + VIDEO_URL + "\n"
         "После просмотра обсудите ответы: опора тела — скелет; мозг защищает череп, сердце и лёгкие — грудная клетка; "
         "двигаться помогают мышцы и суставы.")

# ================================================================ SLIDE 7 — museum hub
HALLS = [("bone", "Скелет — опора тела", C["sky"], C["sky_soft"], 8),
         ("search", "Из чего состоит скелет", C["violet"], C["lilac_soft"], 9),
         ("gear", "Суставы", C["mint"], C["mint_soft"], 10),
         ("muscle", "Мышцы", C["coral"], C["coral_soft"], 11),
         ("chair", "Осанка", C["orange"], "FFEBD6", 12),
         ("trophy", "Музей рекордов", C["sun"], C["sun_soft"], 14)]
s = S[7]
bg(s, "bg_light.jpg")
kicker(s, "ВИРТУАЛЬНАЯ ЭКСКУРСИЯ", C["sky"])
title(s, "Музей «Тело человека»")
home_btn(s)
mu = picture(s, img("museum"), 0.6, 1.9, name="museum", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(6.35, 3.57), descr="Яркий детский музей о теле человека")
wc = card(s, 0.6, 5.67, 6.35, 1.2, name="welcome card")
wt = text(s, 0.9, 5.67, 4.2, 1.2, "Я Костик — ваш экскурсовод. Выбирайте зал — и вперёд!", 17, C["ink"], FONT, True,
          anchor="m", name="welcome text")
m7 = mascot(s, "mascot_point", 6.0, 7.25, 3.6, name="!!mascot")
tl = timeline(s)
tl.begin([fx(mu, "zoom", 700), fx(wc, "float_up", 500, delay=300), fx(wt, "float_up", 500, delay=300),
          fx(m7, "bounce", 1000, delay=200)])
step = []
for i, (key, name, col, soft, target) in enumerate(HALLS):
    cx = 7.3 + (i % 2) * 2.77
    cy = 1.9 + (i // 2) * 1.67
    t = box(s, cx, cy, 2.62, 1.5, fill=soft, radius=0.25, name="!!hall%d" % (i + 1))
    t.line.color.rgb = rgb(col)
    t.line.width = E(0.03)
    shadow(t, alpha=18)
    ic = emoji(s, key, cx + 0.18, cy + 0.15, 0.55, name="!!hall%d icon" % (i + 1))
    zl = text(s, cx + 0.85, cy + 0.17, 1.6, 0.5, "ЗАЛ %d" % (i + 1), 14, col if col != C["sun"] else "C98A00", FONT_BLACK,
              anchor="m", name="hall%d num" % (i + 1))
    nm = text(s, cx + 0.18, cy + 0.75, 2.3, 0.65, name, 15, C["ink"], FONT_BLACK, spacing=0.95, name="hall%d name" % (i + 1),
              check=False)
    kit.check_fit("hall name", name, 15, 2.3, 0.65, FONT_BLACK, spacing=0.95)
    hit(s, cx, cy, 2.62, 1.5, "hall%d link" % (i + 1), target=target)
    d = 200 + i * 150
    step += [fx(t, "pop", 600, delay=d), fx(ic, "pop", 600, delay=d), fx(zl, "fade", 400, delay=d + 200),
             fx(nm, "fade", 400, delay=d + 200)]
tl.then(step)
tl.apply()
set_transition(s, "doors", 1600, dir="vert")
notes(s, "Мы входим в музей «Тело человека». Здесь шесть залов. Нажмите на билет зала — и Костик проведёт вас туда. "
         "Из каждого зала можно вернуться сюда кнопкой «В музей».\n"
         "Удобный порядок: залы с 1-го по 6-й, кнопка «Следующий зал» ведёт дальше по порядку.")


# ================================================================ hall frame
def hall_frame(slide, n, ttl_text, bgname, title_size=34):
    key, name, col, soft, target = HALLS[n - 1]
    bg(slide, bgname)
    w = text_width_in("ЗАЛ %d" % n, 12, FONT, True) + 5 * 1.2 / 72 + 1.0
    pill = box(slide, 0.6, 0.38, w, 0.42, fill=soft, kind="pill", name="!!hall%d" % n)
    pill.line.color.rgb = rgb(col)
    pill.line.width = E(0.02)
    emoji(slide, key, 0.7, 0.42, 0.34, name="!!hall%d icon" % n)
    zt = text(slide, 1.12, 0.38, w - 0.55, 0.42, "ЗАЛ %d" % n, 12, C["ink"], FONT, True, anchor="m", name="hall pill text")
    for r in zt._element.iter(qn("a:rPr")):
        r.set("spc", "120")
    title(slide, ttl_text, size=title_size)
    museum_btn(slide)
    home_btn(slide)


# ================================================================ SLIDE 8 — hall 1
s = S[8]
hall_frame(s, 1, "Скелет — опора тела", "bg_light.jpg")
tp = picture(s, img("tent"), 0.6, 1.9, name="tent", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(6.6, 3.71), descr="Палатка без каркаса упала, а палатка с каркасом стоит")
tc = text(s, 0.6, 5.78, 6.6, 0.75, "Без каркаса палатка падает. Без скелета мы не смогли бы даже стоять!", 17, C["muted"], FONT,
          True, name="tent caption")
dc = card(s, 7.55, 1.9, 5.18, 2.25, name="definition card")
dt = text(s, 7.85, 2.05, 4.65, 1.95, [[("Скелет", {"bold": True, "color": C["violet"]}),
                                        (" — это прочный каркас тела из костей. Он держит форму тела, защищает внутренние органы "
                                         "и вместе с мышцами помогает двигаться.", {})]], 17, name="definition", anchor="m")
kit.check_fit("def", "Скелет — это прочный каркас тела из костей. Он держит форму тела, защищает внутренние органы и вместе с мышцами помогает двигаться.", 17, 4.65, 1.95)
st1 = card(s, 7.55, 4.35, 2.49, 2.15, name="stat adult")
n1 = text(s, 7.7, 4.45, 2.2, 0.95, "206", 50, C["violet"], FONT_BLACK, align="c", name="stat adult num")
l1 = text(s, 7.75, 5.4, 2.1, 0.95, "костей у взрослого человека", 15, C["ink"], FONT, True, align="c", name="stat adult label")
st2 = card(s, 10.24, 4.35, 2.49, 2.15, name="stat baby")
n2 = text(s, 10.39, 4.45, 2.2, 0.95, "≈ 300", 50, C["coral"], FONT_BLACK, align="c", name="stat baby num")
l2 = text(s, 10.44, 5.4, 2.1, 1.0, "у малыша, потом часть костей срастается", 14, C["ink"], FONT, True, align="c", name="stat baby label")
nb = next_btn(s, "Следующий зал", 9, y=6.75)
tl = timeline(s)
tl.begin([fx(tp, "zoom", 700), fx(tc, "fade", 500, delay=400)])
tl.click([fx(dc, "float_up", 500), fx(dt, "float_up", 500)])
tl.click([fx(st1, "pop", 600, sound="pop"), fx(n1, "pop", 600), fx(l1, "fade", 400, delay=200),
          fx(st2, "pop", 600, delay=250), fx(n2, "pop", 600, delay=250), fx(l2, "fade", 400, delay=450)])
tl.apply()
set_transition(s, "morph", 1500)
notes(s, "Зал 1. Посмотрите на палатки: у одной нет каркаса — и она упала. Так и наше тело: без скелета мы не смогли бы стоять.\n"
         "Скелет — это прочный каркас тела из костей. Он держит форму тела, защищает внутренние органы и вместе с мышцами помогает двигаться.\n"
         "Щелчок — определение, ещё щелчок — интересные числа: у взрослого 206 костей, а у новорождённого около 300 — "
         "по мере роста некоторые кости срастаются.")

# ================================================================ SLIDE 9 — hall 2 (hotspots)
s = S[9]
hall_frame(s, 2, "Из чего состоит скелет", "bg_light.jpg")
hn = box(s, 0.6, 1.72, 6.2, 0.44, fill=C["lilac_soft"], kind="pill", name="hotspot hint")
shape_text(hn, "Нажимай на названия — узнаешь секреты костей!", 14, C["indigo"], FONT, True, margins=(0.12, 0.02))
SKH = 4.95
SKW = SKH * 3 / 4
SKX, SKY = (SW - SKW) / 2, 2.3
sk = picture(s, img("skeleton"), SKX, SKY, name="skeleton", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(SKW, SKH), descr="Скелет человека спереди")
PARTS_FILE = os.path.join(IMG, "skeleton_points.json")
PTS = {"skull": (0.5, 0.1), "ribs": (0.44, 0.27), "hand": (0.17, 0.53), "spine": (0.5, 0.4), "pelvis": (0.56, 0.49),
       "legs": (0.6, 0.72)}
if os.path.exists(PARTS_FILE):
    PTS.update({k: tuple(v) for k, v in json.load(open(PARTS_FILE)).items()})
PARTS = [  # side, row, key, label, colour, text
    ("l", 0, "skull", "Череп", C["violet"], "Защищает головной мозг — как прочный шлем"),
    ("l", 1, "ribs", "Грудная клетка", C["coral"], "12 пар рёбер берегут сердце и лёгкие"),
    ("l", 2, "hand", "Кости рук", C["sky"], "Берём, пишем, рисуем. В одной кисти 27 косточек!"),
    ("r", 0, "spine", "Позвоночник", C["mint"], "Главная опора тела: 33–34 позвонка, поэтому он гибкий"),
    ("r", 1, "pelvis", "Кости таза", C["orange"], "Опора для позвоночника, к ним крепятся ноги"),
    ("r", 2, "legs", "Кости ног", C["violet"], "Держат вес тела. Бедренная кость — самая длинная!"),
]
tl = timeline(s)
tl.begin([fx(sk, "zoom", 800)])
labels = []
for side, row, key, lab, col, info in PARTS:
    y = 2.3 + row * 1.42
    x = 0.6 if side == "l" else 9.03
    w = 3.7
    lw = text_width_in(lab, 17, FONT_BLACK) + 0.6
    lx = x + w - lw if side == "l" else x
    pill = box(s, lx, y, lw, 0.48, fill=col, kind="pill", name="part " + key)
    shape_text(pill, lab, 17, "FFFFFF", FONT_BLACK, margins=(0.1, 0.0))
    bevel(pill, w=0.05, h=0.02)
    shadow(pill, blur=0.1, dist=0.04, alpha=25)
    bub = card(s, x, y + 0.56, w, 0.8, name="info " + key)
    bub.line.color.rgb = rgb(col)
    bub.line.width = E(0.025)
    shape_text(bub, info, 14, C["ink"], FONT, True, margins=(0.14, 0.05), label="info " + key)
    px, py = PTS[key]
    tx, ty = SKX + px * SKW, SKY + py * SKH
    sx = lx + lw if side == "l" else lx
    sy = y + 0.24
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(sx), E(sy), E(tx), E(ty))
    ln.line.color.rgb = rgb(col)
    ln.line.width = Pt(3.5)
    lnel = ln.line._get_or_add_ln()
    lnel.set("cap", "rnd")
    tail = lnel.makeelement(qn("a:tailEnd"), {"type": "oval", "w": "med", "len": "med"})
    lnel.append(tail)
    set_name(ln, "leader " + key)
    dot = box(s, tx - 0.11, ty - 0.11, 0.22, 0.22, fill="FFFFFF", kind="oval", name="dot " + key)
    dot.line.color.rgb = rgb(col)
    dot.line.width = E(0.04)
    labels.append((pill, bub, ln, dot, side))
for pill, bub, ln, dot, side in labels:
    tl.trigger(pill, [fx(ln, "wipe_left" if side == "l" else "wipe_right", 450, sound="pop"), fx(dot, "pop", 400, delay=300),
                      fx(bub, "pop", 500, delay=150)])
step = [fx(p, "fly_left" if sd == "l" else "fly_right", 600, delay=120 * i) for i, (p, b, l, d, sd) in enumerate(labels)]
tl.then(step)
nb = next_btn(s, "Следующий зал", 10, y=6.75)
tl.apply()
set_transition(s, "morph", 1500, adv_click=False)
notes(s, "Зал 2. Это скелет человека. Нажимайте на цветные названия — появится линия к нужной части скелета и подсказка.\n"
         "Череп защищает головной мозг. Грудная клетка (12 пар рёбер) защищает сердце и лёгкие. Позвоночник — главная опора тела, "
         "в нём 33–34 позвонка, поэтому он гибкий. Кости таза — опора для позвоночника, к ним крепятся ноги. "
         "Кости рук помогают брать предметы, писать, рисовать (в кисти 27 косточек). Кости ног держат вес тела; бедренная кость — самая длинная.\n"
         "На этом слайде щелчок по пустому месту не перелистывает — используйте кнопку «Следующий зал» или стрелку на клавиатуре.")

# ================================================================ SLIDE 10 — hall 3 joints
s = S[10]
hall_frame(s, 3, "Суставы — «шарниры» скелета", "bg_mint.jpg")
mn = picture(s, img("mannequin"), 0.6, 1.9, name="mannequin", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(4.7, 4.7), descr="Деревянная кукла-манекен с подвижными суставами")
dc = card(s, 5.65, 1.9, 7.08, 1.5, name="joints def")
dtx = text(s, 5.95, 1.95, 6.55, 1.4, [[("Суставы", {"bold": True, "color": C["mint"]}),
                                       (" — подвижные соединения костей. Благодаря им мы сгибаем руки и ноги, поворачиваем голову.", {})]],
           17, name="joints def text", anchor="m")
kit.check_fit("joints", "Суставы — подвижные соединения костей. Благодаря им мы сгибаем руки и ноги, поворачиваем голову.", 17, 6.55, 1.4)
th = text(s, 5.65, 3.6, 7.0, 0.55, "Попробуй сам!", 24, "13846F", FONT_BLACK, name="try head")
acts = [("muscle", "Согни руку в локте"), ("hand", "Покрути кистью"), ("leg", "Присядь и встань"), ("smile", "Наклони голову")]
tl = timeline(s)
tl.begin([fx(mn, "zoom", 700), fx(dc, "float_up", 500, delay=300), fx(dtx, "float_up", 500, delay=300),
          fx(th, "fade", 400, delay=600)])
for i, (key, t) in enumerate(acts):
    x = 5.65 + (i % 2) * 3.64
    y = 4.25 + (i // 2) * 1.2
    c = card(s, x, y, 3.44, 1.05, name="act %d" % (i + 1))
    ic, ii = icon_circle(s, key, x + 0.15, y + 0.15, 0.75, C["mint_soft"], name="act%d" % (i + 1))
    tt = text(s, x + 1.05, y, 2.3, 1.05, t, 17, C["ink"], FONT, True, anchor="m", name="act text %d" % (i + 1))
    tl.click([fx(c, "pop", 500, sound="pop"), fx(ic, "pop", 500), fx(ii, "pop", 500), fx(tt, "pop", 500)])
nb = next_btn(s, "Следующий зал", 11, y=6.75)
tl.apply()
set_transition(s, "morph", 1500)
notes(s, "Зал 3. Посмотрите на деревянную куклу: она гнётся там, где у неё шарниры. У нас тоже есть такие «шарниры» — суставы.\n"
         "Суставы — подвижные соединения костей: плечевой, локтевой, коленный, тазобедренный и другие.\n"
         "По щелчку появляются задания «Попробуй сам!» — дети выполняют движения: сгибают руку в локте, крутят кистью, приседают, "
         "наклоняют голову. Спросите: какие суставы работали?")

# ================================================================ SLIDE 11 — hall 4 muscles
s = S[11]
hall_frame(s, 4, "Мышцы — двигатели тела", "bg_warm.jpg")
ar = picture(s, img("arm"), 0.6, 1.9, name="arm", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(5.6, 4.2), descr="Рука: мышцы сгибают и разгибают её в локте")
ARM_FILE = os.path.join(IMG, "arm_points.json")
APTS = {"biceps": (0.45, 0.3), "triceps": (0.42, 0.62)}
if os.path.exists(ARM_FILE):
    APTS.update({k: tuple(v) for k, v in json.load(open(ARM_FILE)).items()})
bl = box(s, 0.6 + APTS["biceps"][0] * 5.6 - 0.75, 1.9 + APTS["biceps"][1] * 4.2 - 0.22, 1.5, 0.44, fill=C["coral"], kind="pill",
         name="biceps label")
shape_text(bl, "сгибает", 15, "FFFFFF", FONT_BLACK, margins=(0.05, 0))
shadow(bl, blur=0.1, dist=0.04, alpha=30)
tlb = box(s, 0.6 + APTS["triceps"][0] * 5.6 - 0.85, 1.9 + APTS["triceps"][1] * 4.2 - 0.22, 1.7, 0.44, fill=C["sky"], kind="pill",
          name="triceps label")
shape_text(tlb, "разгибает", 15, "FFFFFF", FONT_BLACK, margins=(0.05, 0))
shadow(tlb, blur=0.1, dist=0.04, alpha=30)
facts = [("muscle", [("600+", {"face": FONT_BLACK, "size": 26, "color": C["coral"]}), ("  мышц в теле человека", {"bold": True})],
          "600+ мышц в теле человека"),
         ("bone", [("Мышцы крепятся к костям сухожилиями. Сокращаясь, они тянут кость — и мы двигаемся.", {})],
          "Мышцы крепятся к костям сухожилиями. Сокращаясь, они тянут кость — и мы двигаемся."),
         ("clap", [("Мышцы работают парами: одна сгибает руку, другая разгибает.", {})],
          "Мышцы работают парами: одна сгибает руку, другая разгибает."),
         ("heart", [("Сердце — тоже мышца! Оно работает без отдыха всю жизнь.", {})],
          "Сердце — тоже мышца! Оно работает без отдыха всю жизнь.")]
tl = timeline(s)
tl.begin([fx(ar, "zoom", 700)])
tl.then([fx(bl, "pop", 500), fx(tlb, "pop", 500, delay=200)])
for i, (key, runs, plain) in enumerate(facts):
    y = 1.9 + i * 1.1
    c = card(s, 6.55, y, 6.18, 0.95, name="fact %d" % (i + 1))
    ic, ii = icon_circle(s, key, 6.7, y + 0.13, 0.7, C["coral_soft"], name="fact%d" % (i + 1))
    tt = text(s, 7.55, y, 5.05, 0.95, [runs], 15, C["ink"], FONT, False, anchor="m", name="fact text %d" % (i + 1))
    kit.check_fit("fact %d" % i, plain, 15, 5.05, 0.95)
    tl.click([fx(c, "fly_right", 500), fx(ic, "fly_right", 500), fx(ii, "fly_right", 500), fx(tt, "fly_right", 500)])
nb = next_btn(s, "Следующий зал", 12, y=6.75)
tl.apply()
set_transition(s, "morph", 1500)
notes(s, "Зал 4. Кости сами двигаться не могут — их приводят в движение мышцы. В теле человека больше 600 мышц.\n"
         "Мышцы крепятся к костям сухожилиями. Сокращаясь, мышца тянет кость. Мышцы работают парами: "
         "двуглавая мышца плеча (бицепс) сгибает руку, трёхглавая (трицепс) — разгибает. Предложите детям согнуть руку и потрогать мышцу.\n"
         "Сердце — тоже мышца, которая работает всю жизнь без отдыха.\n"
         "Вывод: скелет и мышцы вместе — это опорно-двигательная система.")

# ================================================================ SLIDE 12 — hall 5 posture game
s = S[12]
hall_frame(s, 5, "Осанка: кто сидит правильно?", "bg_light.jpg")
dfn = box(s, 0.6, 1.7, 12.13, 0.62, fill=C["lilac_soft"], radius=0.2, name="posture def")
shape_text(dfn, "Осанка — это привычное положение тела, когда мы сидим, стоим и ходим.", 17, C["indigo"], FONT, True,
           margins=(0.2, 0.04))
IMW = 3.85
xs2 = [3.0, 3.0 + IMW + 1.0]
pics = {}
for i, key in enumerate(["posture_bad", "posture_good"]):
    x = xs2[i]
    p = picture(s, img(key), x, 2.55, name=key, rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
                crop_to=(IMW, IMW), descr="Мальчик сидит за партой " + ("сгорбившись" if key == "posture_bad" else "с прямой спиной"))
    lt = box(s, x - 0.22, 2.35, 0.62, 0.62, fill=C["violet"], kind="oval", name="letter %d" % (i + 1))
    shape_text(lt, "АБ"[i], 20, "FFFFFF", FONT_BLACK, margins=(0, 0))
    bevel(lt, w=0.05, h=0.02)
    pics[key] = (p, x, lt)
tl = timeline(s)
tl.begin([fx(pics["posture_bad"][0], "zoom", 600), fx(pics["posture_good"][0], "zoom", 600, delay=200),
          fx(pics["posture_bad"][2], "pop", 500, delay=400), fx(pics["posture_good"][2], "pop", 500, delay=550)])
m12 = mascot(s, "mascot_think", 1.55, 7.3, 2.75, name="!!mascot")
for key, good in (("posture_bad", False), ("posture_good", True)):
    p, x, _ = pics[key]
    col = C["green"] if good else C["red"]
    fr = box(s, x - 0.06, 2.49, IMW + 0.12, IMW + 0.12, fill=None, radius=0.33, name="frame " + key)
    fr.line.color.rgb = rgb(col)
    fr.line.width = E(0.1)
    bw = 3.5
    badge = box(s, x + (IMW - bw) / 2, 2.55 + IMW - 0.42, bw, 0.62, fill=col, kind="pill", name="badge " + key)
    shape_text(badge, "Правильно! Спина прямая" if good else "Неправильно! Спина согнута", 14, "FFFFFF", FONT_BLACK,
               margins=(0.08, 0.0), label="posture badge")
    bevel(badge, w=0.05, h=0.02)
    mark = emoji(s, "check" if good else "cross", x + IMW - 0.55, 2.3, 0.75, name="mark " + key)
    h = hit(s, x, 2.55, IMW, IMW, "click " + key)
    if good:
        tl.trigger(h, [fx(fr, "zoom", 400, sound="correct"), fx(badge, "pop", 600, delay=100), fx(mark, "spin_in", 600, delay=150)]
                   ).then([fx(p, "pulse", 300, scale=106000)])
    else:
        tl.trigger(h, [fx(fr, "fade", 300, sound="wrong"), fx(badge, "pop", 500, delay=100), fx(mark, "zoom", 400, delay=100)]
                   ).then([fx(p, "shake")])
tl.then([fx(m12, "fly_left", 700)])
nb = next_btn(s, "Правила осанки", 13, y=6.75)
tl.apply()
set_transition(s, "morph", 1500, adv_click=False)
notes(s, "Зал 5. Осанка — это привычное положение тела, когда мы сидим, стоим и ходим.\n"
         "Вопрос: кто из мальчиков сидит правильно? Пусть дети ответят, а затем нажмите на картинку.\n"
         "Картинка Б — правильно: спина прямая, ноги на полу, тетрадь далеко от глаз (зелёная рамка и звук колокольчика). "
         "Картинка А — неправильно: спина согнута, голова низко (красная рамка).\n"
         "Щелчок по пустому месту не перелистывает слайд — дальше по кнопке «Правила осанки».")

# ================================================================ SLIDE 13 — posture rules
s = S[13]
hall_frame(s, 5, "Как сохранить правильную осанку", "bg_mint.jpg")
m13 = mascot(s, "mascot_posture", 2.15, 7.2, 5.1, name="!!mascot")
rules = [("chair", "Сиди прямо: спина касается спинки стула, ноги стоят на полу", C["sky"]),
         ("backpack", "Носи рюкзак на двух плечах, а не в одной руке", C["coral"]),
         ("sleep", "Спи на ровной постели с невысокой подушкой", C["violet"]),
         ("cartwheel", "Каждый день делай зарядку и больше двигайся", C["mint"])]
tl = timeline(s)
tl.begin([fx(m13, "bounce", 1000)])
for i, (key, t, col) in enumerate(rules):
    x = 4.35 + (i % 2) * 4.29
    y = 1.9 + (i // 2) * 2.35
    c = card(s, x, y, 4.09, 2.15, name="rule %d" % (i + 1))
    ic, ii = icon_circle(s, key, x + 0.25, y + 0.25, 0.9, col, name="rule%d" % (i + 1))
    for el in (ic,):
        bevel(el, w=0.06, h=0.025)
    nm = text(s, x + 1.3, y + 0.3, 2.5, 0.6, "Правило %d" % (i + 1), 15, col if col != C["sun"] else "C98A00", FONT_BLACK,
              name="rule num %d" % (i + 1))
    tt = text(s, x + 0.25, y + 1.2, 3.65, 0.85, t, 16, C["ink"], FONT, True, name="rule text %d" % (i + 1))
    tl.click([fx(c, "pop", 500, sound="pop"), fx(ic, "pop", 500), fx(ii, "pop", 500), fx(nm, "fade", 400, delay=200),
              fx(tt, "fade", 400, delay=200)])
nb = next_btn(s, "Следующий зал", 14, y=6.75)
tl.apply()
set_transition(s, "morph", 1500)
notes(s, "Правила хорошей осанки появляются по щелчку. Костик держит книгу на голове — попробуйте пройтись по классу так же, "
         "ровно-ровно, чтобы книга не упала! Это отличное упражнение для осанки.")

# ================================================================ SLIDE 14 — records
s = S[14]
hall_frame(s, 6, "Музей рекордов", "bg_light.jpg")
rc = picture(s, img("records"), 0.6, 1.9, name="records", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(4.6, 4.6), descr="Лупа над крошечной косточкой и длинная бедренная кость")
recs = [("206", "костей в скелете взрослого человека", C["violet"]),
        ("600+", "мышц помогают нам двигаться", C["coral"]),
        ("3 мм", "длина стремечка — самой маленькой косточки (она в ухе)", C["mint"]),
        ("106", "костей в кистях и стопах — больше половины всех!", "E39B00")]
tl = timeline(s)
tl.begin([fx(rc, "zoom", 700)])
for i, (num, lab, col) in enumerate(recs):
    x = 5.55 + (i % 2) * 3.69
    y = 1.9 + (i // 2) * 2.4
    c = card(s, x, y, 3.49, 2.2, name="record %d" % (i + 1))
    nt = text(s, x + 0.2, y + 0.15, 3.1, 0.95, num, 46, col, FONT_BLACK, align="c", name="record num %d" % (i + 1))
    lt = text(s, x + 0.25, y + 1.12, 3.0, 0.95, lab, 15, C["ink"], FONT, True, align="c", name="record text %d" % (i + 1))
    tl.click([fx(c, "stretch_h", 450, sound="flip"), fx(nt, "pop", 600, delay=250), fx(lt, "fade", 400, delay=350)])
nb = next_btn(s, "Выйти из музея", 15, y=6.75)
tl.apply()
set_transition(s, "morph", 1500)
notes(s, "Зал 6 — Музей рекордов. По щелчку открываются карточки: 206 костей у взрослого; больше 600 мышц; "
         "самая маленькая кость — стремечко в ухе, около 3 мм; в кистях и стопах 106 костей — больше половины всех костей скелета! "
         "Самая длинная кость — бедренная.\nКнопка «Выйти из музея» ведёт к физминутке.")

# ================================================================ SLIDE 15 — fizminutka
s = S[15]
bg(s, "bg_mint.jpg")
kicker(s, "ФИЗМИНУТКА", C["mint"])
title(s, "Разминаем косточки и мышцы!")
home_btn(s)
VW = 8.3
VH = VW * 768 / 1344
mv = s.shapes.add_movie(os.path.join(ASSETS, "fizminutka.mp4"), E(0.6), E(1.9), E(VW), E(VH),
                        poster_frame_image=os.path.join(ASSETS, "fizminutka_poster.jpg"), mime_type="video/mp4")
set_name(mv, "fizminutka video")
set_descr(mv, "Видео-физминутка: учительница показывает упражнения")
geom = mv._element.spPr.find(qn("a:prstGeom"))
geom.set("prst", "roundRect")
mv.line.color.rgb = rgb("FFFFFF")
mv.line.width = E(0.07)
shadow(mv, blur=0.25, dist=0.08, alpha=25)
vc = text(s, 0.6, 1.9 + VH + 0.12, VW, 0.4, "Видео играет само и повторяется. Нажми на видео, чтобы поставить на паузу.", 13,
          C["muted"], FONT, True, align="c", name="video tip")
ec = card(s, 9.25, 1.9, 3.48, 2.95, name="moves card")
eh = text(s, 9.5, 2.05, 3.0, 0.5, "Повторяй за мной!", 19, "13846F", FONT_BLACK, name="moves head")
el = text(s, 9.5, 2.6, 3.05, 2.15, "Руки в стороны\nНаклоны вправо и влево\nРуки вверх — потянулись!\nПрисели — встали",
          16, C["ink"], FONT, True, para_space=5, name="moves list")
m15 = mascot(s, "mascot_flex", 11.0, 7.3, 2.45, name="!!mascot")
tl = timeline(s)
tl.begin([fx(mv, "play", 10140)])
tl.trigger(mv, [fx(mv, "toggle", 1)])
tl.media(mv, loop=True)
tl.apply()
set_transition(s, "ferris", 1500, dir="l")
notes(s, "Физминутка! Все встают. Видео запускается автоматически и повторяется по кругу — выполняйте движения вместе с героиней: "
         "руки в стороны, наклоны вправо-влево, руки вверх, присесть и встать. Щелчок по видео — пауза/продолжить.\n"
         "Видео для физминутки создано нейросетью.")

# ================================================================ SLIDE 16 — games hub
s = S[16]
bg(s, "bg_quiz.jpg")
kicker(s, "ИНТЕРАКТИВНЫЕ ИГРЫ", C["violet"])
title(s, "Проверь себя!")
home_btn(s)
m16 = mascot(s, "mascot_think", 2.2, 7.2, 5.0, name="!!mascot")
games = [("target", "Викторина «Знаток скелета»", "5 вопросов — выбери верный ответ", 17, C["violet"]),
         ("puzzle", "Игра «Кто кого защищает?»", "Соедини кость и орган", 22, C["coral"]),
         ("question", "Игра «Верю — не верю»", "Переверни карточку и проверь", 23, C["mint"])]
tl = timeline(s)
tl.begin([fx(m16, "fly_left", 700)])
step = []
for i, (key, nm, sub, target, col) in enumerate(games):
    y = 1.95 + i * 1.6
    c = card(s, 4.4, y, 8.33, 1.38, name="game %d" % (i + 1))
    c.line.color.rgb = rgb(col)
    c.line.width = E(0.03)
    ic, ii = icon_circle(s, key, 4.6, y + 0.19, 1.0, col, name="game%d" % (i + 1))
    bevel(ic, w=0.07, h=0.03)
    t1 = text(s, 5.85, y + 0.18, 5.6, 0.55, nm, 22, C["ink"], FONT_BLACK, name="game title %d" % (i + 1))
    t2 = text(s, 5.85, y + 0.78, 5.6, 0.45, sub, 16, C["muted"], FONT, True, name="game sub %d" % (i + 1))
    pi = emoji(s, "play", 11.85, y + 0.41, 0.56, name="game play %d" % (i + 1))
    hit(s, 4.4, y, 8.33, 1.38, "game link %d" % (i + 1), target=target)
    d = 250 * i
    step += [fx(c, "fly_right", 600, delay=d), fx(ic, "fly_right", 600, delay=d), fx(ii, "fly_right", 600, delay=d),
             fx(t1, "fly_right", 600, delay=d), fx(t2, "fly_right", 600, delay=d), fx(pi, "spin_in", 600, delay=d + 300)]
tl.then(step)
tl.apply()
set_transition(s, "switch", 1300, dir="r")
notes(s, "Интерактивные игры, сделанные средствами PowerPoint (триггеры, анимация, гиперссылки, звуки).\n"
         "Нажмите на игру, чтобы начать. Правило: если ответ верный — зелёный цвет и колокольчик, если нет — красный цвет, "
         "и можно попробовать ещё раз. Игры идут по порядку: викторина → «Кто кого защищает?» → «Верю — не верю».")

# ================================================================ SLIDES 17–21 — quiz
QUIZ = [("Что служит опорой нашего тела?", ["Кожа", "Скелет", "Сердце"], 1),
        ("Какие кости защищают головной мозг?", ["Череп", "Рёбра", "Позвоночник"], 0),
        ("Что защищает грудная клетка?", ["Желудок", "Головной мозг", "Сердце и лёгкие"], 2),
        ("Сколько мышц в теле человека?", ["Около 60", "Больше 600", "Около 6"], 1),
        ("Как называются подвижные соединения костей?", ["Суставы", "Мышцы", "Позвонки"], 0)]
LETTERS = "АБВ"
ACOLS = [C["sky"], C["coral"], C["mint"]]
for qi, (question, answers, right) in enumerate(QUIZ):
    s = S[17 + qi]
    bg(s, "bg_quiz.jpg")
    kicker(s, "ВОПРОС %d ИЗ 5" % (qi + 1), C["violet"])
    title(s, question, size=32, w=11.4, h=1.2)
    home_btn(s)
    for d in range(5):
        dcol = C["mint"] if d < qi else (C["violet"] if d == qi else "FFFFFF")
        dt = box(s, 9.55 + d * 0.5, 0.5, 0.3, 0.3, fill=dcol, kind="oval", name="!!progress %d" % (d + 1))
        if d > qi:
            dt.line.color.rgb = rgb(C["lilac"])
            dt.line.width = E(0.025)
    tl = timeline(s)
    m_think = mascot(s, "mascot_think", 1.45, 7.35, 2.35, name="mascot think")
    m_joy = mascot(s, "mascot_joy", 1.45, 7.35, 2.45, name="mascot joy")
    b0 = box(s, 2.75, 5.55, 4.4, 0.9, fill="FFFFFF", radius=0.3, name="bubble ask")
    shadow(b0, alpha=18)
    shape_text(b0, "Выбери правильный ответ!", 17, C["ink"], FONT, True)
    b_bad = box(s, 2.75, 5.55, 4.4, 0.9, fill=C["coral_soft"], radius=0.3, name="bubble wrong")
    b_bad.line.color.rgb = rgb(C["red"])
    b_bad.line.width = E(0.025)
    shape_text(b_bad, "Ой! Подумай ещё раз", 17, C["red"], FONT_BLACK)
    b_ok = box(s, 2.75, 5.55, 4.4, 0.9, fill="E3F8EC", radius=0.3, name="bubble right")
    b_ok.line.color.rgb = rgb(C["green"])
    b_ok.line.width = E(0.025)
    shape_text(b_ok, "Верно! Молодец!", 19, "138A55", FONT_BLACK)
    hits = []
    for ai, a in enumerate(answers):
        x = 0.6 + ai * 4.19
        y = 2.4
        c = card(s, x, y, 3.75, 2.4, name="answer %s" % LETTERS[ai])
        lc = box(s, x + 0.25, y + 0.25, 0.7, 0.7, fill=ACOLS[ai], kind="oval", name="letter %s" % LETTERS[ai])
        shape_text(lc, LETTERS[ai], 22, "FFFFFF", FONT_BLACK, margins=(0, 0))
        bevel(lc, w=0.05, h=0.02)
        at = text(s, x + 0.25, y + 0.95, 3.25, 1.25, a, 26, C["ink"], FONT_BLACK, align="c", anchor="m", name="answer text %s" % LETTERS[ai])
        good = ai == right
        ov = box(s, x, y, 3.75, 2.4, fill=C["green"] if good else C["red"], radius=0.22, name="result %s" % LETTERS[ai])
        shape_text(ov, [[("Верно!" if good else "Не то!", {"size": 30, "face": FONT_BLACK})], [(a, {"size": 20, "bold": True})]],
                   26, "FFFFFF", FONT_BLACK, check=False)
        kit.check_fit("quiz answer", a, 20, 3.5, 0.6, FONT, True)
        mk = emoji(s, "check" if good else "cross", x + 3.75 - 0.62, y - 0.22, 0.8, name="mark %s" % LETTERS[ai])
        hits.append((x, y, good, ov, mk, c))
    nxt_target = 18 + qi if qi < 4 else 22
    nb = next_btn(s, "Следующий вопрос" if qi < 4 else "Следующая игра", nxt_target, y=6.62)
    for x, y, good, ov, mk, c in hits:
        h = hit(s, x, y, 3.75, 2.4, "choose %s" % ("right" if good else "wrong"))
        if good:
            tl.trigger(h, [fx(ov, "zoom", 450, sound="correct"), fx(mk, "spin_in", 600, delay=150), fx(b_ok, "pop", 500, delay=100),
                           fx(m_think, "fade_out", 300), fx(m_joy, "bounce", 900, delay=100)]
                       ).then([fx(nb[0], "fly_bottom", 500), fx(nb[1], "fly_bottom", 500), fx(nb[2], "fly_bottom", 500)])
        else:
            tl.trigger(h, [fx(ov, "fade", 300, sound="wrong"), fx(mk, "zoom", 400, delay=100), fx(b_bad, "pop", 400)]
                       ).then([fx(ov, "shake")]).then([fx(b_bad, "fade_out", 400)], delay=1200)
    tl.apply()
    set_transition(s, "prism", 1400, adv_click=False)
    notes(s, "Вопрос %d. %s\nВарианты: %s.\nПравильный ответ: %s.\n"
             "Нажмите на ответ, который выбрали дети. Верный — зелёная карточка, колокольчик, Костик прыгает от радости, "
             "и появляется кнопка «%s». Неверный — красная карточка и подсказка «Подумай ещё раз»; можно выбрать снова."
          % (qi + 1, question, ", ".join(answers), answers[right], "Следующий вопрос" if qi < 4 else "Следующая игра"))

# ================================================================ SLIDE 22 — matching
s = S[22]
bg(s, "bg_quiz.jpg")
kicker(s, "ИГРА НА СООТВЕТСТВИЕ", C["coral"])
title(s, "Кто кого защищает?")
home_btn(s)
ins = text(s, 0.6, 1.65, 11.5, 0.45, "Назовите пару вслух, а потом нажмите на кость — проверим!", 17, C["muted"], FONT, True,
           name="match hint")
LEFT = [("Череп", "skull", C["violet"]), ("Грудная клетка", "bone", C["coral"]), ("Позвоночник", "bone", C["mint"])]
RIGHT = [("Сердце и лёгкие", "lungs"), ("Головной мозг", "brain"), ("Спинной мозг", "zap")]
PAIR = {0: 1, 1: 0, 2: 2}
ROWY = [2.45, 3.95, 5.45]
tl = timeline(s)
rights = []
for j, (nm, key) in enumerate(RIGHT):
    y = ROWY[j]
    c = card(s, 8.73, y, 4.0, 1.15, name="organ %d" % (j + 1))
    ic, ii = icon_circle(s, key, 8.9, y + 0.15, 0.85, C["lilac_soft"], name="organ%d" % (j + 1))
    tt = text(s, 9.9, y, 2.7, 1.15, nm, 19, C["ink"], FONT_BLACK, anchor="m", name="organ text %d" % (j + 1))
    fr = box(s, 8.67, y - 0.06, 4.12, 1.27, fill=None, radius=0.26, name="organ ok %d" % (j + 1))
    fr.line.color.rgb = rgb(C["green"])
    fr.line.width = E(0.07)
    mk = emoji(s, "check", 12.35, y - 0.25, 0.6, name="organ check %d" % (j + 1))
    rights.append((fr, mk))
for i, (nm, key, col) in enumerate(LEFT):
    y = ROWY[i]
    c = card(s, 0.6, y, 4.0, 1.15, name="bone card %d" % (i + 1))
    c.line.color.rgb = rgb(col)
    c.line.width = E(0.03)
    ic, ii = icon_circle(s, key, 0.77, y + 0.15, 0.85, col, name="bonecard%d" % (i + 1))
    tt = text(s, 1.77, y, 2.7, 1.15, nm, 19, C["ink"], FONT_BLACK, anchor="m", name="bone text %d" % (i + 1))
    j = PAIR[i]
    y2 = ROWY[j]
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, E(4.68), E(y + 0.575), E(8.65), E(y2 + 0.575))
    ln.line.color.rgb = rgb(col)
    ln.line.width = Pt(6)
    lnel = ln.line._get_or_add_ln()
    lnel.set("cap", "rnd")
    lnel.append(lnel.makeelement(qn("a:headEnd"), {"type": "oval", "w": "sm", "len": "sm"}))
    lnel.append(lnel.makeelement(qn("a:tailEnd"), {"type": "oval", "w": "sm", "len": "sm"}))
    set_name(ln, "pair line %d" % (i + 1))
    h = hit(s, 0.6, y, 4.0, 1.15, "pick bone %d" % (i + 1))
    fr, mk = rights[j]
    tl.trigger(h, [fx(ln, "wipe_left", 600, sound="correct"), fx(c, "pulse", 250, scale=105000)]
               ).then([fx(fr, "zoom", 400), fx(mk, "spin_in", 600)])
nb = next_btn(s, "Следующая игра", 23, y=6.75)
tl.apply()
set_transition(s, "conveyor", 1400, dir="l", adv_click=False)
notes(s, "Игра на соответствие. Спросите детей: что защищает череп? грудная клетка? позвоночник?\n"
         "После ответа нажмите на карточку кости — появится линия к органу, который она защищает, и зелёная рамка.\n"
         "Череп — головной мозг; грудная клетка — сердце и лёгкие; позвоночник — спинной мозг.")

# ================================================================ SLIDE 23 — true / false
s = S[23]
bg(s, "bg_quiz.jpg")
kicker(s, "ИГРА", C["mint"])
title(s, "Верю — не верю")
home_btn(s)
ins = text(s, 0.6, 1.65, 11.5, 0.45, "Это правда или нет? Нажмите на карточку, чтобы перевернуть её", 17, C["muted"], FONT, True,
           name="tf hint")
TF = [("Сердце — это тоже мышца", True, "Сердце — мышца, которая работает без отдыха всю жизнь"),
      ("Позвоночник — это одна длинная кость", False, "Он состоит из 33–34 позвонков, поэтому гнётся"),
      ("Самая маленькая косточка находится в ухе", True, "Это стремечко — всего около 3 мм"),
      ("Чтобы мышцы были сильными, нужно больше лежать", False, "Мышцы крепнут, когда мы двигаемся и занимаемся спортом")]
tl = timeline(s)
for i, (stmt, truth, why) in enumerate(TF):
    x = 0.6 + i * 3.09
    y, w, h = 2.3, 2.85, 4.0
    back = box(s, x, y, w, h, fill=C["green"] if truth else C["coral"], radius=0.25, name="tf back %d" % (i + 1))
    shadow(back, alpha=22)
    shape_text(back, [[("ВЕРЮ!" if truth else "НЕ ВЕРЮ!", {"size": 26, "face": FONT_BLACK})], [("", {"size": 8})],
                      [(why, {"size": 16, "bold": True})]], 16, "FFFFFF", FONT, margins=(0.22, 0.2), check=False)
    kit.check_fit("tf why", why, 16, w - 0.44, 2.6, FONT, True)
    front = box(s, x, y, w, h, fill="FFFFFF", radius=0.25, name="tf front %d" % (i + 1))
    front.line.color.rgb = rgb(C["lilac"])
    front.line.width = E(0.04)
    shadow(front, alpha=18)
    shape_text(front, [[("?", {"size": 54, "face": FONT_BLACK, "color": C["lilac"]})], [(stmt, {"size": 19, "bold": True})],
                       [("", {"size": 8})], [("Верю или не верю?", {"size": 13, "color": C["muted"], "bold": True})]],
               19, C["ink"], FONT, margins=(0.2, 0.2), check=False)
    kit.check_fit("tf stmt", stmt, 19, w - 0.4, 1.9, FONT, True)
    tl.trigger(front, [fx(front, "collapse_h", 260, sound="flip")]).then([fx(back, "stretch_h", 300)])
nb = next_btn(s, "Онлайн-задание", 24, y=6.75)
tl.apply()
set_transition(s, "flip", 1300, dir="r", adv_click=False)
notes(s, "Игра «Верю — не верю». Учитель читает утверждение, дети поднимают руки: «верю» или «не верю». "
         "Затем нажмите на карточку — она перевернётся и покажет правильный ответ.\n"
         "1) Сердце — тоже мышца: верю. 2) Позвоночник — одна кость: не верю (33–34 позвонка). "
         "3) Самая маленькая кость в ухе: верю (стремечко, около 3 мм). 4) Чтобы мышцы были сильными, надо больше лежать: не верю.")

# ================================================================ SLIDE 24 — online task
s = S[24]
bg(s, "bg_mint.jpg")
kicker(s, "ОНЛАЙН-ЗАДАНИЕ", C["sky"])
title(s, "Играем онлайн!")
home_btn(s)
m24 = mascot(s, "mascot_tablet", 2.35, 7.25, 5.3, name="!!mascot")
oc = card(s, 4.6, 1.9, 8.13, 4.85, name="online card")
oh = text(s, 4.95, 2.1, 7.5, 0.6, "Игра «Костик и тайны скелета»", 24, C["ink"], FONT_BLACK, name="online head")
LV = [("puzzle", "Подбери к каждой кости её работу"), ("clock", "«Верно или неверно» — на время"),
      ("backpack", "Полезно или вредно для осанки?")]
tl = timeline(s)
tl.begin([fx(m24, "fly_left", 700), fx(oc, "float_up", 600, delay=200), fx(oh, "float_up", 600, delay=200)])
step = []
for i, (key, t) in enumerate(LV):
    y = 2.85 + i * 0.68
    ic, ii = icon_circle(s, key, 4.95, y, 0.55, C["sky_soft"], name="level%d" % (i + 1))
    tt = text(s, 5.65, y - 0.02, 6.8, 0.6, "Уровень %d. %s" % (i + 1, t), 16, C["ink"], FONT, True, anchor="m",
              name="level text %d" % (i + 1))
    step += [fx(ic, "fade", 400, delay=150 * i), fx(ii, "fade", 400, delay=150 * i), fx(tt, "fade", 400, delay=150 * i)]
tl.then(step)
pb = box(s, 4.95, 5.0, 4.5, 0.95, fill=C["coral"], kind="pill", name="play online")
bevel(pb)
shadow(pb, alpha=30)
shape_text(pb, "Играть онлайн", 22, "FFFFFF", FONT_BLACK, margins=(0.6, 0.02))
pic_play = emoji(s, "rocket", 5.15, 5.17, 0.6, name="play online icon")
for el in (pb, pic_play):
    link_url(el, GAME_URL)
ut = text(s, 4.95, 6.05, 5.6, 0.45, GAME_URL.replace("https://", ""), 14, C["muted"], FONT, True, name="online url")
link_url(ut, GAME_URL)
qr2 = picture(s, os.path.join(IMG, "qr_game.png") if os.path.exists(os.path.join(IMG, "qr_game.png")) else os.path.join(ASSETS, "qr_video.png"),
              10.75, 4.6, w=1.65, h=1.65, name="qr game", descr="QR-код на онлайн-игру")
link_url(qr2, GAME_URL)
qt2 = text(s, 10.45, 6.28, 2.25, 0.35, "Сканируй QR-код", 13, C["muted"], FONT, True, align="c", name="qr game text")
tl.then([fx(pb, "pop", 600, sound="pop"), fx(pic_play, "pop", 600), fx(ut, "fade", 400), fx(qr2, "zoom", 500, delay=200),
         fx(qt2, "fade", 400, delay=300)])
tl.then([fx(pb, "pulse", 400, scale=108000)])
tl.apply()
set_transition(s, "airplane", 1800)
notes(s, "Онлайн-задание. Нажмите кнопку «Играть онлайн» (нужен интернет) или дайте детям отсканировать QR-код планшетом/телефоном.\n"
         "Ссылка: " + GAME_URL + "\nВ игре три уровня: подобрать к каждой кости её работу; ответить «верно/неверно» на время; "
         "разложить привычки на полезные и вредные для осанки. В конце — звёзды и диплом «Знаток скелета».")

# ================================================================ SLIDE 25 — summary: finish the sentence
s = S[25]
bg(s, "bg_light.jpg")
kicker(s, "ПОДВЕДЁМ ИТОГИ", C["orange"])
title(s, "Закончи предложение")
home_btn(s)
FIN = [("Опора нашего тела — это…", "скелет", C["violet"]), ("Головной мозг защищает…", "череп", C["sky"]),
       ("Подвижные соединения костей — это…", "суставы", C["mint"]), ("Кости приводят в движение…", "мышцы", C["coral"]),
       ("Правильное положение тела — это…", "осанка", C["orange"])]
tl = timeline(s)
step = []
for i, (q, a, col) in enumerate(FIN):
    y = 1.95 + i * 0.95
    c = card(s, 0.6, y, 8.55, 0.8, name="sentence %d" % (i + 1))
    nn = box(s, 0.75, y + 0.13, 0.54, 0.54, fill=col, kind="oval", name="sentence num %d" % (i + 1))
    shape_text(nn, str(i + 1), 17, "FFFFFF", FONT_BLACK, margins=(0, 0))
    qt = text(s, 1.5, y, 7.5, 0.8, q, 20, C["ink"], FONT, True, anchor="m", name="sentence text %d" % (i + 1))
    slot = box(s, 9.4, y + 0.06, 3.33, 0.68, fill="FFFFFF", kind="pill", name="slot %d" % (i + 1))
    slot.line.color.rgb = rgb(C["lilac"])
    slot.line.width = E(0.025)
    ln = slot.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:prstDash"), {"val": "dash"}))
    an = box(s, 9.4, y + 0.06, 3.33, 0.68, fill=col, kind="pill", name="answer word %d" % (i + 1))
    shape_text(an, a.upper(), 22, "FFFFFF", FONT_BLACK, margins=(0.1, 0))
    bevel(an, w=0.05, h=0.02)
    d = 120 * i
    step += [fx(c, "fly_left", 500, delay=d), fx(nn, "fly_left", 500, delay=d), fx(qt, "fly_left", 500, delay=d),
             fx(slot, "fade", 400, delay=d + 200)]
    FIN[i] = (q, a, col, an)
tl.begin(step)
for q, a, col, an in FIN:
    tl.click([fx(an, "pop", 600, sound="correct")])
tl.apply()
set_transition(s, "vortex", 1800, dir="r")
notes(s, "Подведение итогов в игровой форме. Учитель читает начало фразы, дети хором заканчивают, затем щелчок — появляется ответ.\n"
         "Ответы: скелет; череп; суставы; мышцы; осанка.")

# ================================================================ SLIDE 26 — infographic
s = S[26]
bg(s, "bg_sun.jpg")
kicker(s, "ИНФОГРАФИКА", C["indigo"])
title(s, "Что мы узнали")
home_btn(s)
cc = box(s, 4.87, 2.05, 3.6, 3.6, fill="FFFFFF", kind="oval", name="center circle")
shadow(cc, alpha=25)
bevel(cc, w=0.12, h=0.05)
mj = mascot(s, "mascot_joy", 6.67, 5.45, 3.2, name="!!mascot")
fp = box(s, 4.42, 5.95, 4.5, 0.72, fill=C["indigo"], kind="pill", name="formula")
shape_text(fp, "Скелет + мышцы = движение!", 19, "FFFFFF", FONT_BLACK, margins=(0.1, 0))
bevel(fp, w=0.05, h=0.02)
INFO = [(0.6, 1.95, "bone", "Скелет", "206 костей. Опора и защита тела", C["violet"]),
        (8.83, 1.95, "gear", "Суставы", "Подвижные соединения: сгибаемся и поворачиваемся", C["mint"]),
        (0.6, 4.3, "muscle", "Мышцы", "Больше 600. Приводят кости в движение", C["coral"]),
        (8.83, 4.3, "chair", "Осанка", "Прямая спина — здоровое тело", C["sky"])]
tl = timeline(s)
tl.begin([fx(cc, "zoom", 700), fx(mj, "bounce", 1000, delay=200)])
step = []
for i, (x, y, key, hd, tx, col) in enumerate(INFO):
    c = card(s, x, y, 3.9, 2.05, name="info card %d" % (i + 1))
    ic, ii = icon_circle(s, key, x + 0.22, y + 0.22, 0.8, col, name="info%d" % (i + 1))
    bevel(ic, w=0.06, h=0.025)
    h1 = text(s, x + 1.2, y + 0.3, 2.65, 0.6, hd, 24, col if col != C["sun"] else "C98A00", FONT_BLACK, name="info head %d" % (i + 1))
    t1 = text(s, x + 0.25, y + 1.12, 3.45, 0.85, tx, 16, C["ink"], FONT, True, name="info text %d" % (i + 1))
    step += [fx(c, "pop", 600, delay=250 * i), fx(ic, "pop", 600, delay=250 * i), fx(ii, "pop", 600, delay=250 * i),
             fx(h1, "fade", 400, delay=250 * i + 200), fx(t1, "fade", 400, delay=250 * i + 200)]
tl.then(step)
tl.then([fx(fp, "pop", 600, sound="win")])
tl.apply()
set_transition(s, "honeycomb", 1800)
notes(s, "Инфографика «Что мы узнали»: скелет — 206 костей, опора и защита тела; суставы — подвижные соединения костей; "
         "мышцы — больше 600, приводят кости в движение; осанка — правильное положение тела. "
         "Скелет и мышцы вместе — опорно-двигательная система: «Скелет + мышцы = движение!»")

# ================================================================ SLIDE 27 — keep healthy
s = S[27]
bg(s, "bg_light.jpg")
kicker(s, "СОВЕТЫ КОСТИКА", C["mint"])
title(s, "Крепкие кости и сильные мышцы")
home_btn(s)
fd = picture(s, img("food"), 0.6, 1.9, name="food", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(5.0, 3.75), descr="Молоко, сыр, творог, рыба и другие полезные продукты")
sp = picture(s, img("sport"), 5.85, 1.9, name="sport", rounded=0.3, border="FFFFFF", border_w=0.07, shadow_on=True,
             crop_to=(6.88, 3.75), descr="Дети занимаются спортом в парке")
f1 = card(s, 0.6, 5.85, 5.0, 1.0, name="food tip")
fi = emoji(s, "milk", 0.78, 6.05, 0.6, name="food tip icon")
ft = text(s, 1.55, 5.85, 3.9, 1.0, "Ешь молоко, творог, сыр и рыбу — в них кальций для костей", 15, C["ink"], FONT, True,
          anchor="m", name="food tip text")
f2 = card(s, 5.85, 5.85, 6.88, 1.0, name="sport tip")
si = emoji(s, "run", 6.03, 6.05, 0.6, name="sport tip icon")
st = text(s, 6.8, 5.85, 5.8, 1.0, "Двигайся: зарядка, прогулки, спорт. И высыпайся — 9–10 часов!", 15, C["ink"], FONT, True,
          anchor="m", name="sport tip text")
tl = timeline(s)
tl.begin([fx(fd, "zoom", 700), fx(sp, "zoom", 700, delay=200)])
tl.click([fx(f1, "float_up", 500), fx(fi, "float_up", 500), fx(ft, "float_up", 500)])
tl.click([fx(f2, "float_up", 500), fx(si, "float_up", 500), fx(st, "float_up", 500)])
tl.apply()
set_transition(s, "pan", 1300, dir="u")
notes(s, "Как сделать кости крепкими, а мышцы сильными? Правильно питаться: молоко, творог, сыр, рыба содержат кальций. "
         "Много двигаться: зарядка, прогулки, спорт. Высыпаться: младшим школьникам нужно 9–10 часов сна. И следить за осанкой!")

# ================================================================ SLIDE 28 — reflection ladder
s = S[28]
bg(s, "bg_dark.jpg")
kicker(s, "РЕФЛЕКСИЯ", C["sun"], C["ink"])
title(s, "Лесенка успеха", color="FFFFFF")
home_btn(s)
sub = text(s, 0.6, 1.62, 5.1, 0.45, "Нажми на ступеньку, где ты сейчас", 17, "D9D2FF", FONT, True, name="ladder hint")
STEPS = [(1.0, 4.6, 2.45, C["coral"], "Мне было трудно", "Не страшно! Повтори дома — и всё получится", "mascot_shrug", "pop"),
         (4.87, 3.7, 3.35, C["sun"], "Есть вопросы", "Хорошо! Спроси учителя — и станешь знатоком", "mascot_think", "pop"),
         (8.74, 2.8, 4.25, C["mint"], "Всё понятно! Могу объяснить другу", "Супер! Ты настоящий знаток скелета!", "mascot_joy", "win")]
tl = timeline(s)
for i, (x, y, h, col, lab, msg, mkey, snd) in enumerate(STEPS):
    w = 3.6
    st_ = box(s, x, y, w, h, fill=col, radius=0.2, name="step %d" % (i + 1))
    bevel(st_, w=0.1, h=0.04)
    shadow(st_, alpha=35)
    tc = C["ink"] if col == C["sun"] else "FFFFFF"
    shape_text(st_, [[(lab, {"face": FONT_BLACK, "size": 18})]], 18, tc, FONT_BLACK, anchor="t", margins=(0.2, 0.18), check=False)
    kit.check_fit("step label", lab, 18, w - 0.4, 0.8, FONT_BLACK)
    ms = text(s, x + 0.2, y + 0.92, w - 0.4, 0.6, msg, 15, tc, FONT, True, name="step msg %d" % (i + 1))
    mm = mascot(s, mkey, x + w / 2, y + 0.02, 2.0, name="step mascot %d" % (i + 1))
    face = emoji(s, ["confused", "think", "grin"][i], x + w / 2 - 0.4, y + h - 0.95, 0.8, name="step face %d" % (i + 1))
    tl.trigger(st_, [fx(mm, "bounce", 900, sound=snd), fx(ms, "fade", 500, delay=300)])
tl.apply()
set_transition(s, "glitter", 1600, dir="l", pattern="hexagon")
notes(s, "Рефлексия «Лесенка успеха». Каждый ученик решает, на какой ступеньке он сейчас: "
         "«Мне было трудно», «Есть вопросы» или «Всё понятно! Могу объяснить другу». "
         "Нажмите на ступеньку — на неё запрыгнет Костик и скажет ободряющие слова. Можно попросить детей поднять руку у своей ступеньки.")

# ================================================================ SLIDE 29 — finish the phrase
s = S[29]
bg(s, "bg_light.jpg")
kicker(s, "РЕФЛЕКСИЯ", C["violet"])
title(s, "Продолжи фразу")
home_btn(s)
PH = [("bulb", "Сегодня на уроке я узнал(а)…", C["sky"]), ("star", "Больше всего мне понравилось…", C["coral"]),
      ("muscle", "Я буду беречь свою осанку, потому что…", C["mint"])]
tl = timeline(s)
step = []
for i, (key, t, col) in enumerate(PH):
    x = 0.6 + i * 4.115
    c = box(s, x, 2.0, 3.9, 3.2, fill="FFFFFF", radius=0.35, name="phrase %d" % (i + 1))
    c.line.color.rgb = rgb(col)
    c.line.width = E(0.05)
    shadow(c, alpha=18)
    ic, ii = icon_circle(s, key, x + 0.3, 2.3, 1.0, col, name="phrase%d" % (i + 1))
    bevel(ic, w=0.07, h=0.03)
    tt = text(s, x + 0.3, 3.5, 3.3, 1.5, t, 21, C["ink"], FONT_BLACK, name="phrase text %d" % (i + 1))
    star = emoji(s, "star", x + 2.85, 1.75, 0.85, name="phrase star %d" % (i + 1))
    step += [fx(c, "pop", 600, delay=200 * i), fx(ic, "pop", 600, delay=200 * i), fx(ii, "pop", 600, delay=200 * i),
             fx(tt, "fade", 400, delay=200 * i + 250)]
    tl_star = (c, star)
    PH[i] = (key, t, col, c, star)
bot = text(s, 0.6, 5.55, 12.13, 0.5, "Ответил — нажми на карточку и получи звезду от Костика!", 18, C["indigo"], FONT_BLACK,
           align="c", name="phrase hint")
tl.begin(step)
tl.then([fx(bot, "fade", 500)])
for key, t, col, c, star in PH:
    tl.trigger(c, [fx(star, "spin_in", 700, sound="correct")])
tl.apply()
set_transition(s, "pageCurlDouble", 1600)
notes(s, "Продолжите фразу. Дети по желанию заканчивают одну из фраз. После ответа нажмите на карточку — Костик дарит звезду.")

# ================================================================ SLIDE 30 — thanks
s = S[30]
bg(s, "bg_dark.jpg")
g1 = box(s, 8.05, 0.95, 5.0, 5.0, fill=None, kind="oval", name="glow ring")
fill_alpha(g1, "FFFFFF", 9)
ttl = title(s, "", x=0.75, y=1.6, w=7.6, h=2.4)
tf = ttl.text_frame
for i, (line, col) in enumerate([("Спасибо", "FFFFFF"), ("за урок!", C["sun"])]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.line_spacing = 0.95
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = line
    kit._style_run(r, 68, col, FONT_BLACK, False)
text_3d(ttl, extrusion_color="1A1450", depth=0.07)
sub = text(s, 0.75, 4.15, 7.0, 0.9, "Берегите осанку и будьте здоровы!", 24, "E4DEFF", FONT, True, name="thanks sub")
au = text(s, 0.75, 5.5, 6.0, 0.9, [[("Шелешко А.И.", {"size": 20, "bold": True, "color": "FFFFFF"})],
                                    [("Группа П-31", {"size": 16, "color": "D9D2FF"})]], name="thanks author")
mt = mascot(s, "mascot_wave", 10.55, 6.95, 5.6, name="!!mascot")
e1 = emoji(s, "party", 7.6, 0.8, 0.8, name="float party")
e2 = emoji(s, "star", 12.3, 5.8, 0.6, name="float star")
e3 = emoji(s, "bone", 8.2, 5.6, 0.7, name="float bone")
tl = timeline(s)
tl.begin([fx(ttl, "pop", 800, sound="win"), fx(g1, "zoom", 900), fx(mt, "bounce", 1100, delay=200)])
tl.then([fx(sub, "float_up", 600), fx(e1, "spin_in", 700), fx(e2, "spin_in", 700, delay=200), fx(e3, "spin_in", 700, delay=350)])
tl.then([fx(au, "fade", 500)])
tl.then([fx(mt, "bob", 1600, dy="-0.02")])
tl.apply()
set_transition(s, "prestige", 1800)
notes(s, "Спасибо за урок! Костик прощается с ребятами. Напомните: берегите осанку, больше двигайтесь и правильно питайтесь.")

# ================================================================ SLIDE 31 — sources & tools
s = S[31]
bg(s, "bg_light.jpg")
kicker(s, "ИСТОЧНИКИ И ИНСТРУМЕНТЫ", C["indigo"])
title(s, "Над уроком работали")
home_btn(s)
lc = card(s, 0.6, 1.9, 5.6, 4.85, name="sources card")
text(s, 0.9, 2.1, 5.0, 0.5, "Источники", 22, C["ink"], FONT_BLACK, name="sources head")
src1 = text(s, 0.9, 2.7, 5.1, 1.15, "Плешаков А.А. Окружающий мир. 3 класс. Учебник, часть 1. Тема «Опора тела и движение»", 15,
            C["ink"], FONT, False, name="source book")
src2 = text(s, 0.9, 3.95, 5.1, 0.5, [[("Видеоэкскурсия: ", {"bold": True}), ("youtu.be/6C_RWeZtCNg", {"color": C["violet"], "bold": True})]],
            15, name="source video")
link_url(src2, VIDEO_URL)
src3 = text(s, 0.9, 4.55, 5.1, 0.5, [[("Онлайн-игра: ", {"bold": True}), (GAME_URL.replace("https://", ""), {"color": C["violet"], "bold": True})]],
            15, name="source game")
link_url(src3, GAME_URL)
src4 = text(s, 0.9, 5.75, 5.1, 0.8, "Шрифт Nunito (лицензия SIL OFL), иконки Noto Emoji (Google)", 13, C["muted"], FONT, True,
            name="source fonts")
text(s, 6.55, 1.9, 6.0, 0.5, "Нейросети в проекте", 22, C["ink"], FONT_BLACK, name="ai head")
AI = [("robot", "Claude (Anthropic)", "сценарий урока, тексты, вопросы, вёрстка презентации, онлайн-игра", C["violet"]),
      ("sparkles", "Nano Banana 2 (Google) в Higgsfield", "иллюстрации и маскот Костик", C["coral"]),
      ("film", "MiniMax Hailuo", "видео для физминутки", C["mint"])]
for i, (key, nm, what, col) in enumerate(AI):
    y = 2.55 + i * 1.45
    c = card(s, 6.55, y, 6.18, 1.28, name="ai %d" % (i + 1))
    ic, ii = icon_circle(s, key, 6.72, y + 0.2, 0.88, col, name="ai%d" % (i + 1))
    text(s, 7.8, y + 0.12, 4.8, 0.45, nm, 17, C["ink"], FONT_BLACK, name="ai name %d" % (i + 1))
    text(s, 7.8, y + 0.55, 4.8, 0.65, what, 14, C["muted"], FONT, True, name="ai what %d" % (i + 1))
set_transition(s, "fade", 900)
notes(s, "Источники и инструменты. Нейросети, которые использовались при подготовке проекта: Claude — сценарий, тексты, задания, "
         "вёрстка и онлайн-игра; Nano Banana 2 (через Higgsfield) — иллюстрации; MiniMax Hailuo — видео для физминутки.")

prs.save(OUT)
print("saved", OUT)
print("placeholders:", sorted(set(PLACEHOLDERS)))
print("fit warnings:")
for w in kit.WARNINGS:
    print("  ", w)
