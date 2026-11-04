// «Использование и охрана полезных ископаемых» — Человек и мир, 3 класс.
// pptxgenjs builds the slides; tools/anim.py then adds animations, triggers, sounds, links and audio.
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const pptxgen = require('pptxgenjs');
const AS = require('./assets');

const ROOT = AS.ROOT;
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, 'deck', 'config.json'), 'utf8'));
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', 'fizminutka_timeline.json'), 'utf8'));

const W = 13.333, H = 7.5, F = 'Arial';
const NAVY = '1D2B53', INK = '1D2B53', MUTED = '5B6B8C', WHITE = 'FFFFFF';
const GREEN = '1FA463', GREEN_D = '17834F', GREEN_L = 'E3F6EA';
const AMBER = 'F5A524', AMBER_D = 'B86E00', AMBER_L = 'FFF1D6';
const CORAL = 'EF5B5B', CORAL_D = 'C23B3B', CORAL_L = 'FDE5E5';
const FLAME = 'F2643D', FLAME_L = 'FDE6DE', STEEL = '4A7BD0', STEEL_L = 'E2EBFA', SAND = 'D9971A', SAND_L = 'FBF0D2';
const SKY_L = 'EAF4FF';

// slide numbers
const S = { TITLE: 1, ORG: 2, AKT: 3, TOPIC: 4, PROB: 5, GOAL: 6, HUB: 7, ST1: 8, ST2: 9, ST3: 10, ST4: 11, ST5: 12, ST6: 13, ST7: 14, ST8: 15,
  VIDEO: 16, FIZ: 17, T1: 18, T2A: 19, T2B: 20, T3A: 21, T3B: 22, Q1: 23, Q2: 24, Q3: 25, Q4: 26, ONLINE: 27, SUM: 28, REF: 29, HW: 30, END: 31 };

const sh = () => ({ type: 'outer', color: '1D2B53', blur: 10, offset: 3, angle: 90, opacity: 0.14 });
const mg = (l, t, r, b) => [l, r, b, t]; // pptxgenjs order is [left, right, bottom, top], points

class Anim {
  constructor(n) { this.spec = { slide: n, auto: [], clicks: [], triggers: [], audio: [], links: [] }; this.base = 0; }
  auto(obj, fx, delay, dur = 500, extra = {}) { this.spec.auto.push({ obj, fx, delay: Math.round(delay + (extra.abs ? 0 : this.base)), dur, ...extra }); }
  click(list) { this.spec.clicks.push(list.map((e, i) => ({ dur: 500, delay: 0, ...e, node: i ? 'withEffect' : undefined }))); }
  trig(on, list) { this.spec.triggers.push({ on, fx: list.map((e) => ({ dur: 500, delay: 0, ...e })) }); }
  link(obj, slide) { this.spec.links.push({ obj, slide }); }
  url(obj, url) { this.spec.links.push({ obj, url }); }
}

let P, BG, A = {};
const specs = [];
let prevBg = null;

// ---------- primitives ----------
function txt(s, name, text, o) {
  s.addText(text, Object.assign({ fontFace: F, margin: 0, valign: 'top', isTextBox: true, objectName: name, color: INK, fontSize: 18 }, o));
  return name;
}
function box(s, name, o) {
  const { text = '', ...rest } = o;
  const opts = Object.assign({
    shape: P.ShapeType.roundRect, fontFace: F, objectName: name, rectRadius: 0.16, fill: { color: WHITE }, line: { type: 'none' },
    margin: mg(14, 8, 14, 8), valign: 'middle', color: INK, fontSize: 18,
  }, rest);
  // no native shape shadows: phone and web viewers draw them wrongly; white cards get a hairline border instead
  delete opts.shadow;
  if (!rest.line && opts.fill && opts.fill.color === WHITE && (opts.fill.transparency || 0) < 50) opts.line = { color: 'D3DDEB', width: 1 };
  s.addText(text, opts);
  return name;
}
function hit(s, name, x, y, w, h) { // invisible click area for triggers
  s.addShape(P.ShapeType.rect, { x, y, w, h, fill: { color: WHITE, transparency: 100 }, line: { type: 'none' }, objectName: name });
  return name;
}
function pic(s, name, file, x, y, w, h, alt) {
  s.addImage({ path: file, x, y, w, h, objectName: name, altText: alt || name });
  return name;
}
function setBg(s, a, key) {
  if (prevBg && prevBg !== key) { // cross-fade from the previous background, no slide transition needed
    s.background = { path: BG[prevBg] };
    pic(s, 'bgfade', BG[key], 0, 0, W, H, 'Фон');
    a.auto('bgfade', 'fade', 0, 800, { abs: true });
    a.base = 250;
  } else {
    s.background = { path: BG[key] };
  }
  prevBg = key;
}
function header(s, a, kicker, title, dark = false, o = {}) {
  txt(s, 'kicker', kicker, { x: 0.6, y: 0.36, w: o.kw || 9.5, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: dark ? 'FFD27A' : AMBER_D });
  txt(s, 'title', title, { x: 0.6, y: 0.64, w: o.tw || 10.2, h: 0.78, fontSize: o.ts || 34, bold: true, color: dark ? WHITE : NAVY, valign: 'middle' });
  a.auto('kicker', 'float', 0, 500);
  a.auto('title', 'float', 90, 650);
}
function homeBtn(s, a) {
  pic(s, 'home', A.home, 0.3, 6.84, 0.44, 0.44, 'На главную страницу экскурсии');
  a.link('home', S.HUB);
  a.auto('home', 'fade', 900, 400);
}
function mapBtn(s, a) {
  box(s, 'mapbtn', { x: 10.95, y: 0.44, w: 1.8, h: 0.56, rectRadius: 0.28, fill: { color: NAVY }, shadow: sh(), text: 'На карту', color: WHITE, bold: true, fontSize: 15, align: 'left', margin: mg(46, 0, 6, 0) });
  pic(s, 'mapicon', A.mapIcon, 11.07, 0.53, 0.38, 0.38, 'Карта');
  a.link('mapbtn', S.HUB); a.link('mapicon', S.HUB);
  a.auto('mapbtn', 'fade', 500, 400); a.auto('mapicon', 'fade', 500, 400);
}
function notes(s, t) { s.addNotes(t); }
function bubbleTail(s, name, x, y, flip = false, color = WHITE) {
  s.addShape(P.ShapeType.rtTriangle, { x, y, w: 0.42, h: 0.42, fill: { color }, line: { type: 'none' }, flipH: flip, objectName: name });
  return name;
}

// ---------- images ----------
const IMG = AS.IMG;
function exists(f) { return fs.existsSync(f); }
function rawPath(code) { for (const e of ['.png', '.jpg', '.jpeg', '.webp']) { const f = path.join(IMG, 'raw', code + e); if (exists(f)) return f; } return null; }
const LABELS = CFG.labels;
async function ch(code) { const f = path.join(IMG, 'cut', code + '.png'); return exists(f) ? f : AS.placeholder(code, LABELS[code] || '', 'char'); }
async function sq(code) { const f = path.join(IMG, 'cut', code + '.png'); return exists(f) ? f : AS.placeholder(code, LABELS[code] || '', 'sq'); }
async function med(code) { return AS.medallion(await sq(code), code); }
async function scene(code, aspect = 43) {
  const r = rawPath(code);
  if (r) return AS.framed(r, code, aspect);
  return AS.placeholder(code, LABELS[code] || '', aspect === 169 ? 'scene169' : 'scene43');
}
const SC = (aspect) => (aspect === 169 ? 9 / 16 : 3 / 4);

// =====================================================================================
async function build() {
  P = new pptxgen();
  P.layout = 'LAYOUT_WIDE';
  P.title = 'Использование и охрана полезных ископаемых';
  P.subject = 'Человек и мир, 3 класс';
  P.author = 'Урок-путешествие';
  P.theme = { headFontFace: F, bodyFontFace: F };

  BG = await AS.backgrounds();
  BG.title = rawPath('TITLE');
  if (BG.title) { const tj = path.join(AS.OUT, 'title_bg.jpg'); await sharp(BG.title).flatten({ background: '#ffffff' }).jpeg({ quality: 90 }).toFile(tj); BG.title = tj; }
  BG.hub = BG.dark;
  const hubSrc = rawPath('HUB') || rawPath('B1');
  if (hubSrc) {
    const out = path.join(AS.OUT, 'bg_hub.jpg');
    const ov = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="2667" height="1500"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#14204A" stop-opacity="0.80"/><stop offset="0.75" stop-color="#14204A" stop-opacity="0.55"/><stop offset="1" stop-color="#14204A" stop-opacity="0.30"/></linearGradient></defs><rect width="2667" height="1500" fill="url(#g)"/></svg>`);
    await sharp(hubSrc).resize(2667, 1500, { fit: 'cover' }).composite([{ input: ov }]).jpeg({ quality: 88 }).toFile(out);
    BG.hub = out;
  }
  BG.fiz = BG.green;
  if (rawPath('B11')) {
    const out = path.join(AS.OUT, 'bg_fiz.jpg');
    await sharp(rawPath('B11')).flop().resize(2667, 1500, { fit: 'cover' }).jpeg({ quality: 88 }).toFile(out);
    BG.fiz = out;
  }

  A.home = await AS.badge('FaHouse', '#1D2B53');
  A.mapIcon = await AS.badge('FaMapLocationDot', 'none', '#FFFFFF', { pad: 0.08 });
  A.speaker = await AS.badge('FaVolumeHigh', '#1D2B53');

  await slideTitle(); await slideOrg(); await slideAkt(); await slideTopic(); await slideProblem(); await slideGoals();
  await slideHub(); await slideSt1(); await slideSt2(); await slideSt3(); await slideSt4(); await slideSt5(); await slideSt6(); await slideSt7(); await slideSt8();
  await slideVideo(); await slideFiz();
  await slideT1(); await slideT2(0); await slideT2(1); await slideT3(0); await slideT3(1);
  for (let i = 0; i < 4; i++) await slideQuiz(i);
  await slideOnline(); await slideSummary(); await slideReflect(); await slideHomework(); await slideEnd();

  const out = path.join(ROOT, 'build', 'deck_raw.pptx');
  await P.writeFile({ fileName: out });
  fs.writeFileSync(path.join(ROOT, 'build', 'anim_spec.json'), JSON.stringify(specs, null, 1));
  console.log('slides', specs.length, '->', out);
}

function newSlide(n, section) {
  if (section) P.addSection({ title: section });
  const s = P.addSlide({ sectionTitle: currentSection });
  const a = new Anim(n);
  specs.push(a.spec);
  return [s, a];
}
let currentSection = '';
function section(t) { currentSection = t; P.addSection({ title: t }); }

// ---------------- 1. Титульный ----------------
async function slideTitle() {
  section('Цель и задачи урока');
  const [s, a] = newSlide(S.TITLE);
  if (BG.title) { s.background = { path: BG.title }; prevBg = 'title'; } else setBg(s, a, 'dark');
  box(s, 'card', { x: 0.55, y: 0.6, w: 4.3, h: 4.25, rectRadius: 0.28, fill: { color: WHITE, transparency: 8 }, shadow: { type: 'outer', color: '1D2B53', blur: 18, offset: 4, angle: 90, opacity: 0.22 } });
  txt(s, 'kicker', 'ЧЕЛОВЕК И МИР · 3 КЛАСС', { x: 0.9, y: 0.95, w: 3.7, h: 0.3, fontSize: 12, bold: true, charSpacing: 2, color: AMBER_D });
  txt(s, 'title', 'Использование и охрана полезных ископаемых', { x: 0.9, y: 1.32, w: 3.75, h: 1.95, fontSize: 30, bold: true, color: NAVY, valign: 'top', lineSpacingMultiple: 0.95 });
  txt(s, 'sub', 'Урок-путешествие в кладовые Земли', { x: 0.9, y: 3.42, w: 3.7, h: 0.75, fontSize: 18, color: GREEN_D, bold: true, valign: 'top' });
  txt(s, 'guide', 'Ведёт экскурсию юный геолог Мира', { x: 0.9, y: 4.12, w: 3.7, h: 0.4, fontSize: 14, color: MUTED, italic: true });
  a.auto('card', 'zoom', 100, 700, { sound: 'sparkle' });
  a.auto('kicker', 'float', 450, 500); a.auto('title', 'float', 550, 700); a.auto('sub', 'float', 800, 600); a.auto('guide', 'fade', 1050, 600);
  notes(s, 'Организационный момент (2 мин).\n— Ребята, сегодня мы отправимся в небольшое путешествие. Но путешествовать будем не по городам и странам, а в глубины нашей планеты. Там находятся природные богатства, без которых жизнь современного человека была бы совсем другой.\n— Проверьте, всё ли готово к уроку. Настраиваемся на работу и начинаем.');
}

