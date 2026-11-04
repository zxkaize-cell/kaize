// Visual assets rendered from SVG with sharp: backgrounds, icon badges, frames, placeholders.
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const React = require('react');
const RDS = require('react-dom/server');
const fa = require('react-icons/fa6');
const gi = require('react-icons/gi');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'assets');
const IMG = path.join(ROOT, 'img');
fs.mkdirSync(OUT, { recursive: true });

const FONT = "Liberation Sans, Arial, sans-serif";

function icon(name) {
  const lib = name.startsWith('Gi') ? gi : fa;
  const C = lib[name];
  if (!C) throw new Error('icon ' + name);
  return C;
}
function iconSvg(name, size, color, x = 0, y = 0) {
  let s = RDS.renderToStaticMarkup(React.createElement(icon(name), { size, color }));
  return s.replace('<svg ', `<svg x="${x}" y="${y}" `);
}
async function svgPng(svg, file, opts = {}) {
  const out = path.join(OUT, file);
  let img = sharp(Buffer.from(svg), { density: opts.density || 72 });
  if (opts.jpg) await img.jpeg({ quality: 88 }).toFile(out);
  else await img.png().toFile(out);
  return out;
}
const esc = (t) => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// ---------- backgrounds (2667 x 1500 px = 13.333 x 7.5 in at 200 dpi) ----------
const BW = 2667, BH = 1500;
function rnd(seed) { let s = seed; return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }; }
function wave(y, amp, seed, phase = 0) {
  const r = rnd(seed); let d = `M 0 ${BH} L 0 ${y}`;
  const n = 6; const seg = BW / n;
  let py = y;
  for (let i = 1; i <= n; i++) {
    const ny = y + (r() - 0.5) * amp * 2;
    d += ` C ${(i - 0.6) * seg} ${py + amp * Math.sin(i + phase)} ${(i - 0.4) * seg} ${ny - amp * Math.sin(i + phase)} ${i * seg} ${ny}`;
    py = ny;
  }
  return d + ` L ${BW} ${BH} Z`;
}
function sparkles(seed, n, color, op, area = [0, 0, BW, BH * 0.8], size = [6, 16]) {
  const r = rnd(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x = area[0] + r() * (area[2] - area[0]), y = area[1] + r() * (area[3] - area[1]);
    const k = size[0] + r() * (size[1] - size[0]);
    s += `<path d="M ${x} ${y - k} L ${x + k * 0.35} ${y} L ${x} ${y + k} L ${x - k * 0.35} ${y} Z" fill="${color}" opacity="${(op * (0.5 + r() * 0.5)).toFixed(2)}"/>`;
  }
  return s;
}
function dots(seed, n, colors, area, rad = [3, 9], op = 0.5) {
  const r = rnd(seed); let s = '';
  for (let i = 0; i < n; i++) {
    const x = area[0] + r() * (area[2] - area[0]), y = area[1] + r() * (area[3] - area[1]);
    s += `<circle cx="${x}" cy="${y}" r="${rad[0] + r() * (rad[1] - rad[0])}" fill="${colors[i % colors.length]}" opacity="${(op * (0.4 + r() * 0.6)).toFixed(2)}"/>`;
  }
  return s;
}
async function backgrounds() {
  const defs = `<filter id="b40"><feGaussianBlur stdDeviation="40"/></filter><filter id="b8"><feGaussianBlur stdDeviation="6"/></filter>`;
  const light = `<svg xmlns="http://www.w3.org/2000/svg" width="${BW}" height="${BH}"><defs>${defs}
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E6F2FF"/><stop offset="0.75" stop-color="#F7FBFF"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient></defs>
    <rect width="${BW}" height="${BH}" fill="url(#g)"/>
    <circle cx="${BW * 0.88}" cy="${BH * 0.08}" r="420" fill="#FFFFFF" opacity="0.75" filter="url(#b40)"/>
    <circle cx="${BW * 0.05}" cy="${BH * 0.55}" r="380" fill="#FFF3D9" opacity="0.55" filter="url(#b40)"/>
    ${sparkles(7, 26, '#BFD8F5', 0.55)}
    <path d="${wave(BH - 120, 18, 3, 0.4)}" fill="#F6E4BA" opacity="0.55"/>
    <path d="${wave(BH - 80, 14, 5, 1.3)}" fill="#F1CBAE" opacity="0.45"/>
    <path d="${wave(BH - 42, 10, 9, 2.1)}" fill="#D5DEEA" opacity="0.75"/>
  </svg>`;
  const dark = `<svg xmlns="http://www.w3.org/2000/svg" width="${BW}" height="${BH}"><defs>${defs}
    <linearGradient id="g" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="#16214A"/><stop offset="1" stop-color="#253A82"/></linearGradient></defs>
    <rect width="${BW}" height="${BH}" fill="url(#g)"/>
    <circle cx="${BW * 0.82}" cy="${BH * 0.18}" r="520" fill="#3A5BC7" opacity="0.35" filter="url(#b40)"/>
    <circle cx="${BW * 0.12}" cy="${BH * 0.85}" r="460" fill="#F5A524" opacity="0.10" filter="url(#b40)"/>
    ${dots(11, 70, ['#FFFFFF'], [0, 0, BW, BH * 0.85], [1.5, 4], 0.55)}
    <g filter="url(#b8)">${dots(13, 22, ['#FFC857', '#7FE0C2', '#9DB6FF', '#FF9A7A'], [0, BH * 0.15, BW, BH * 0.9], [5, 11], 0.55)}</g>
    <path d="${wave(BH - 130, 20, 21, 0.2)}" fill="#1B2B63" opacity="0.65"/>
    <path d="${wave(BH - 75, 14, 23, 1.1)}" fill="#14204A" opacity="0.7"/>
  </svg>`;
  const green = `<svg xmlns="http://www.w3.org/2000/svg" width="${BW}" height="${BH}"><defs>${defs}
    <linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E3F6EA"/><stop offset="0.8" stop-color="#F8FDF9"/><stop offset="1" stop-color="#FFFFFF"/></linearGradient></defs>
    <rect width="${BW}" height="${BH}" fill="url(#g)"/>
    <circle cx="${BW * 0.9}" cy="${BH * 0.1}" r="420" fill="#FFFFFF" opacity="0.8" filter="url(#b40)"/>
    ${sparkles(31, 22, '#B7E3C5', 0.6)}
    <path d="${wave(BH - 120, 20, 33, 0.7)}" fill="#C5EBD1" opacity="0.6"/>
    <path d="${wave(BH - 70, 14, 35, 1.9)}" fill="#A5DDB7" opacity="0.5"/>
  </svg>`;
  const warm = `<svg xmlns="http://www.w3.org/2000/svg" width="${BW}" height="${BH}"><defs>${defs}
    <linearGradient id="g" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#FFF7E3"/><stop offset="1" stop-color="#FFE4AE"/></linearGradient></defs>
    <rect width="${BW}" height="${BH}" fill="url(#g)"/>
    <circle cx="${BW * 0.85}" cy="${BH * 0.12}" r="460" fill="#FFFFFF" opacity="0.7" filter="url(#b40)"/>
    ${dots(41, 46, ['#F5A524', '#1FA463', '#4A7BD0', '#F2643D'], [0, 0, BW, BH * 0.85], [4, 9], 0.35)}
    ${sparkles(43, 18, '#F5C25B', 0.6)}
    <path d="${wave(BH - 110, 18, 45, 0.3)}" fill="#FFD27A" opacity="0.45"/>
    <path d="${wave(BH - 60, 12, 47, 1.4)}" fill="#F8C35C" opacity="0.4"/>
  </svg>`;
  return {
    light: await svgPng(light, 'bg_light.jpg', { jpg: true }),
    dark: await svgPng(dark, 'bg_dark.jpg', { jpg: true }),
    green: await svgPng(green, 'bg_green.jpg', { jpg: true }),
    warm: await svgPng(warm, 'bg_warm.jpg', { jpg: true }),
  };
}