// ---------------- 2. Оргмомент ----------------
async function slideOrg() {
  const [s, a] = newSlide(S.ORG);
  setBg(s, a, 'dark');
  pic(s, 'girl', await ch('C1'), 0.45, 1.55, 3.6, 5.4, 'Юный геолог Мира машет рукой');
  box(s, 'bubble', { x: 4.1, y: 0.75, w: 8.6, h: 2.2, rectRadius: 0.3, text: [
    { text: 'Привет! Я — Мира, юный геолог.', options: { bold: true, fontSize: 24, color: NAVY, breakLine: true } },
    { text: 'Сегодня мы отправимся в путешествие… в глубины нашей планеты! Там спрятаны природные богатства.', options: { fontSize: 20, color: INK } },
  ], margin: mg(26, 14, 26, 14), valign: 'middle' });
  bubbleTail(s, 'tail', 3.78, 2.35, true);
  txt(s, 'readyT', 'Всё готово к уроку?', { x: 4.15, y: 3.35, w: 2.6, h: 0.45, fontSize: 18, bold: true, color: 'FFD27A' });
  const items = [['FaBookOpen', 'Учебник'], ['FaPencil', 'Тетрадь и ручка'], ['FaFaceSmile', 'Хорошее настроение']];
  for (let i = 0; i < items.length; i++) {
    const y = 3.95 + i * 0.95;
    pic(s, `ri${i}`, await AS.badge(items[i][0], '#F5A524'), 4.15, y, 0.62, 0.62);
    txt(s, `rt${i}`, items[i][1], { x: 4.9, y: y, w: 2.0, h: 0.62, fontSize: 17, bold: true, color: WHITE, valign: 'middle' });
  }
  pic(s, 'b1', await scene('B1'), 7.85, 3.15, 4.95, 4.95 * 0.75, 'Разрез Земли с полезными ископаемыми');
  a.auto('girl', 'zoom', 0, 700); a.auto('girl', 'pulse', 3200, 700);
  a.auto('bubble', 'pop', 300, 600, { sound: 'pop' }); a.auto('tail', 'fade', 600, 300);
  a.auto('b1', 'zoom', 700, 800);
  a.auto('readyT', 'float', 1100, 500);
  for (let i = 0; i < 3; i++) { a.auto(`ri${i}`, 'pop', 1300 + i * 220, 450); a.auto(`rt${i}`, 'float', 1350 + i * 220, 450); }
  homeBtn(s, a);
  notes(s, '— Сегодня нашим гидом будет юный геолог Мира. Геологи изучают, что находится в глубинах Земли.\n— Посмотрите на картинку справа: под землёй много слоёв, и в них спрятаны природные богатства.\n— Проверьте, всё ли готово к уроку.');
}

// ---------------- 3. Актуализация ----------------
async function slideAkt() {
  const [s, a] = newSlide(S.AKT);
  setBg(s, a, 'light');
  header(s, a, 'РАЗМИНКА ДЛЯ УМА', 'Из чего сделаны эти предметы?');
  const items = [['FaHouseChimney', 'Дом', 'кирпич, бетон, стекло', '#F2643D', 'O1'], ['FaRoad', 'Дорога', 'песок, щебень, асфальт', '#5B6B8C', 'O2'], ['FaWineBottle', 'Бутылка', 'стекло — из песка', '#1FA463', 'O3'],
    ['FaGears', 'Деталь', 'металл — из руды', '#4A7BD0', 'O4'], ['FaCar', 'Машина', 'металл, стекло, бензин', '#EF5B5B', 'O5'], ['GiBrickWall', 'Кирпич', 'глина', '#D9971A', 'O6']];
  const cw = 2.85, chh = 2.55, gx = 0.22, gy = 0.22, x0 = 0.6, y0 = 1.62;
  for (let i = 0; i < 6; i++) {
    const x = x0 + (i % 3) * (cw + gx), y = y0 + Math.floor(i / 3) * (chh + gy);
    box(s, `c${i}`, { x, y, w: cw, h: chh, rectRadius: 0.2 });
    const objPath = path.join(IMG, 'cut', items[i][4] + '.png');
    if (exists(objPath)) pic(s, `im${i}`, objPath, x + (cw - 1.5) / 2, y + 0.12, 1.5, 1.5, items[i][1]);
    else pic(s, `im${i}`, await AS.badge(items[i][0], items[i][3], '#FFFFFF', { pad: 0.22 }), x + (cw - 1.35) / 2, y + 0.2, 1.35, 1.35, items[i][1]);
    txt(s, `nm${i}`, items[i][1], { x, y: y + 1.64, w: cw, h: 0.36, fontSize: 19, bold: true, align: 'center', color: NAVY });
    box(s, `an${i}`, { x: x + 0.14, y: y + 2.04, w: cw - 0.28, h: 0.4, rectRadius: 0.2, fill: { color: GREEN }, shadow: undefined, text: items[i][2], color: WHITE, bold: true, fontSize: 14, align: 'center', margin: mg(4, 0, 4, 0) });
    hit(s, `h${i}`, x, y, cw, chh);
    a.auto(`c${i}`, 'float', 250 + i * 110, 500); a.auto(`im${i}`, 'zoom', 330 + i * 110, 550); a.auto(`nm${i}`, 'fade', 380 + i * 110, 400);
    a.trig(`h${i}`, [{ obj: `an${i}`, fx: 'pop', dur: 450, sound: 'pop' }, { obj: `im${i}`, fx: 'pulse', dur: 500 }]);
  }
  pic(s, 'girl', await ch('C3'), 10.15, 2.95, 2.9, 4.35, 'Мира думает');
  box(s, 'hint', { x: 9.9, y: 1.62, w: 2.85, h: 1.12, rectRadius: 0.2, fill: { color: AMBER_L }, text: 'Нажми на предмет — узнаешь ответ!', fontSize: 16, bold: true, color: AMBER_D, align: 'center' });
  box(s, 'concl', { x: 9.9, y: 1.62, w: 2.85, h: 1.12, rectRadius: 0.2, fill: { color: NAVY }, text: 'Всё это человек берёт из природы — из земных недр!', fontSize: 15, bold: true, color: WHITE, align: 'center' });
  a.auto('girl', 'zoom', 700, 700); a.auto('hint', 'pop', 1000, 500);
  a.click([{ obj: 'hint', fx: 'fadeOut', dur: 300 }, { obj: 'concl', fx: 'pop', dur: 500, delay: 200, sound: 'magic' }]);
  homeBtn(s, a);
  notes(s, 'Актуализация знаний (5 мин).\nНажимайте на карточки предметов — появится, из чего они сделаны. Щелчок по свободному месту покажет вывод.\n— Из чего сделаны эти предметы?\n— Откуда человек получает материалы для их изготовления?\n— Какие природные богатства вы уже знаете? Что находится под землёй?\nПредполагаемые ответы: песок, глина, уголь, нефть, газ, различные руды, камни.\n— Многие вещества и материалы человек получает из природы. Некоторые из них добывают из земных недр. Такие природные богатства называют полезными ископаемыми.');
}

// ---------------- 4. Тема урока ----------------
async function slideTopic() {
  const [s, a] = newSlide(S.TOPIC);
  setBg(s, a, 'dark');
  txt(s, 'kicker', 'ТЕМА УРОКА', { x: 1.5, y: 0.9, w: 10.33, h: 0.35, fontSize: 15, bold: true, charSpacing: 4, color: 'FFD27A', align: 'center' });
  txt(s, 'title', 'Использование и охрана полезных ископаемых', { x: 1.0, y: 1.3, w: 11.33, h: 1.75, fontSize: 44, bold: true, color: WHITE, align: 'center', valign: 'middle' });
  box(s, 'def', { x: 2.0, y: 3.3, w: 9.33, h: 1.45, rectRadius: 0.25, text: [
    { text: 'Природные богатства, которые человек добывает из земных недр, называют ', options: { color: INK } },
    { text: 'полезными ископаемыми', options: { color: AMBER_D, bold: true } }, { text: '.', options: { color: INK } }],
    fontSize: 22, align: 'center', margin: mg(24, 10, 24, 10) });
  const codes = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8'];
  const d = 1.25, gap = 0.2, x0 = (W - (8 * d + 7 * gap)) / 2;
  for (let i = 0; i < 8; i++) {
    pic(s, `m${i}`, await med(codes[i]), x0 + i * (d + gap), 5.2, d, d, LABELS[codes[i]]);
    a.auto(`m${i}`, 'pop', 1500 + i * 120, 450);
  }
  a.auto('kicker', 'fade', 0, 500); a.auto('title', 'zoom', 150, 900, { sound: 'magic' });
  a.auto('def', 'float', 900, 700);
  homeBtn(s, a);
  notes(s, 'На доске появляется тема: «Использование и охрана полезных ископаемых».\n— Внизу — полезные ископаемые, с которыми мы сегодня познакомимся: уголь, нефть, газ, железная руда, песок, глина, известняк, каменная соль.');
}

// ---------------- 5. Проблема ----------------
async function slideProblem() {
  const [s, a] = newSlide(S.PROB);
  setBg(s, a, 'light');
  header(s, a, 'ПОДУМАЕМ', 'Как связаны эти картинки?');
  const iw = 5.0, ih = iw * 0.75;
  pic(s, 'q', await scene('B2'), 0.45, 1.45, iw, ih, 'Карьер');
  pic(s, 'c', await scene('B3'), 7.88, 1.45, iw, ih, 'Город');
  box(s, 'ql', { x: 0.85, y: 4.35, w: 1.6, h: 0.5, rectRadius: 0.25, fill: { color: SAND }, text: 'Карьер', color: WHITE, bold: true, fontSize: 16, align: 'center' });
  box(s, 'cl', { x: 8.28, y: 4.35, w: 1.5, h: 0.5, rectRadius: 0.25, fill: { color: STEEL }, text: 'Город', color: WHITE, bold: true, fontSize: 16, align: 'center' });
  pic(s, 'arrow', await AS.arrow('arrow_amber.png', '#F5A524'), 5.75, 2.75, 1.0, 0.6);
  pic(s, 'qm', await AS.badge('FaQuestion', '#1D2B53'), 6.6, 2.6, 0.9, 0.9);
  box(s, 'ban', { x: 0.6, y: 5.3, w: 12.13, h: 0.78, rectRadius: 0.39, fill: { color: NAVY }, text: 'Можно ли использовать полезные ископаемые сколько угодно?', color: WHITE, bold: true, fontSize: 22, align: 'center' });
  const ans = [['Нет!', 1.4], ['Их запасы могут закончиться', 4.4], ['Их нужно беречь!', 3.0]];
  let x = (W - (1.4 + 4.4 + 3.0 + 0.5)) / 2;
  ans.forEach((t, i) => { box(s, `a${i}`, { x, y: 6.3, w: t[1], h: 0.6, rectRadius: 0.3, fill: { color: GREEN_L }, line: { color: GREEN, width: 1.5 }, shadow: undefined, text: t[0], color: GREEN_D, bold: true, fontSize: 18, align: 'center' }); x += t[1] + 0.25; });
  // positions: re-place a0..a2 horizontally
  a.auto('q', 'zoom', 200, 700); a.auto('ql', 'pop', 700, 400);
  a.auto('c', 'zoom', 400, 700); a.auto('cl', 'pop', 900, 400);
  a.auto('arrow', 'wipeL', 1100, 500); a.auto('qm', 'pop', 1400, 450); a.auto('qm', 'pulse', 2100, 600);
  a.click([{ obj: 'ban', fx: 'float', dur: 600, sound: 'pop' }]);
  a.click([{ obj: 'a0', fx: 'pop', dur: 450, sound: 'correct' }, { obj: 'a1', fx: 'pop', dur: 450, delay: 250 }, { obj: 'a2', fx: 'pop', dur: 450, delay: 500 }]);
  homeBtn(s, a);
  notes(s, 'Постановка учебной проблемы (3 мин).\n— Посмотрите на эти изображения: карьер, где добывают полезные ископаемые, и современный город. Как они связаны между собой?\n— Действительно, многие вещи вокруг нас появились благодаря полезным ископаемым. Но возникает вопрос (щелчок): можно ли использовать полезные ископаемые сколько угодно?\nЩелчок — ответы: нет; их запасы могут закончиться; их нужно беречь.\n— Сегодня мы выясним, как человек использует полезные ископаемые и что нужно делать, чтобы сохранить природные богатства.');
}

// ---------------- 6. Цель и задачи ----------------
async function slideGoals() {
  const [s, a] = newSlide(S.GOAL);
  setBg(s, a, 'light');
  header(s, a, 'НАШ МАРШРУТ', 'Цель и задачи урока');
  box(s, 'goal', { x: 0.6, y: 1.6, w: 9.15, h: 1.5, rectRadius: 0.22, fill: { color: AMBER_L }, shadow: sh(), text: [
    { text: 'ЦЕЛЬ', options: { bold: true, fontSize: 14, color: AMBER_D, charSpacing: 2, breakLine: true } },
    { text: 'Узнать, как человек использует полезные ископаемые и почему их нужно беречь', options: { bold: true, fontSize: 21, color: NAVY } }],
    margin: mg(100, 10, 18, 10) });
  pic(s, 'goalic', await AS.badge('FaBullseye', '#F5A524'), 0.85, 1.92, 0.86, 0.86);
  const tasks = ['Узнать, что такое полезные ископаемые', 'Познакомиться с их видами', 'Выяснить, где их использует человек', 'Понять, почему и как их беречь'];
  const icons = ['FaMagnifyingGlass', 'FaLayerGroup', 'FaIndustry', 'FaHandHoldingHeart'];
  const cw = 4.45, chh = 1.62;
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + (i % 2) * (cw + 0.25), y = 3.4 + Math.floor(i / 2) * (chh + 0.25);
    box(s, `t${i}`, { x, y, w: cw, h: chh, rectRadius: 0.2, text: tasks[i], fontSize: 19, bold: true, color: NAVY, margin: mg(96, 8, 16, 8) });
    pic(s, `n${i}`, await AS.numBadge(i + 1, '#1FA463'), x + 0.22, y + (chh - 0.62) / 2 - 0.12, 0.62, 0.62);
    pic(s, `i${i}`, await AS.badge(icons[i], '#E3F6EA', '#17834F'), x + 0.36, y + chh / 2 + 0.12, 0.38, 0.38);
    a.auto(`t${i}`, 'float', 650 + i * 140, 500); a.auto(`n${i}`, 'pop', 750 + i * 140, 400); a.auto(`i${i}`, 'fade', 800 + i * 140, 400);
  }
  pic(s, 'girl', await ch('C4'), 9.95, 2.0, 3.25, 4.88, 'Мира готова к путешествию');
  a.auto('goal', 'float', 250, 600); a.auto('goalic', 'pop', 450, 450, { sound: 'pop' });
  a.auto('girl', 'zoom', 500, 700);
  homeBtn(s, a);
  notes(s, '— Сегодня мы выясним, как человек использует полезные ископаемые и что нужно делать, чтобы сохранить природные богатства.\nЗадачи урока: узнать, что такое полезные ископаемые; познакомиться с их видами; выяснить, где их использует человек; понять, почему и как их нужно беречь.');
}

// ---------------- 7. Главная страница экскурсии ----------------
const STATIONS = [
  [S.ST1, 'Что это такое?', 'FaMagnifyingGlass', '#F5A524'], [S.ST2, 'Три группы', 'FaSitemap', '#7A5AF8'], [S.ST3, 'Горючие', 'FaFire', '#F2643D'],
  [S.ST4, 'Рудные', 'GiMetalBar', '#4A7BD0'], [S.ST5, 'Нерудные', 'GiBrickWall', '#D9971A'], [S.ST6, 'Как добывают?', 'GiMining', '#5B6B8C'],
  [S.ST7, 'Почему беречь?', 'FaHourglassHalf', '#EF5B5B'], [S.ST8, 'Как охранять?', 'FaRecycle', '#1FA463']];
async function slideHub() {
  section('Виртуальная экскурсия');
  const [s, a] = newSlide(S.HUB);
  setBg(s, a, 'hub');
  header(s, a, 'ВИРТУАЛЬНАЯ ЭКСКУРСИЯ', 'Карта подземного музея', true);
  txt(s, 'sub', 'Выбери станцию — и в путь!', { x: 0.6, y: 1.38, w: 6, h: 0.4, fontSize: 18, color: 'D6E2FF' });
  a.auto('sub', 'fade', 250, 500);
  const cw = 3.0, chh = 0.95, gx = 0.25, gy = 0.24, x0 = 0.6, y0 = 2.0;
  const pos = [[0, 0], [1, 0], [2, 0], [2, 1], [1, 1], [0, 1], [0, 2], [1, 2]];
  // route behind the chips (px at 100 px/in)
  const pts = pos.map(([c, r]) => [Math.round((x0 + c * (cw + gx) + cw / 2) * 100), Math.round((y0 + r * (chh + gy) + chh / 2) * 100)]);
  const rf = await AS.route(pts, 1100, 560, 'route.png');
  pic(s, 'route', rf, 0, 0, 11.0, 5.6, 'Маршрут');
  a.auto('route', 'wipeL', 300, 1400);
  for (let i = 0; i < 8; i++) {
    const [c, r] = pos[i];
    const x = x0 + c * (cw + gx), y = y0 + r * (chh + gy);
    const [sl, label, ic, col] = STATIONS[i];
    box(s, `ch${i}`, { x, y, w: cw, h: chh, rectRadius: 0.475, text: [
      { text: `Станция ${i + 1}`, options: { fontSize: 12, color: MUTED, bold: true, breakLine: true } },
      { text: label, options: { fontSize: 16, color: NAVY, bold: true } }], margin: mg(64, 4, 6, 4),
      shadow: { type: 'outer', color: '0B1230', blur: 12, offset: 3, angle: 90, opacity: 0.35 } });
    pic(s, `ic${i}`, await AS.badge(ic, col), x + 0.13, y + 0.135, 0.68, 0.68, label);
    a.link(`ch${i}`, sl); a.link(`ic${i}`, sl);
    a.auto(`ch${i}`, 'pop', 450 + i * 150, 450, i === 0 ? { sound: 'sparkle' } : {}); a.auto(`ic${i}`, 'zoom', 520 + i * 150, 400);
  }
  pic(s, 'girl', await ch('C1'), 10.35, 1.6, 2.65, 3.98, 'Мира приглашает на экскурсию');
  a.auto('girl', 'zoom', 900, 700);
  txt(s, 'secT', 'РАЗДЕЛЫ УРОКА', { x: 0.6, y: 5.82, w: 4, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: 'FFD27A' });
  const secs = [['Видеоэкскурсия', 'FaCirclePlay', S.VIDEO, 2.62], ['Физкультминутка', 'FaPersonRunning', S.FIZ, 2.74], ['Задания', 'FaPuzzlePiece', S.T1, 1.78],
    ['Интерактив онлайн', 'FaGlobe', S.ONLINE, 2.97], ['Итоги', 'FaFlagCheckered', S.SUM, 1.44]];
  let x = 0.6;
  for (let i = 0; i < secs.length; i++) {
    const [t, ic, sl, w] = secs[i];
    box(s, `sb${i}`, { x, y: 6.2, w, h: 0.66, rectRadius: 0.33, fill: { color: WHITE, transparency: 86 }, line: { color: 'C9D6FF', width: 1.25 }, shadow: undefined,
      text: t, color: WHITE, bold: true, fontSize: 15, align: 'left', margin: mg(38, 0, 4, 0) });
    pic(s, `si${i}`, await AS.badge(ic, 'none', '#FFD27A', { pad: 0.1 }), x + 0.14, 6.36, 0.34, 0.34, t);
    a.link(`sb${i}`, sl); a.link(`si${i}`, sl);
    a.auto(`sb${i}`, 'float', 1700 + i * 90, 450); a.auto(`si${i}`, 'fade', 1750 + i * 90, 400);
    x += w + 0.15;
  }
  a.auto('secT', 'fade', 1650, 400);
  notes(s, 'Главная страница виртуальной экскурсии. Нажмите на станцию, чтобы перейти к ней. На каждой станции кнопка «На карту» возвращает сюда.\nВнизу — быстрые переходы к разделам урока: видеоэкскурсия, физкультминутка, задания, интерактив онлайн, итоги.\nЕсли щёлкнуть по свободному месту, презентация пойдёт по порядку: станция 1, 2, 3…\nКнопка с домиком в левом нижнем углу на всех слайдах ведёт на эту страницу.');
}

function stationHead(s, a, n, title, o = {}) {
  header(s, a, `СТАНЦИЯ ${n}`, title, false, { tw: 10.0, ...o });
  mapBtn(s, a);
}

// ---------------- 8. Станция 1 ----------------
async function slideSt1() {
  const [s, a] = newSlide(S.ST1);
  setBg(s, a, 'light');
  stationHead(s, a, 1, 'Что такое полезные ископаемые?');
  box(s, 'def', { x: 0.6, y: 1.65, w: 8.2, h: 1.95, rectRadius: 0.22, fill: { color: AMBER_L }, text: [
    { text: 'Полезные ископаемые', options: { bold: true, color: AMBER_D } },
    { text: ' — это природные вещества, которые находятся в земной коре и используются человеком.', options: { color: NAVY } }],
    fontSize: 24, margin: mg(110, 10, 22, 10) });
  pic(s, 'defic', await AS.badge('FaGem', '#F5A524'), 0.9, 2.17, 0.9, 0.9);
  const cards = [['FaLayerGroup', '#4A7BD0', 'Где они лежат?', 'Близко к поверхности Земли или глубоко под землёй.'],
    ['FaIndustry', '#1FA463', 'Как их используют?', 'Песок и глину — почти без изменения. Другие полезные ископаемые перерабатывают.']];
  for (let i = 0; i < 2; i++) {
    const x = 0.6 + i * 4.2;
    box(s, `c${i}`, { x, y: 3.9, w: 4.0, h: 2.95, rectRadius: 0.22, text: [
      { text: cards[i][2], options: { bold: true, fontSize: 21, color: NAVY, breakLine: true } },
      { text: cards[i][3], options: { fontSize: 18, color: INK } }], valign: 'top', margin: mg(20, 92, 20, 12) });
    pic(s, `ci${i}`, await AS.badge(cards[i][0], cards[i][1]), x + 0.28, 4.12, 0.72, 0.72);
    a.auto(`c${i}`, 'float', 900 + i * 180, 550); a.auto(`ci${i}`, 'pop', 1000 + i * 180, 400);
  }
  pic(s, 'girl', await ch('C1'), 9.3, 1.95, 3.35, 5.03, 'Мира объясняет');
  a.auto('def', 'float', 300, 650); a.auto('defic', 'pop', 500, 450, { sound: 'pop' });
  a.auto('girl', 'zoom', 600, 700);
  notes(s, 'Изучение нового материала.\n— Полезные ископаемые — это природные вещества, которые находятся в земной коре и используются человеком. Они могут находиться близко к поверхности Земли или глубоко под землёй.\n— Некоторые полезные ископаемые человек использует почти без изменения. Например, песок и глину. Другие перерабатывают, чтобы получить необходимые материалы и вещества.');
}

// ---------------- 9. Станция 2: три группы ----------------
const GROUPS = [
  { t: 'Горючие', col: FLAME, light: FLAME_L, ic: 'FaFire', icol: '#F2643D', m: ['M1', 'M2', 'M3'], ex: ['каменный уголь', 'нефть', 'природный газ'], sl: S.ST3 },
  { t: 'Рудные', col: STEEL, light: STEEL_L, ic: 'GiMetalBar', icol: '#4A7BD0', m: ['M4'], ex: ['железная руда', 'руды цветных металлов'], sl: S.ST4 },
  { t: 'Нерудные', col: SAND, light: SAND_L, ic: 'GiBrickWall', icol: '#D9971A', m: ['M5', 'M6', 'M7', 'M8'], ex: ['песок', 'глина', 'известняк', 'каменная соль'], sl: S.ST5 }];