// ---------- icon badge: circle (or rounded square) with an icon ----------
async function badge(iconName, bg, fg = '#FFFFFF', opts = {}) {
  const size = opts.size || 256, pad = opts.pad || 0.24;
  const key = `badge_${iconName}_${bg.replace('#', '')}_${fg.replace('#', '')}_${opts.ring ? 'r' : ''}.png`;
  const f = path.join(OUT, key);
  if (fs.existsSync(f)) return f;
  const is = Math.round(size * (1 - 2 * pad));
  const off = Math.round((size - is) / 2);
  const ring = opts.ring ? `<circle cx="${size / 2}" cy="${size / 2}" r="${size / 2 - 6}" fill="none" stroke="#FFFFFF" stroke-width="10"/>` : '';
  const shape = bg === 'none' ? '' : `<circle cx="${size / 2}" cy="${size / 2}" r="${size / 2}" fill="${bg}"/>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">${shape}${ring}${iconSvg(iconName, is, fg, off, off)}</svg>`;
  return svgPng(svg, key);
}
// circle with a number
async function numBadge(n, bg, fg = '#FFFFFF') {
  const key = `num_${n}_${bg.replace('#', '')}.png`;
  const f = path.join(OUT, key);
  if (fs.existsSync(f)) return f;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><circle cx="128" cy="128" r="128" fill="${bg}"/>
    <text x="128" y="128" dy="0.36em" text-anchor="middle" font-family="${FONT}" font-weight="bold" font-size="150" fill="${fg}">${esc(n)}</text></svg>`;
  return svgPng(svg, key);
}

// ---------- placeholders for images the teacher generates ----------
async function placeholder(code, label, kind) {
  const key = `ph_${code}.png`;
  const dims = { char: [600, 900], sq: [600, 600], scene43: [1200, 900], scene169: [1600, 900] }[kind];
  const [w, h] = dims;
  const ic = { char: 'FaChild', sq: 'FaGem', scene43: 'FaMountain', scene169: 'FaMountain' }[kind];
  const isz = Math.min(w, h) * 0.32;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <rect x="12" y="12" width="${w - 24}" height="${h - 24}" rx="${Math.min(w, h) * 0.08}" fill="#FFFFFF" fill-opacity="0.72" stroke="#8FA6C9" stroke-width="8" stroke-dasharray="26 18"/>
    ${iconSvg(ic, isz, '#9DB0CF', (w - isz) / 2, h * 0.5 - isz * 0.85)}
    <text x="${w / 2}" y="${h * 0.5 + isz * 0.42}" text-anchor="middle" font-family="${FONT}" font-weight="bold" font-size="${Math.min(w, h) * 0.13}" fill="#5B6B8C">${esc(code)}</text>
    <text x="${w / 2}" y="${h * 0.5 + isz * 0.42 + Math.min(w, h) * 0.12}" text-anchor="middle" font-family="${FONT}" font-size="${Math.min(w, h) * 0.065}" fill="#7A89A8">${esc(label)}</text>
  </svg>`;
  return svgPng(svg, key);
}