async function slideSt2() {
  const [s, a] = newSlide(S.ST2);
  setBg(s, a, 'light');
  stationHead(s, a, 2, 'Три группы полезных ископаемых');
  box(s, 'root', { x: 4.27, y: 1.55, w: 4.8, h: 0.78, rectRadius: 0.39, fill: { color: NAVY }, text: 'Полезные ископаемые', color: WHITE, bold: true, fontSize: 23, align: 'center' });
  pic(s, 'tree', await AS.treeLines('tree.png', '#9DB0CF'), 1.0, 2.33, 11.33, 0.78);
  const cw = 3.95, gap = 0.24;
  for (let i = 0; i < 3; i++) {
    const g = GROUPS[i], x = 0.6 + i * (cw + gap), y = 3.1;
    box(s, `g${i}`, { x, y, w: cw, h: 3.85, rectRadius: 0.24, fill: { color: WHITE }, line: { color: g.col, width: 2 }, text: '' });
    pic(s, `gi${i}`, await AS.badge(g.ic, g.icol), x + 0.25, y + 0.22, 0.72, 0.72);
    txt(s, `gt${i}`, g.t, { x: x + 1.1, y: y + 0.22, w: cw - 1.3, h: 0.72, fontSize: 26, bold: true, color: g.col, valign: 'middle' });
    const n = g.m.length, md = 0.82, mx0 = x + (cw - (n * md + (n - 1) * 0.08)) / 2;
    for (let k = 0; k < n; k++) pic(s, `gm${i}_${k}`, await med(g.m[k]), mx0 + k * (md + 0.08), y + 1.08, md, md, g.ex[k] || '');
    txt(s, `ge${i}`, g.ex.map((e, k) => ({ text: e, options: { bullet: { code: '25CF' }, breakLine: k < g.ex.length - 1 } })), { x: x + 0.35, y: y + 2.0, w: cw - 0.6, h: 1.25, fontSize: 17, color: INK, paraSpaceAfter: 2 });
    box(s, `go${i}`, { x: x + 0.35, y: y + 3.22, w: cw - 0.7, h: 0.45, rectRadius: 0.22, fill: { color: g.light }, shadow: undefined, text: 'Подробнее →', color: g.col, bold: true, fontSize: 14, align: 'center' });
    for (const o of [`g${i}`, `gi${i}`, `gt${i}`, `ge${i}`, `go${i}`]) a.link(o, g.sl);
    for (let k = 0; k < n; k++) a.link(`gm${i}_${k}`, g.sl);
    const d0 = 1000 + i * 250;
    a.auto(`g${i}`, 'float', d0, 550); a.auto(`gi${i}`, 'pop', d0 + 150, 400); a.auto(`gt${i}`, 'fade', d0 + 150, 400);
    for (let k = 0; k < n; k++) a.auto(`gm${i}_${k}`, 'zoom', d0 + 250 + k * 80, 400);
    a.auto(`ge${i}`, 'fade', d0 + 350, 400); a.auto(`go${i}`, 'fade', d0 + 450, 400);
  }
  a.auto('root', 'zoom', 250, 600, { sound: 'pop' }); a.auto('tree', 'wipeU', 700, 500);
  notes(s, 'Учитель составляет на доске схему: полезные ископаемые → горючие, рудные, нерудные.\nКарточка группы — ссылка: щёлкните по ней, чтобы перейти на станцию этой группы.');
}

// station with minerals on the left, scene + fact on the right
async function mineralCards(s, a, codes, names, x0, y, w, h, gap, delay) {
  for (let i = 0; i < codes.length; i++) {
    const x = x0 + i * (w + gap);
    box(s, `m${i}`, { x, y, w, h, rectRadius: 0.2 });
    const isz = Math.min(w - 0.3, h - 0.65);
    pic(s, `mi${i}`, await sq(codes[i]), x + (w - isz) / 2, y + 0.1, isz, isz, names[i]);
    txt(s, `mn${i}`, names[i], { x: x + 0.05, y: y + h - 0.5, w: w - 0.1, h: 0.4, fontSize: names[i].length > 13 ? 16 : 18, bold: true, align: 'center', color: NAVY, valign: 'middle' });
    a.auto(`m${i}`, 'float', delay + i * 140, 500); a.auto(`mi${i}`, 'zoom', delay + 80 + i * 140, 550); a.auto(`mn${i}`, 'fade', delay + 120 + i * 140, 400);
  }
}
async function sceneFact(s, a, code, fact, fallback) {
  const r = rawPath(code);
  if (r || !fallback) {
    pic(s, 'scene', await scene(code), 8.75, 1.6, 4.0, 3.0, LABELS[code]);
  } else {
    pic(s, 'scene', await ch(fallback), 9.8, 1.4, 2.13, 3.2, 'Мира');
  }
  a.auto('scene', 'zoom', 500, 700);
  box(s, 'fact', { x: 8.75, y: 4.82, w: 4.0, h: 2.1, rectRadius: 0.2, fill: { color: SKY_L }, shadow: undefined, text: [
    { text: 'ЭТО ИНТЕРЕСНО', options: { bold: true, fontSize: 12, color: STEEL, charSpacing: 2, breakLine: true } },
    { text: fact, options: { fontSize: 17, color: NAVY, bold: true } }], valign: 'top', margin: mg(70, 12, 14, 10) });
  pic(s, 'facti', await AS.badge('FaLightbulb', '#4A7BD0'), 8.95, 5.02, 0.52, 0.52);
}

// ---------------- 10. Станция 3: горючие ----------------
async function slideSt3() {
  const [s, a] = newSlide(S.ST3);
  setBg(s, a, 'light');
  stationHead(s, a, 3, 'Горючие полезные ископаемые');
  await mineralCards(s, a, ['M1', 'M2', 'M3'], ['Каменный уголь', 'Нефть', 'Природный газ'], 0.6, 1.6, 2.5, 2.75, 0.15, 300);
  box(s, 'q', { x: 0.6, y: 4.6, w: 7.8, h: 0.7, rectRadius: 0.35, fill: { color: FLAME_L }, shadow: undefined, text: 'Почему их называют горючими?', color: FLAME, bold: true, fontSize: 20, margin: mg(62, 0, 12, 0) });
  pic(s, 'qi', await AS.badge('FaQuestion', '#F2643D'), 0.72, 4.69, 0.52, 0.52);
  box(s, 'ans', { x: 0.6, y: 5.42, w: 7.8, h: 0.7, rectRadius: 0.35, fill: { color: GREEN_L }, shadow: undefined, text: 'Они горят! При сгорании выделяется тепло.', color: GREEN_D, bold: true, fontSize: 19, margin: mg(62, 0, 12, 0) });
  pic(s, 'ansi', await AS.badge('FaFire', '#1FA463'), 0.72, 5.51, 0.52, 0.52);
  box(s, 'use', { x: 0.6, y: 6.24, w: 7.8, h: 0.7, rectRadius: 0.35, fill: { color: NAVY }, shadow: undefined, text: 'Это топливо и сырьё для разных веществ.', color: WHITE, bold: true, fontSize: 18, margin: mg(62, 0, 12, 0) });
  pic(s, 'usei', await AS.badge('FaGasPump', '#F5A524'), 0.72, 6.33, 0.52, 0.52);
  await sceneFact(s, a, 'B4', 'Из нефти делают бензин, пластмассу и даже краски!', 'C3');
  a.auto('q', 'float', 900, 500); a.auto('qi', 'pop', 1000, 400);
  a.auto('fact', 'float', 1100, 500); a.auto('facti', 'pop', 1200, 400);
  a.click([{ obj: 'ans', fx: 'float', dur: 500, sound: 'correct' }, { obj: 'ansi', fx: 'pop', dur: 400, delay: 100 }]);
  a.click([{ obj: 'use', fx: 'float', dur: 500, sound: 'pop' }, { obj: 'usei', fx: 'pop', dur: 400, delay: 100 }]);
  notes(s, 'Горючие полезные ископаемые: каменный уголь, нефть, природный газ.\n— Почему их называют горючими? (щелчок) — Они горят. При их сгорании выделяется тепло.\n— (щелчок) Их используют как топливо и как сырьё для производства различных веществ.');
}

// ---------------- 11. Станция 4: рудные ----------------
async function slideSt4() {
  const [s, a] = newSlide(S.ST4);
  setBg(s, a, 'light');
  stationHead(s, a, 4, 'Рудные полезные ископаемые');
  // flow: руда -> металл -> вещи
  box(s, 'f0', { x: 0.6, y: 1.6, w: 2.35, h: 2.75, rectRadius: 0.2 });
  pic(s, 'f0i', await sq('M4'), 0.8, 1.7, 1.95, 1.95, 'Железная руда');
  txt(s, 'f0t', 'Железная руда', { x: 0.6, y: 3.82, w: 2.35, h: 0.4, fontSize: 17, bold: true, align: 'center', color: NAVY });
  pic(s, 'ar0', await AS.arrow('arrow_steel.png', '#4A7BD0'), 3.05, 2.65, 0.75, 0.45);
  box(s, 'f1', { x: 3.9, y: 1.6, w: 2.0, h: 2.75, rectRadius: 0.2, fill: { color: STEEL_L }, text: 'Металл', fontSize: 19, bold: true, color: STEEL, align: 'center', valign: 'bottom', margin: mg(4, 4, 4, 16) });
  pic(s, 'f1i', await AS.badge('GiMetalBar', '#4A7BD0'), 4.3, 1.9, 1.2, 1.2, 'Металл');
  pic(s, 'ar1', await AS.arrow('arrow_steel.png', '#4A7BD0'), 6.0, 2.65, 0.75, 0.45);
  box(s, 'f2', { x: 6.85, y: 1.6, w: 1.55, h: 2.75, rectRadius: 0.2, fill: { color: GREEN_L }, text: 'Вещи', fontSize: 19, bold: true, color: GREEN_D, align: 'center', valign: 'bottom', margin: mg(4, 4, 4, 16) });
  pic(s, 'f2i', await AS.badge('FaWrench', '#1FA463'), 7.18, 1.95, 0.9, 0.9, 'Вещи');
  box(s, 'q', { x: 0.6, y: 4.6, w: 7.8, h: 0.7, rectRadius: 0.35, fill: { color: STEEL_L }, shadow: undefined, text: 'Где мы встречаем металлические изделия?', color: STEEL, bold: true, fontSize: 19, margin: mg(62, 0, 12, 0) });
  pic(s, 'qi', await AS.badge('FaQuestion', '#4A7BD0'), 0.72, 4.69, 0.52, 0.52);
  const prod = [['FaCar', 'машины'], ['FaBicycle', 'велосипеды'], ['FaUtensils', 'посуда'], ['FaHammer', 'инструменты'], ['FaGears', 'детали']];
  const pw = 1.48, pg = 0.1;
  for (let i = 0; i < prod.length; i++) {
    const x = 0.6 + i * (pw + pg);
    box(s, `p${i}`, { x, y: 5.45, w: pw, h: 1.48, rectRadius: 0.18, text: prod[i][1], fontSize: 14, bold: true, color: NAVY, align: 'center', valign: 'bottom', margin: mg(1, 2, 1, 8) });
    pic(s, `pi${i}`, await AS.badge(prod[i][0], '#E2EBFA', '#4A7BD0'), x + (pw - 0.72) / 2, 5.58, 0.72, 0.72, prod[i][1]);
  }
  await sceneFact(s, a, 'B5', 'Из руд цветных металлов получают медь и алюминий.', 'C4');
  const order = ['f0', 'f0i', 'f0t', 'ar0', 'f1', 'f1i', 'ar1', 'f2', 'f2i'];
  order.forEach((o, i) => a.auto(o, o.startsWith('ar') ? 'wipeL' : (o.endsWith('i') ? 'zoom' : 'float'), 300 + i * 110, 450));
  a.auto('q', 'float', 1300, 500); a.auto('qi', 'pop', 1400, 400);
  a.auto('fact', 'float', 1500, 500); a.auto('facti', 'pop', 1600, 400);
  a.click(prod.flatMap((p, i) => [{ obj: `p${i}`, fx: 'pop', dur: 420, delay: i * 160, sound: i === 0 ? 'pop' : undefined }, { obj: `pi${i}`, fx: 'zoom', dur: 400, delay: i * 160 + 60 }]));
  notes(s, 'Рудные полезные ископаемые: железная руда, некоторые руды цветных металлов.\n— Из руд получают металлы. А где мы встречаем металлические изделия?\nЩелчок — ответы: машины, велосипеды, посуда, инструменты, детали различных предметов.');
}

// ---------------- 12. Станция 5: нерудные ----------------
async function slideSt5() {
  const [s, a] = newSlide(S.ST5);
  setBg(s, a, 'light');
  stationHead(s, a, 5, 'Нерудные полезные ископаемые');
  const codes = ['M5', 'M6', 'M7', 'M8'], names = ['Песок', 'Глина', 'Известняк', 'Каменная соль'];
  const uses = ['стекло, строительство', 'кирпич, посуда, плитка', 'строительные материалы', 'в пищу и для заводов'];
  const w = 1.83, gap = 0.16;
  await mineralCards(s, a, codes, names, 0.6, 1.6, w, 2.6, gap, 300);
  for (let i = 0; i < 4; i++) {
    const x = 0.6 + i * (w + gap);
    box(s, `u${i}`, { x, y: 4.32, w, h: 0.98, rectRadius: 0.18, fill: { color: SAND_L }, line: { color: SAND, width: 1.5 }, shadow: undefined, text: uses[i], fontSize: 15, bold: true, color: '8A5A00', align: 'center', margin: mg(6, 2, 6, 2) });
    hit(s, `h${i}`, x, 1.6, w, 2.6);
    a.trig(`h${i}`, [{ obj: `u${i}`, fx: 'pop', dur: 450, sound: 'pop' }, { obj: `mi${i}`, fx: 'pulse', dur: 500 }]);
  }
  box(s, 'q', { x: 0.6, y: 5.55, w: 7.8, h: 1.35, rectRadius: 0.22, fill: { color: AMBER_L }, shadow: undefined, text: [
    { text: 'Где человек использует песок? А глину? А известняк?', options: { bold: true, fontSize: 19, color: NAVY, breakLine: true } },
    { text: 'Нажми на камень — проверь себя!', options: { fontSize: 16, color: AMBER_D, bold: true } }], margin: mg(70, 8, 14, 8) });
  pic(s, 'qi', await AS.badge('FaHandPointer' in require('react-icons/fa6') ? 'FaHandPointer' : 'FaQuestion', '#F5A524'), 0.78, 5.95, 0.55, 0.55);
  await sceneFact(s, a, 'B6', 'Обычное стекло делают из песка: его плавят в огромных печах.', 'C3');
  a.auto('q', 'float', 1000, 500); a.auto('qi', 'pop', 1100, 400);
  a.auto('fact', 'float', 1200, 500); a.auto('facti', 'pop', 1300, 400);
  notes(s, 'Нерудные полезные ископаемые: песок, глина, известняк, каменная соль.\nНажимайте на карточки — под ними появится, где их используют.\n— Где человек может использовать песок? — В строительстве, для изготовления стекла, для других строительных материалов.\n— А глину? — Для изготовления кирпича, керамических изделий.\n— Известняк? — В строительстве, для получения строительных материалов.');
}

// ---------------- 13. Станция 6: как добывают ----------------
async function slideSt6() {
  const [s, a] = newSlide(S.ST6);
  setBg(s, a, 'light');
  stationHead(s, a, 6, 'Как добывают полезные ископаемые?');
  pic(s, 'img', await scene('B1'), 0.45, 1.5, 6.4, 4.8, 'Карьер, шахта и нефтяная вышка на разрезе Земли');
  const cards = [['GiMining', '#D9971A', 'Карьер', 'если лежат близко к поверхности'], ['GiMineWagon', '#5B6B8C', 'Шахта', 'если лежат глубоко под землёй'], ['GiOilPump', '#1D2B53', 'Буровая вышка', 'чтобы добыть нефть и газ']];
  for (let i = 0; i < 3; i++) {
    const y = 1.6 + i * 1.5;
    box(s, `c${i}`, { x: 7.15, y, w: 5.6, h: 1.34, rectRadius: 0.2, text: [
      { text: cards[i][2], options: { bold: true, fontSize: 20, color: NAVY, breakLine: true } },
      { text: cards[i][3], options: { fontSize: 16, color: INK } }], margin: mg(84, 6, 12, 6) });
    pic(s, `ci${i}`, await AS.badge(cards[i][0], cards[i][1]), 7.33, y + 0.3, 0.74, 0.74);
  }
  box(s, 'fact', { x: 0.6, y: 6.25, w: 12.15, h: 0.7, rectRadius: 0.35, fill: { color: SKY_L }, shadow: undefined, text: [
    { text: 'Это интересно: ', options: { bold: true, color: STEEL } }, { text: 'в Беларуси калийную соль добывают в глубоких шахтах возле Солигорска.', options: { color: NAVY, bold: true } }],
    fontSize: 17, margin: mg(62, 0, 12, 0) });
  pic(s, 'facti', await AS.badge('FaLightbulb', '#4A7BD0'), 0.72, 6.34, 0.52, 0.52);
  a.auto('img', 'zoom', 300, 800);
  for (let i = 0; i < 3; i++) a.click([{ obj: `c${i}`, fx: 'float', dur: 500, sound: 'pop' }, { obj: `ci${i}`, fx: 'pop', dur: 400, delay: 100 }]);
  a.click([{ obj: 'fact', fx: 'float', dur: 500, sound: 'magic' }, { obj: 'facti', fx: 'pop', dur: 400, delay: 100 }]);
  notes(s, 'Полезные ископаемые могут находиться близко к поверхности Земли или глубоко под землёй.\nЩелчками открывайте: карьер — если залегают близко к поверхности; шахта — если глубоко; буровая вышка — для нефти и газа.\nПоследний щелчок — интересный факт о Беларуси.');
}

// ---------------- 14. Станция 7: почему беречь ----------------
async function slideSt7() {
  const [s, a] = newSlide(S.ST7);
  setBg(s, a, 'light');
  stationHead(s, a, 7, 'Почему ископаемые нужно беречь?');
  const hasForest = !!rawPath('B8');
  pic(s, 'img', await scene(hasForest ? 'B8' : 'B2'), 0.45, 1.5, 4.7, 3.525, hasForest ? 'Древний лес' : 'Карьер');
  box(s, 'cap', { x: 0.8, y: 4.3, w: 3.1, h: 0.5, rectRadius: 0.25, fill: { color: GREEN_D }, shadow: undefined, text: hasForest ? 'Миллионы лет назад…' : 'Запасы не бесконечны!', color: WHITE, bold: true, fontSize: 15, align: 'center' });
  box(s, 'q', { x: 5.35, y: 1.6, w: 7.4, h: 1.3, rectRadius: 0.22, fill: { color: CORAL_L }, shadow: undefined, text: 'Что будет, если добывать полезные ископаемые и совсем не думать о будущем?', fontSize: 19, bold: true, color: NAVY, margin: mg(78, 8, 16, 8) });
  pic(s, 'qi', await AS.badge('FaQuestion', '#EF5B5B'), 5.55, 1.94, 0.62, 0.62);
  const cons = ['Запасы уменьшатся', 'Некоторые закончатся', 'Разрушится почва', 'Изменится природа', 'Появится загрязнение'];
  for (let i = 0; i < 5; i++) {
    const x = 5.35 + (i % 2) * 3.78, y = 3.1 + Math.floor(i / 2) * 0.74;
    box(s, `k${i}`, { x, y, w: 3.62, h: 0.6, rectRadius: 0.3, fill: { color: WHITE }, line: { color: CORAL, width: 1.5 }, text: cons[i], fontSize: 16, bold: true, color: CORAL_D, align: 'left', margin: mg(40, 0, 4, 0) });
    pic(s, `ki${i}`, await AS.badge('FaXmark', '#EF5B5B'), x + 0.1, y + 0.11, 0.38, 0.38);
    a.click([{ obj: `k${i}`, fx: 'pop', dur: 450, sound: 'pop' }, { obj: `ki${i}`, fx: 'zoom', dur: 400, delay: 80 }]);
  }
  box(s, 'concl', { x: 0.6, y: 5.75, w: 12.15, h: 1.2, rectRadius: 0.22, fill: { color: GREEN }, text: [
    { text: 'Полезные ископаемые образовывались миллионы лет. Их запасы не бесконечны! ', options: { bold: true } },
    { text: 'Использовать их нужно разумно и бережно.', options: { bold: true, color: 'FFF4C2' } }], color: WHITE, fontSize: 20, margin: mg(84, 6, 18, 6) });
  pic(s, 'conci', await AS.badge('FaHourglassHalf', '#FFFFFF', '#1FA463'), 0.85, 6.0, 0.7, 0.7);
  a.auto('img', 'zoom', 300, 800); a.auto('cap', 'pop', 900, 400);
  a.auto('q', 'float', 600, 550); a.auto('qi', 'pop', 750, 400);
  a.click([{ obj: 'concl', fx: 'float', dur: 600, sound: 'bell' }, { obj: 'conci', fx: 'pop', dur: 450, delay: 150 }]);
  notes(s, 'Проблемный вопрос (5 мин).\n— Представьте, что человек добывает нефть, уголь, газ, руду и другие полезные ископаемые, но совершенно не думает о будущем. К чему это может привести?\nКаждый щелчок открывает один ответ детей: запасы могут уменьшиться; некоторые полезные ископаемые могут закончиться; разрушится почва; изменится природа; появится загрязнение.\nПоследний щелчок — вывод: большинство полезных ископаемых образовывалось в природе очень долго. Поэтому их запасы не бесконечны. Человек должен использовать их разумно и бережно.\nНа картинке — древний лес: из таких растений за миллионы лет образовался каменный уголь.');
}

// ---------------- 15. Станция 8: как охранять ----------------
async function slideSt8() {
  const [s, a] = newSlide(S.ST8);
  setBg(s, a, 'light');
  stationHead(s, a, 8, 'Как охранять полезные ископаемые?');
  const rules = [['FaLightbulb', 'Не трать зря', 'выключай свет и приборы, когда они не нужны'], ['FaBolt', 'Береги топливо и энергию', 'меньше энергии впустую — меньше сжигают топлива'],
    ['FaArrowsRotate', 'Используй вещи повторно', 'если вещь ещё может послужить'], ['FaRecycle', 'Сдавай отходы на переработку', 'бумагу, металл и стекло можно использовать снова'],
    ['FaSeedling', 'Восстанавливай природу', 'после добычи сажают лес и делают озёра']];
  for (let i = 0; i < 5; i++) {
    const y = 1.6 + i * 1.07;
    box(s, `r${i}`, { x: 0.6, y, w: 7.1, h: 0.95, rectRadius: 0.2, text: [
      { text: rules[i][1], options: { bold: true, fontSize: 19, color: NAVY, breakLine: true } },
      { text: rules[i][2], options: { fontSize: 15, color: MUTED } }], margin: mg(122, 4, 12, 4) });
    pic(s, `rn${i}`, await AS.numBadge(i + 1, '#1FA463'), 0.75, y + 0.2, 0.55, 0.55);
    pic(s, `ri${i}`, await AS.badge(rules[i][0], '#E3F6EA', '#17834F'), 1.38, y + 0.2, 0.55, 0.55);
    a.click([{ obj: `r${i}`, fx: 'float', dur: 500, sound: 'pop' }, { obj: `rn${i}`, fx: 'pop', dur: 400, delay: 80 }, { obj: `ri${i}`, fx: 'zoom', dur: 400, delay: 140 }]);
  }
  pic(s, 'img', await scene('B9'), 7.85, 1.5, 5.05, 3.79, 'Карьер превратили в парк с озером');
  box(s, 'cap', { x: 8.1, y: 5.45, w: 4.6, h: 1.4, rectRadius: 0.2, fill: { color: GREEN_L }, shadow: undefined, text: [
    { text: 'Был карьер — стал парк!', options: { bold: true, fontSize: 19, color: GREEN_D, breakLine: true } },
    { text: 'После добычи нарушенные земли нужно восстанавливать.', options: { fontSize: 15, color: NAVY } }], margin: mg(16, 6, 12, 6) });
  a.auto('img', 'zoom', 300, 800); a.auto('cap', 'float', 800, 500);
  notes(s, 'Охрана полезных ископаемых (5 мин).\n— Что значит «охранять полезные ископаемые»? (выслушать предположения)\nЩелчками открывайте правила:\n1. Не расходовать полезные ископаемые без необходимости. Например, не оставлять включённый свет и электроприборы.\n2. Экономить топливо и энергию. Чем меньше энергии мы тратим напрасно, тем меньше топлива требуется для её производства.\n3. Повторно использовать материалы.\n4. Перерабатывать отходы: бумагу, металл, стекло. Это уменьшает количество новых природных ресурсов.\n5. Бережно относиться к окружающей среде при добыче. После разработки месторождений необходимо восстанавливать нарушенные территории.');
}

// ---------------- 16. Видеоэкскурсия (пустой) ----------------
async function slideVideo() {
  section('Видеоэкскурсия');
  const [s, a] = newSlide(S.VIDEO);
  setBg(s, a, 'dark');
  txt(s, 'kicker', 'ВИДЕОЭКСКУРСИЯ', { x: 0.6, y: 0.36, w: 6, h: 0.3, fontSize: 13, bold: true, charSpacing: 2, color: 'FFD27A' });
  a.auto('kicker', 'fade', 0, 500);
  homeBtn(s, a);
  notes(s, 'Слайд для видеоэкскурсии. Вставьте видео: Вставка → Видео → Это устройство. Растяните его на свободное место.');
}