// framed scene: cover-crop to aspect, rounded corners, white border, soft shadow
async function framed(src, code, aspect) {
  const W = aspect === 169 ? 1600 : 1200, H = 900;
  const out = path.join(OUT, `frame_${code}.png`);
  const pad = 40, border = 16, rad = 46;
  const iw = W - 2 * pad - 2 * border, ih = H - 2 * pad - 2 * border;
  const photo = await sharp(src).resize(iw, ih, { fit: 'cover', position: 'attention' }).png().toBuffer();
  const mask = Buffer.from(`<svg width="${iw}" height="${ih}"><rect width="${iw}" height="${ih}" rx="${rad - border}" fill="#fff"/></svg>`);
  const rounded = await sharp(photo).composite([{ input: mask, blend: 'dest-in' }]).png().toBuffer();
  const base = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}"><defs><filter id="s" x="-10%" y="-10%" width="120%" height="130%"><feGaussianBlur stdDeviation="14"/></filter></defs>
    <rect x="${pad}" y="${pad + 10}" width="${W - 2 * pad}" height="${H - 2 * pad}" rx="${rad}" fill="#1D2B53" opacity="0.22" filter="url(#s)"/>
    <rect x="${pad}" y="${pad}" width="${W - 2 * pad}" height="${H - 2 * pad}" rx="${rad}" fill="#FFFFFF"/></svg>`);
  await sharp(base).composite([{ input: rounded, left: pad + border, top: pad + border }]).png().toFile(out);
  return out;
}

// white medallion with a mineral cut-out inside
async function medallion(src, code) {
  const S = 600, out = path.join(OUT, `med_${code}.png`);
  const inner = await sharp(src).resize(Math.round(S * 0.70), Math.round(S * 0.70), { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  const base = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}"><defs><filter id="s"><feGaussianBlur stdDeviation="12"/></filter></defs>
    <circle cx="${S / 2}" cy="${S / 2 + 10}" r="${S / 2 - 40}" fill="#1D2B53" opacity="0.20" filter="url(#s)"/>
    <circle cx="${S / 2}" cy="${S / 2}" r="${S / 2 - 40}" fill="#FFFFFF"/></svg>`);
  await sharp(base).composite([{ input: inner, gravity: 'center' }]).png().toFile(out);
  return out;
}