// ---------------- 17. Физкультминутка ----------------
async function slideFiz() {
  section('Физкультминутка с ИИ');
  const [s, a] = newSlide(S.FIZ);
  setBg(s, a, 'fiz');
  header(s, a, 'ПЕРЕРЫВ', 'Физкультминутка', false, { tw: 5.5 });
  box(s, 'ai', { x: 5.15, y: 0.78, w: 2.95, h: 0.56, rectRadius: 0.28, fill: { color: NAVY }, text: 'Озвучивает ИИ', color: WHITE, bold: true, fontSize: 15, margin: mg(44, 0, 8, 0) });
  pic(s, 'aii', await AS.badge('FaWandMagicSparkles', 'none', '#FFD27A', { pad: 0.08 }), 5.3, 0.88, 0.36, 0.36);
  box(s, 'panel', { x: 0.6, y: 1.65, w: 6.9, h: 5.3, rectRadius: 0.26, fill: { color: WHITE, transparency: 6 } });
  const icons = ['GiMining', 'FaArrowUp', 'FaArrowsRotate', 'FaArrowDown', 'FaArrowsLeftRight', 'FaHandsClapping'];
  const fa6 = require('react-icons/fa6');
  for (let i = 0; i < 6; i++) {
    const y = 1.85 + i * 0.82;
    box(s, `hl${i}`, { x: 0.78, y: y - 0.04, w: 6.54, h: 0.8, rectRadius: 0.2, fill: { color: AMBER_L }, line: { color: AMBER, width: 2 }, shadow: undefined });
    const ic = fa6[icons[i]] || icons[i].startsWith('Gi') ? icons[i] : 'FaStar';
    pic(s, `li${i}`, await AS.badge(ic, '#1FA463'), 0.95, y + 0.08, 0.56, 0.56);
    txt(s, `ln${i}`, [{ text: TL.lines[i], options: { bold: true, fontSize: 21, color: NAVY, breakLine: true } }, { text: TL.moves[i], options: { fontSize: 14, color: MUTED } }],
      { x: 1.7, y: y, w: 5.5, h: 0.72, valign: 'middle' });
  }
  box(s, 'barbg', { x: 0.95, y: 6.72, w: 6.2, h: 0.1, rectRadius: 0.05, fill: { color: 'E1E7F2' }, shadow: undefined });
  box(s, 'bar', { x: 0.95, y: 6.72, w: 6.2, h: 0.1, rectRadius: 0.05, fill: { color: AMBER }, shadow: undefined });
  // poses stacked on the right
  const poses = ['C1', 'P0', 'P1', 'P2', 'P3', 'P3m', 'P4', 'P5', 'C4'];
  const px = 7.85, py = 1.3, pw = 4.85, ph = 4.85 * 1.15;
  for (const p of poses) pic(s, `pose_${p}`, await poseImg(p), px, py, pw, ph, 'Мира показывает движение');
  pic(s, 'aud', A.speaker, 12.55, 6.75, 0.5, 0.5, 'Озвучка физкультминутки');
  a.spec.audio.push({ obj: 'aud', file: path.join(ROOT, 'build', 'fizminutka.mp3'), autoplay: true, dur: Math.round(TL.total * 1000) });
  a.auto('ai', 'pop', 300, 450); a.auto('aii', 'fade', 400, 300);
  a.auto('panel', 'float', 200, 600);
  for (let i = 0; i < 6; i++) { a.auto(`li${i}`, 'pop', 450 + i * 90, 350); a.auto(`ln${i}`, 'fade', 480 + i * 90, 350); }
  a.auto('barbg', 'fade', 900, 300);
  a.auto('bar', 'wipeL', 0, Math.round(TL.total * 1000), { abs: true });
  // timeline (absolute from slide start, audio starts at 0)
  let cur = null;
  const lineAt = {};
  for (const ev of TL.events) {
    const t = Math.round(ev.t * 1000);
    if (cur !== ev.pose) {
      a.auto(`pose_${ev.pose}`, 'appear', t, 1, { abs: true });
      if (cur) a.auto(`pose_${cur}`, 'disappear', t, 1, { abs: true });
      cur = ev.pose;
    }
    const key = `${ev.round || 0}_${ev.line}`;
    if (ev.line >= 0 && !(key in lineAt)) lineAt[key] = t;
  }
  // highlight each line while it is being read and shown
  const starts = Object.entries(lineAt).map(([k, t]) => ({ line: +k.split('_')[1], t })).sort((x, y) => x.t - y.t);
  const ends = TL.events.filter((e) => e.line < 0).map((e) => Math.round(e.t * 1000));
  starts.forEach((st, i) => {
    let end = i + 1 < starts.length ? starts[i + 1].t : null;
    const stop = ends.find((e) => e > st.t);
    if (stop && (end === null || stop < end)) end = stop;
    a.auto(`hl${st.line}`, 'fade', st.t, 200, { abs: true });
    a.auto(`hl${st.line}`, 'fadeOut', end - 200, 200, { abs: true });
  });
  if (cur) a.auto(`pose_${cur}`, 'pulse', Math.round(TL.total * 1000) - 2500, 800, { abs: true });
  notes(s, 'Физкультминутка (2 мин). Озвучка ИИ включается сама, как только открывается слайд. Мира показывает движения, текущая строчка подсвечивается. Два круга: второй — быстрее.\nМы копаем глубоко — наклоны вперёд.\nДостаём руду легко — выпрямиться, поднять руки.\nУголь, глину и песок — повороты вправо-влево.\nИз земли берём мы в срок — приседание.\nНо природу охраняем — руки в стороны.\nЗемлю нашу сохраняем! — руки вверх.\nЧтобы начать заново, вернитесь на предыдущий слайд и снова откройте этот. Значок динамика справа внизу — ручное управление звуком.\nЭта же физкультминутка есть на сайте урока.');
}
async function poseImg(code) {
  const pf = (c) => path.join(IMG, 'pose', c + '.png');
  if (code === 'P3m' && exists(pf('P3'))) {
    const out = path.join(AS.OUT, 'pose_P3m.png');
    await sharp(pf('P3')).flop().png().toFile(out);
    return out;
  }
  if (exists(pf(code))) return pf(code);
  if (code === 'P3m') {
    const src = await ch('P3');
    const out = path.join(AS.OUT, 'pose_P3m.png');
    await sharp(src).flop().png().toFile(out);
    return out;
  }
  return ch(code);
}

// ---------------- 18. Задание 1: что из чего ----------------
async function slideT1() {
  section('Задания');
  const [s, a] = newSlide(S.T1);
  setBg(s, a, 'light');
  header(s, a, 'ЗАДАНИЕ 1 · РАБОТАЕМ В ПАРАХ', 'Что из чего получают?', false, { tw: 6.6 });
  box(s, 'hint', { x: 7.4, y: 0.78, w: 5.35, h: 0.6, rectRadius: 0.3, fill: { color: AMBER_L }, shadow: undefined, text: 'Нажми на камень — проверь себя!', fontSize: 16, bold: true, color: AMBER_D, align: 'center' });
  a.auto('hint', 'pop', 400, 450);
  const rows = [['M2', 'Нефть', 'топливо (бензин), разные материалы и вещества'], ['M3', 'Природный газ', 'топливо, тепло и энергия'], ['M1', 'Каменный уголь', 'тепло и энергия, топливо'],
    ['M4', 'Железная руда', 'производство металла'], ['M5', 'Песок', 'производство стекла, строительство'], ['M6', 'Глина', 'кирпич и керамика'], ['M7', 'Известняк', 'строительство']];
  for (let i = 0; i < 7; i++) {
    const col = i < 4 ? 0 : 1, r = i < 4 ? i : i - 4;
    const x = 0.6 + col * 6.2, y = 1.68 + r * 1.32;
    box(s, `m${i}`, { x, y, w: 2.6, h: 1.12, rectRadius: 0.2, text: rows[i][1], fontSize: 17, bold: true, color: NAVY, margin: mg(72, 2, 4, 2) });
    pic(s, `mi${i}`, await sq(rows[i][0]), x + 0.08, y + 0.13, 0.86, 0.86, rows[i][1]);
    pic(s, `ar${i}`, await AS.arrow('arrow_green.png', '#1FA463'), x + 2.68, y + 0.38, 0.55, 0.33);
    box(s, `u${i}`, { x: x + 3.3, y, w: 2.65, h: 1.12, rectRadius: 0.2, fill: { color: GREEN_L }, line: { color: GREEN, width: 1.5 }, shadow: undefined, text: rows[i][2], fontSize: 15, bold: true, color: GREEN_D, margin: mg(10, 2, 8, 2) });
    hit(s, `h${i}`, x, y, 2.6, 1.12);
    a.auto(`m${i}`, 'float', 300 + i * 100, 450); a.auto(`mi${i}`, 'zoom', 360 + i * 100, 450);
    a.trig(`h${i}`, [{ obj: `ar${i}`, fx: 'wipeL', dur: 350, sound: 'correct' }, { obj: `u${i}`, fx: 'float', dur: 450, delay: 200 }, { obj: `mi${i}`, fx: 'pulse', dur: 500 }]);
  }
  box(s, 'tq', { x: 6.8, y: 5.64, w: 5.95, h: 1.3, rectRadius: 0.2, fill: { color: NAVY }, text: [
    { text: 'Какие полезные ископаемые используют как топливо?', options: { bold: true, fontSize: 17, color: WHITE } }], margin: mg(76, 4, 12, 4) });
  pic(s, 'tqi', await AS.badge('FaGasPump', '#F5A524'), 7.0, 5.97, 0.62, 0.62);
  box(s, 'ta', { x: 6.8, y: 5.64, w: 5.95, h: 1.3, rectRadius: 0.2, fill: { color: AMBER }, text: [
    { text: 'Нефть, природный газ и каменный уголь!', options: { bold: true, fontSize: 19, color: NAVY } }], margin: mg(76, 4, 12, 4) });
  pic(s, 'tai', await AS.badge('FaFire', '#1D2B53', '#FFD27A'), 7.0, 5.97, 0.62, 0.62);
  a.auto('tq', 'float', 1100, 500); a.auto('tqi', 'pop', 1200, 400);
  a.click([{ obj: 'ta', fx: 'pop', dur: 500, sound: 'correct' }, { obj: 'tai', fx: 'zoom', dur: 400, delay: 100 }]);
  notes(s, 'Практическая работа «Что из чего?» (6 мин). Учащиеся работают в парах или группах с карточками: соединить полезное ископаемое с областью применения.\nПроверка: нажимайте на карточку полезного ископаемого — появится правильный ответ.\nУточняющие вопросы: какое полезное ископаемое используется для получения металла? Что используется при изготовлении стекла? Какие полезные ископаемые человек использует как топливо? (щелчок по свободному месту — ответ)');
}

// ---------------- 19-20. Можно — нельзя ----------------
const SIT = [['Оставить свет включённым в пустой комнате', false], ['Выключить компьютер после окончания работы', true], ['Бросить металлическую банку в лесу', false],
  ['Сдать металлические отходы на переработку', true], ['Оставлять воду и электричество расходоваться без необходимости', false], ['Использовать вещи повторно, если это возможно', true],
  ['Бережно относиться к природным богатствам', true]];
async function slideT2(part) {
  const [s, a] = newSlide(part ? S.T2B : S.T2A);
  setBg(s, a, 'light');
  header(s, a, `ЗАДАНИЕ 2 · ИГРА${part ? ' (ПРОДОЛЖЕНИЕ)' : ''}`, 'Можно или нельзя?', false, { tw: 5.6 });
  box(s, 'rule', { x: 6.6, y: 0.78, w: 6.15, h: 0.6, rectRadius: 0.3, fill: { color: SKY_L }, shadow: undefined, text: 'Правильно — жми 👍   Неправильно — жми 👎', fontSize: 15, bold: true, color: NAVY, align: 'center' });
  a.auto('rule', 'pop', 400, 450);
  const items = part ? SIT.slice(4) : SIT.slice(0, 4);
  const up = await AS.badge('FaThumbsUp', '#1FA463'), down = await AS.badge('FaThumbsDown', '#EF5B5B');
  for (let i = 0; i < items.length; i++) {
    const n = (part ? 4 : 0) + i + 1, y = 1.68 + i * 1.3;
    box(s, `c${i}`, { x: 0.6, y, w: 9.45, h: 1.12, rectRadius: 0.2, text: items[i][0], fontSize: 19, bold: true, color: NAVY, margin: mg(78, 2, 150, 2) });
    pic(s, `n${i}`, await AS.numBadge(n, '#1D2B53'), 0.78, y + 0.26, 0.6, 0.6);
    pic(s, `up${i}`, up, 8.05, y + 0.16, 0.8, 0.8, 'Можно');
    pic(s, `dn${i}`, down, 9.03, y + 0.16, 0.8, 0.8, 'Нельзя');
    box(s, `ok${i}`, { x: 10.25, y: y + 0.21, w: 2.5, h: 0.7, rectRadius: 0.35, fill: { color: GREEN }, text: items[i][1] ? 'Верно! Можно' : 'Верно! Нельзя', color: WHITE, bold: true, fontSize: 16, align: 'center' });
    box(s, `no${i}`, { x: 10.25, y: y + 0.21, w: 2.5, h: 0.7, rectRadius: 0.35, fill: { color: CORAL }, text: 'Подумай ещё!', color: WHITE, bold: true, fontSize: 16, align: 'center' });
    const good = items[i][1] ? `up${i}` : `dn${i}`, bad = items[i][1] ? `dn${i}` : `up${i}`;
    a.trig(good, [{ obj: `ok${i}`, fx: 'pop', dur: 450, sound: 'correct' }, { obj: good, fx: 'pulse', dur: 500 }]);
    a.trig(bad, [{ obj: `no${i}`, fx: 'pop', dur: 400, sound: 'wrong' }, { obj: `c${i}`, fx: 'shake', dur: 600 }, { obj: `no${i}`, fx: 'fadeOut', dur: 400, delay: 1500 }]);
    a.auto(`c${i}`, 'float', 300 + i * 130, 500); a.auto(`n${i}`, 'pop', 380 + i * 130, 400);
    a.auto(`up${i}`, 'zoom', 450 + i * 130, 400); a.auto(`dn${i}`, 'zoom', 500 + i * 130, 400);
  }
  if (part) {
    box(s, 'ban', { x: 0.6, y: 5.72, w: 9.45, h: 1.22, rectRadius: 0.2, fill: { color: GREEN_L }, shadow: undefined, text: [
      { text: 'Помни: ', options: { bold: true, color: GREEN_D } }, { text: 'металл, бумагу и стекло можно переработать и использовать снова!', options: { bold: true, color: NAVY } }],
      fontSize: 18, margin: mg(rawPath('B10') ? 160 : 112, 4, 16, 4) });
    if (rawPath('B10')) pic(s, 'img', await scene('B10'), 0.75, 5.58, 2.0, 1.5, 'Дети сортируют отходы');
    else pic(s, 'img', await AS.badge('FaRecycle', '#1FA463'), 1.0, 5.86, 0.95, 0.95, 'Переработка');
    a.auto('ban', 'float', 900, 500); a.auto('img', 'zoom', 1000, 600);
  }
  homeBtn(s, a);
  notes(s, 'Игра «Можно — нельзя» (3 мин). Дети показывают 👍 или 👎, затем учитель нажимает на нужный значок на слайде: правильный ответ — зелёная плашка и звук, неправильный — «Подумай ещё!».\nПосле каждого ответа кратко прокомментируйте ситуацию.\n1. Оставить свет включённым в пустой комнате — нельзя.\n2. Выключить компьютер после окончания работы — можно.\n3. Бросить металлическую банку в лесу — нельзя.\n4. Сдать металлические отходы на переработку — можно.\n5. Оставлять воду и электричество расходоваться без необходимости — нельзя.\n6. Использовать вещи повторно — можно.\n7. Бережно относиться к природным богатствам — можно.');
}