// dashed snake route for the excursion map
async function route(points, w, h, file) {
  const d = points.map((p, i) => (i ? 'L' : 'M') + ` ${p[0]} ${p[1]}`).join(' ');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <path d="${d}" fill="none" stroke="#FFD27A" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 26" opacity="0.95"/></svg>`;
  return svgPng(svg, file);
}

// tree connector (one node to three) for the groups scheme
async function treeLines(file, color) {
  const w = 1900, h = 130;
  const xs = [w * 0.165, w * 0.5, w * 0.835];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}">
    <path d="M ${w / 2} 0 L ${w / 2} ${h * 0.45} M ${xs[0]} ${h} L ${xs[0]} ${h * 0.45} L ${xs[2]} ${h * 0.45} L ${xs[2]} ${h}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  return svgPng(svg, file);
}

async function arrow(file, color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120"><path d="M 10 60 L 150 60 M 110 20 L 155 60 L 110 100" fill="none" stroke="${color}" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  return svgPng(svg, file);
}

// traffic light body for reflection
async function trafficLight(file) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="380" height="1060"><defs><filter id="s"><feGaussianBlur stdDeviation="10"/></filter></defs>
    <rect x="40" y="40" width="300" height="980" rx="120" fill="#1D2B53" opacity="0.25" filter="url(#s)"/>
    <rect x="30" y="20" width="300" height="980" rx="120" fill="#24345F"/>
    <circle cx="180" cy="190" r="110" fill="#1B8F55"/><circle cx="180" cy="510" r="110" fill="#C98A12"/><circle cx="180" cy="830" r="110" fill="#C24848"/>
  </svg>`;
  return svgPng(svg, file);
}
async function glow(file, color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><defs><filter id="b"><feGaussianBlur stdDeviation="28"/></filter></defs>
    <circle cx="200" cy="200" r="150" fill="${color}" opacity="0.85" filter="url(#b)"/><circle cx="200" cy="200" r="110" fill="${color}"/>
    <circle cx="165" cy="160" r="34" fill="#FFFFFF" opacity="0.55"/></svg>`;
  return svgPng(svg, file);
}

module.exports = { ROOT, OUT, IMG, backgrounds, badge, numBadge, placeholder, framed, medallion, route, treeLines, arrow, trafficLight, glow, svgPng, iconSvg };