// ---------------- 21-22. Продолжи предложение ----------------
const SENT = [['Полезные ископаемые — это…', 'природные вещества в земной коре, которые использует человек'], ['К горючим полезным ископаемым относятся…', 'каменный уголь, нефть, природный газ'],
  ['Из железной руды получают…', 'металл'], ['Песок используется…', 'в строительстве и для изготовления стекла'], ['Глина используется…', 'для изготовления кирпича и керамики'],
  ['Полезные ископаемые нужно беречь, потому что…', 'их запасы ограничены: они образовывались миллионы лет'], ['Охранять природные богатства можно…', 'экономя энергию, перерабатывая отходы, повторно используя вещи']];
async function slideT3(part) {
  const [s, a] = newSlide(part ? S.T3B : S.T3A);
  setBg(s, a, 'light');
  header(s, a, `ЗАДАНИЕ 3${part ? ' (ПРОДОЛЖЕНИЕ)' : ''}`, 'Продолжи предложение', false, { tw: 6.4 });
  box(s, 'rule', { x: 7.4, y: 0.78, w: 5.35, h: 0.6, rectRadius: 0.3, fill: { color: AMBER_L }, shadow: undefined, text: 'Ответь сам, потом нажми на карточку', fontSize: 15, bold: true, color: AMBER_D, align: 'center' });
  a.auto('rule', 'pop', 400, 450);
  const items = part ? SENT.slice(4) : SENT.slice(0, 4);
  const endW = part ? 8.9 : 12.15;
  for (let i = 0; i < items.length; i++) {
    const y = 1.68 + i * 1.3;
    box(s, `c${i}`, { x: 0.6, y, w: endW, h: 1.12, rectRadius: 0.2, text: items[i][0], fontSize: 19, bold: true, color: NAVY, margin: mg(78, 2, endW * 72 * 0.5, 2) });
    pic(s, `n${i}`, await AS.numBadge((part ? 4 : 0) + i + 1, '#F5A524'), 0.78, y + 0.26, 0.6, 0.6);
    box(s, `e${i}`, { x: 0.6 + endW * 0.5, y: y + 0.13, w: endW * 0.5 - 0.15, h: 0.86, rectRadius: 0.18, fill: { color: GREEN_L }, line: { color: GREEN, width: 1.5 }, shadow: undefined, text: items[i][1], fontSize: 16, bold: true, color: GREEN_D, margin: mg(12, 2, 10, 2) });
    hit(s, `h${i}`, 0.6, y, endW, 1.12);
    a.trig(`h${i}`, [{ obj: `e${i}`, fx: 'float', dur: 450, sound: 'pop' }]);
    a.auto(`c${i}`, 'float', 300 + i * 130, 500); a.auto(`n${i}`, 'pop', 380 + i * 130, 400);
  }
  if (part) { pic(s, 'girl', await ch('C4'), 9.85, 2.1, 3.2, 4.8, 'Мира радуется'); a.auto('girl', 'zoom', 800, 700); }
  homeBtn(s, a);
  notes(s, 'Закрепление «Продолжи предложение» (4 мин). Учащиеся заканчивают фразы устно, затем нажмите на карточку — появится образец ответа.\n' + SENT.map((x) => `${x[0]} ${x[1]}.`).join('\n'));
}

// ---------------- 23-26. Мини-тест ----------------
const QUIZ = [
  { q: 'Что относится к полезным ископаемым?', a: [['нефть', 'M2'], ['облако', 'FaCloud'], ['птица', 'FaDove']], ok: 0 },
  { q: 'Что получают из железной руды?', a: [['металл', 'GiMetalBar'], ['стекло', 'FaWineBottle'], ['бумагу', 'FaNewspaper']], ok: 0 },
  { q: 'Какое полезное ископаемое используют как топливо?', a: [['природный газ', 'M3'], ['песок', 'M5'], ['глина', 'M6']], ok: 0 },
  { q: 'Как следует относиться к полезным ископаемым?', a: [['расходовать без ограничений', 'FaInfinity'], ['бережно и разумно использовать', 'FaHandHoldingHeart'], ['не использовать никогда', 'FaBan']], ok: 1 }];
async function slideQuiz(i) {
  const [s, a] = newSlide(S.Q1 + i);
  setBg(s, a, 'light');
  header(s, a, `МИНИ-ТЕСТ · ВОПРОС ${i + 1} ИЗ 4`, 'Проверь себя!', false, { tw: 6 });
  for (let k = 0; k < 4; k++) {
    s.addShape(P.ShapeType.ellipse, { x: 11.05 + k * 0.45, y: 0.86, w: 0.28, h: 0.28, fill: { color: k <= i ? AMBER : 'D5DEEA' }, line: { type: 'none' }, objectName: `dot${k}` });
    a.auto(`dot${k}`, 'pop', 300 + k * 80, 300);
  }
  const Q = QUIZ[i];
  box(s, 'q', { x: 0.6, y: 1.6, w: 12.15, h: 1.25, rectRadius: 0.24, fill: { color: NAVY }, text: Q.q, fontSize: 27, bold: true, color: WHITE, margin: mg(92, 4, 18, 4) });
  pic(s, 'qn', await AS.numBadge(i + 1, '#F5A524', '#1D2B53'), 0.85, 1.88, 0.7, 0.7);
  const cw = 3.9, gap = 0.225, letters = ['А', 'Б', 'В'];
  for (let k = 0; k < 3; k++) {
    const x = 0.6 + k * (cw + gap), y = 3.1;
    const [label, im] = Q.a[k];
    box(s, `c${k}`, { x, y, w: cw, h: 2.95, rectRadius: 0.24, text: label, fontSize: label.length > 16 ? 19 : 23, bold: true, color: NAVY, align: 'center', valign: 'bottom', margin: mg(12, 4, 12, 14) });
    pic(s, `l${k}`, await AS.numBadge(letters[k], '#4A7BD0'), x + 0.18, y + 0.18, 0.58, 0.58);
    const isMineral = /^M\d/.test(im);
    if (isMineral) pic(s, `im${k}`, await sq(im), x + (cw - 1.75) / 2, y + 0.2, 1.75, 1.75, label);
    else pic(s, `im${k}`, await AS.badge(im, '#EAF4FF', '#4A7BD0'), x + (cw - 1.45) / 2, y + 0.35, 1.45, 1.45, label);
    s.addShape(P.ShapeType.roundRect, { x: x - 0.06, y: y - 0.06, w: cw + 0.12, h: 3.07, rectRadius: 0.27, fill: { type: 'none' }, line: { color: k === Q.ok ? GREEN : CORAL, width: 5 }, objectName: `ring${k}` });
    hit(s, `h${k}`, x, y, cw, 2.95);
    a.auto(`c${k}`, 'float', 600 + k * 150, 500); a.auto(`l${k}`, 'pop', 700 + k * 150, 400); a.auto(`im${k}`, 'zoom', 720 + k * 150, 450);
  }
  box(s, 'good', { x: 0.6, y: 6.25, w: 12.15, h: 0.72, rectRadius: 0.36, fill: { color: GREEN }, text: i === 3 ? 'Верно! Ты настоящий защитник природных богатств!' : 'Верно! Молодец!', color: WHITE, bold: true, fontSize: 20, align: 'center' });
  box(s, 'bad', { x: 0.6, y: 6.25, w: 12.15, h: 0.72, rectRadius: 0.36, fill: { color: CORAL }, text: 'Не совсем. Попробуй ещё раз!', color: WHITE, bold: true, fontSize: 20, align: 'center' });
  for (let k = 0; k < 3; k++) {
    if (k === Q.ok) a.trig(`h${k}`, [{ obj: `ring${k}`, fx: 'zoom', dur: 400, sound: i === 3 ? 'applause' : 'correct' }, { obj: 'good', fx: 'pop', dur: 450, delay: 100 }, { obj: `im${k}`, fx: 'pulse', dur: 600, delay: 200 }]);
    else a.trig(`h${k}`, [{ obj: `ring${k}`, fx: 'appear', dur: 1, sound: 'wrong' }, { obj: `c${k}`, fx: 'shake', dur: 600 }, { obj: 'bad', fx: 'pop', dur: 400 },
      { obj: 'bad', fx: 'fadeOut', dur: 400, delay: 1600 }, { obj: `ring${k}`, fx: 'fadeOut', dur: 400, delay: 1600 }]);
  }
  a.auto('q', 'float', 250, 600); a.auto('qn', 'pop', 400, 400);
  homeBtn(s, a);
  notes(s, `Мини-тест, вопрос ${i + 1}. Нажмите на вариант ответа: правильный подсветится зелёным, неправильный — красным, и можно попробовать ещё раз.\nПравильный ответ: ${letters[Q.ok]}) ${Q.a[Q.ok][0]}.`);
}

// ---------------- 27. Интерактив онлайн ----------------
async function slideOnline() {
  section('Интерактив онлайн');
  const [s, a] = newSlide(S.ONLINE);
  setBg(s, a, 'dark');
  header(s, a, 'ИНТЕРАКТИВ ОНЛАЙН', 'Играем на сайте урока!', true);
  box(s, 'qrc', { x: 0.6, y: 1.65, w: 4.3, h: 5.3, rectRadius: 0.28 });
  const qr = path.join(AS.OUT, 'qr.png');
  await require('qrcode').toFile(qr, CFG.siteUrl, { width: 900, margin: 1, color: { dark: '#1D2B53', light: '#FFFFFF' } });
  pic(s, 'qr', qr, 0.85, 1.9, 3.8, 3.8, 'QR-код сайта');
  txt(s, 'qrt', 'Наведи камеру телефона на код', { x: 0.75, y: 5.85, w: 4.0, h: 0.8, fontSize: 16, bold: true, color: NAVY, align: 'center', valign: 'middle' });
  const games = [['GiGems', 'Собери коллекцию: три группы'], ['FaLink', 'Что из чего получают?'], ['FaThumbsUp', 'Можно или нельзя?'], ['FaListCheck', 'Мини-тест со звёздами'], ['FaPersonRunning', 'Физкультминутка с ИИ']];
  for (let i = 0; i < games.length; i++) {
    const y = 1.7 + i * 0.82;
    box(s, `g${i}`, { x: 5.3, y, w: 7.45, h: 0.68, rectRadius: 0.34, fill: { color: WHITE, transparency: 88 }, line: { color: 'C9D6FF', width: 1 }, shadow: undefined, text: games[i][1], color: WHITE, bold: true, fontSize: 18, margin: mg(62, 0, 12, 0) });
    pic(s, `gi${i}`, await AS.badge(games[i][0], '#F5A524', '#1D2B53'), 5.42, y + 0.1, 0.48, 0.48);
    a.auto(`g${i}`, 'float', 700 + i * 120, 450); a.auto(`gi${i}`, 'pop', 760 + i * 120, 350);
  }
  box(s, 'open', { x: 5.3, y: 6.0, w: 4.0, h: 0.86, rectRadius: 0.43, fill: { color: AMBER }, text: 'Открыть сайт', color: NAVY, bold: true, fontSize: 22, margin: mg(66, 0, 12, 0) });
  pic(s, 'openi', await AS.badge('FaGlobe', 'none', '#1D2B53', { pad: 0.08 }), 5.55, 6.18, 0.5, 0.5);
  a.url('open', CFG.siteUrl); a.url('openi', CFG.siteUrl);
  txt(s, 'url', CFG.siteLabel, { x: 9.5, y: 6.0, w: 3.3, h: 0.86, fontSize: 15, color: 'C9D6FF', valign: 'middle' });
  a.auto('qrc', 'zoom', 250, 600); a.auto('qr', 'zoom', 400, 600); a.auto('qrt', 'fade', 700, 400);
  a.auto('open', 'pop', 1400, 500, { sound: 'pop' }); a.auto('openi', 'fade', 1500, 300); a.auto('url', 'fade', 1500, 400); a.auto('open', 'pulse', 2600, 700);
  homeBtn(s, a);
  notes(s, 'Интерактив онлайн. Нажмите «Открыть сайт» (нужен интернет): kladovye-zemli.lovable.app. Без интернета можно открыть файл «Сайт_Кладовые_Земли.html» с компьютера. Дети могут открыть сайт по QR-коду с планшета или телефона.\nНа сайте: игра «Собери коллекцию» (сортировка по группам), «Что из чего?», «Можно или нельзя?», мини-тест и та же физкультминутка с ИИ-озвучкой.');
}

// ---------------- 28. Подведение итогов ----------------
async function slideSummary() {
  section('Итоги и рефлексия');
  const [s, a] = newSlide(S.SUM);
  setBg(s, a, 'warm');
  header(s, a, 'ПОДВЕДЁМ ИТОГИ', 'Что мы узнали?');
  const qs = ['Что такое полезные ископаемые?', 'Какие группы мы вспомнили?', 'Для чего они нужны человеку?', 'Почему их необходимо беречь?', 'Что каждый из нас может делать?'];
  for (let i = 0; i < 5; i++) {
    const col = i < 3 ? 0 : 1, r = i < 3 ? i : i - 3;
    const x = 0.6 + col * 6.2, y = 1.6 + r * 0.92;
    box(s, `q${i}`, { x, y, w: 5.95, h: 0.78, rectRadius: 0.39, text: qs[i], fontSize: 18, bold: true, color: NAVY, margin: mg(64, 0, 12, 0) });
    pic(s, `qn${i}`, await AS.numBadge(i + 1, '#F5A524'), x + 0.12, y + 0.1, 0.58, 0.58);
    a.auto(`q${i}`, 'float', 300 + i * 120, 450); a.auto(`qn${i}`, 'pop', 360 + i * 120, 350);
  }
  box(s, 'concl', { x: 0.6, y: 4.55, w: 9.3, h: 2.4, rectRadius: 0.26, fill: { color: NAVY }, text: [
    { text: 'ВЫВОД', options: { bold: true, fontSize: 13, color: 'FFD27A', charSpacing: 2, breakLine: true } },
    { text: 'Полезные ископаемые — важные богатства Земли. Человек использует их в строительстве, промышленности, энергетике и в жизни. Их запасы ограничены, поэтому их нужно добывать и использовать разумно, экономить ресурсы, перерабатывать материалы и беречь природу.', options: { fontSize: 19, color: WHITE } }],
    valign: 'top', margin: mg(24, 14, 22, 12) });
  pic(s, 'girl', await ch('C4'), 10.2, 3.35, 2.6, 3.9, 'Мира радуется');
  a.auto('girl', 'zoom', 900, 700);
  a.click([{ obj: 'concl', fx: 'float', dur: 650, sound: 'bell' }]);
  homeBtn(s, a);
  notes(s, 'Подведение итогов (2 мин).\n— Что такое полезные ископаемые?\n— Какие группы полезных ископаемых мы сегодня вспомнили?\n— Для чего они нужны человеку?\n— Почему их необходимо беречь?\n— Что лично каждый из нас может делать для рационального использования природных ресурсов?\nЩелчок — итоговый вывод.');
}

// ---------------- 29. Рефлексия ----------------
async function slideReflect() {
  const [s, a] = newSlide(S.REF);
  setBg(s, a, 'warm');
  header(s, a, 'РЕФЛЕКСИЯ', 'Как прошёл наш урок?');
  pic(s, 'tl', await AS.trafficLight('traffic.png'), 0.75, 1.55, 1.9, 5.3, 'Светофор');
  const lights = [['#2BD27A', 'Всё понял(а), могу объяснить другому', GREEN_D], ['#FFC23D', 'Кое-что понял(а), но остались вопросы', AMBER_D], ['#FF6B6B', 'Мне нужна помощь', CORAL_D]];
  const cy = [1.55 + 5.3 * 190 / 1060, 1.55 + 5.3 * 510 / 1060, 1.55 + 5.3 * 830 / 1060];
  for (let i = 0; i < 3; i++) {
    const d = 1.35;
    pic(s, `gl${i}`, await AS.glow(`glow${i}.png`, lights[i][0]), 0.75 + 0.95 - d / 2 + 0.05, cy[i] - d / 2, d, d, 'Огонёк');
    hit(s, `h${i}`, 0.75, cy[i] - 0.7, 1.9, 1.4);
    box(s, `t${i}`, { x: 2.95, y: cy[i] - 0.48, w: 4.2, h: 0.96, rectRadius: 0.2, text: lights[i][1], fontSize: 17, bold: true, color: lights[i][2] });
    a.trig(`h${i}`, [{ obj: `gl${i}`, fx: 'pop', dur: 450, sound: 'bell' }, { obj: `t${i}`, fx: 'pulse', dur: 600 }]);
    a.auto(`t${i}`, 'float', 500 + i * 150, 450);
  }
  box(s, 'sc', { x: 7.55, y: 1.6, w: 5.2, h: 5.3, rectRadius: 0.26, text: '' });
  txt(s, 'sct', 'Закончи предложение', { x: 7.85, y: 1.85, w: 4.6, h: 0.5, fontSize: 21, bold: true, color: NAVY });
  const st = ['Сегодня я узнал(а), что…', 'Меня удивило…', 'Теперь я понимаю, почему…', 'Я могу помочь природе, если…'];
  for (let i = 0; i < 4; i++) {
    const y = 2.55 + i * 1.05;
    box(s, `s${i}`, { x: 7.85, y, w: 4.6, h: 0.85, rectRadius: 0.2, fill: { color: AMBER_L }, shadow: undefined, text: st[i], fontSize: 17, bold: true, color: NAVY, margin: mg(16, 0, 10, 0) });
    a.auto(`s${i}`, 'float', 1100 + i * 130, 450);
  }
  a.auto('tl', 'zoom', 250, 700); a.auto('sc', 'float', 800, 500); a.auto('sct', 'fade', 950, 400);
  homeBtn(s, a);
  notes(s, 'Рефлексия (2 мин). Приём «Светофор»: дети поднимают карточку нужного цвета, учитель может нажать на огонёк светофора — он загорится.\n🟢 Зелёный — всё понял, могу объяснить другому.\n🟡 Жёлтый — кое-что понял, но остались вопросы.\n🔴 Красный — мне нужна помощь.\nЗакончите предложения: Сегодня я узнал(а), что… Меня удивило… Теперь я понимаю, почему… Я могу помочь природе, если…');
}

// ---------------- 30. Домашнее задание ----------------
async function slideHomework() {
  const [s, a] = newSlide(S.HW);
  setBg(s, a, 'light');
  header(s, a, 'ДОМАШНЕЕ ЗАДАНИЕ', 'Задание на дом');
  box(s, 'must', { x: 0.6, y: 1.6, w: 12.15, h: 1.05, rectRadius: 0.22, fill: { color: NAVY }, text: [
    { text: 'Обязательно: ', options: { bold: true, color: 'FFD27A' } }, { text: 'прочитать материал учебника и ответить на вопросы после текста.', options: { color: WHITE, bold: true } }], fontSize: 19, margin: mg(84, 4, 16, 4) });
  pic(s, 'musti', await AS.badge('FaBookOpen', '#F5A524', '#1D2B53'), 0.82, 1.8, 0.65, 0.65);
  txt(s, 'chT', 'Творческое задание — выбери одно:', { x: 0.6, y: 2.85, w: 8, h: 0.45, fontSize: 19, bold: true, color: AMBER_D });
  const ch3 = [['FaPaintbrush', '#F2643D', 'Нарисуй одно полезное ископаемое и покажи, где его используют'], ['FaListCheck', '#1FA463', 'Составь памятку «Как беречь природные богатства» из 5 правил'], ['FaMagnifyingGlass', '#4A7BD0', 'Найди дома 5 предметов из природных ресурсов и запиши их названия']];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.125;
    box(s, `c${i}`, { x, y: 3.4, w: 3.9, h: 2.0, rectRadius: 0.22, text: ch3[i][2], fontSize: 17, bold: true, color: NAVY, valign: 'top', margin: mg(18, 76, 16, 10) });
    pic(s, `ci${i}`, await AS.badge(ch3[i][0], ch3[i][1]), x + 0.22, 3.58, 0.68, 0.68);
    a.auto(`c${i}`, 'float', 700 + i * 140, 500); a.auto(`ci${i}`, 'pop', 780 + i * 140, 400);
  }
  box(s, 'bonus', { x: 0.6, y: 5.62, w: 12.15, h: 1.33, rectRadius: 0.22, fill: { color: AMBER_L }, shadow: undefined, text: [
    { text: 'Для самых любознательных: ', options: { bold: true, color: AMBER_D } }, { text: 'составь цепочку «полезное ископаемое → что из него получают → где это используют».', options: { color: NAVY, bold: true, breakLine: true } },
    { text: 'Например: железная руда → металл → инструменты, машины, бытовые предметы.', options: { color: MUTED, italic: true } }], fontSize: 16, margin: mg(84, 4, 16, 4) });
  pic(s, 'bonusi', await AS.badge('FaStar', '#F5A524'), 0.82, 5.95, 0.65, 0.65);
  a.auto('must', 'float', 250, 550); a.auto('musti', 'pop', 400, 400); a.auto('chT', 'fade', 600, 400);
  a.auto('bonus', 'float', 1300, 500); a.auto('bonusi', 'pop', 1400, 400);
  homeBtn(s, a);
  notes(s, 'Домашнее задание.\nОбязательная часть: прочитать соответствующий материал учебника и ответить на вопросы после текста.\nТворческое задание по выбору: нарисовать один вид полезного ископаемого и показать, где его используют; составить памятку «Как беречь природные богатства» из 5 правил; найти дома 5 предметов, изготовленных с использованием природных ресурсов, и записать их названия.\nДополнительно для сильных учащихся: цепочка «полезное ископаемое → что из него получают → где человек это использует».');
}

// ---------------- 31. Финал ----------------
async function slideEnd() {
  const [s, a] = newSlide(S.END);
  setBg(s, a, 'dark');
  txt(s, 'kicker', 'ГЛАВНАЯ МЫСЛЬ УРОКА', { x: 0.6, y: 0.9, w: 8, h: 0.35, fontSize: 14, bold: true, charSpacing: 3, color: 'FFD27A' });
  box(s, 'idea', { x: 0.6, y: 1.4, w: 8.4, h: 2.6, rectRadius: 0.28, text: [
    { text: 'Полезные ископаемые помогают человеку жить и развиваться, но их запасы ограничены.', options: { color: NAVY, bold: true, breakLine: true } },
    { text: 'Используй природные богатства разумно, экономно и бережно!', options: { color: GREEN_D, bold: true } }], fontSize: 23, valign: 'middle', margin: mg(28, 12, 24, 12) });
  txt(s, 'thanks', 'Спасибо за урок!', { x: 0.6, y: 4.5, w: 8.4, h: 1.1, fontSize: 52, bold: true, color: WHITE, valign: 'middle' });
  txt(s, 'bye', 'До новых путешествий!', { x: 0.6, y: 5.6, w: 8.4, h: 0.6, fontSize: 24, color: 'FFD27A', bold: true });
  pic(s, 'girl', await ch('C1'), 9.3, 1.3, 3.75, 5.63, 'Мира прощается');
  a.auto('kicker', 'fade', 0, 500); a.auto('idea', 'float', 200, 700);
  a.auto('girl', 'zoom', 500, 800);
  a.auto('thanks', 'zoom', 1200, 800, { sound: 'applause' }); a.auto('bye', 'float', 1700, 600);
  homeBtn(s, a);
  notes(s, 'Ключевая идея урока для запоминания: полезные ископаемые помогают человеку жить и развиваться, но их запасы ограничены. Поэтому использовать природные богатства нужно разумно, экономно и бережно.');
}

build().catch((e) => { console.error(e); process.exit(1); });
