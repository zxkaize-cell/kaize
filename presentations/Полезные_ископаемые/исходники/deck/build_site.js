// Builds the lesson website as ONE self-contained HTML file (images, sounds, timeline inlined).
// Two outputs: site/index.html (full document, works offline) and site/artifact.html (fragment for claude.ai).
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const React = require('react');
const RDS = require('react-dom/server');
const fa = require('react-icons/fa6');
const gi = require('react-icons/gi');
const AS = require('./assets');

const ROOT = AS.ROOT;
const OUT = path.join(ROOT, 'build', 'site');
fs.mkdirSync(OUT, { recursive: true });
const TL = JSON.parse(fs.readFileSync(path.join(ROOT, 'build', 'fizminutka_timeline.json'), 'utf8'));
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, 'deck', 'config.json'), 'utf8'));

const ic = (name, cls = 'ic') => {
  const C = (name.startsWith('Gi') ? gi : fa)[name];
  if (!C) throw new Error(name);
  return RDS.renderToStaticMarkup(React.createElement(C, { className: cls, 'aria-hidden': 'true' }));
};

async function imgData(code, kind, h) {
  const cut = path.join(AS.IMG, 'cut', code + '.png');
  const src = fs.existsSync(cut) ? cut : await AS.placeholder(code, CFG.labels[code] || '', kind);
  const buf = await sharp(src).resize({ height: h, withoutEnlargement: true }).webp({ quality: 82, alphaQuality: 90 }).toBuffer();
  return 'data:image/webp;base64,' + buf.toString('base64');
}
async function sceneData(code, w) {
  for (const e of ['.png', '.jpg', '.jpeg', '.webp']) {
    const f = path.join(AS.IMG, 'raw', code + e);
    if (fs.existsSync(f)) {
      const buf = await sharp(f).resize({ width: w, withoutEnlargement: true }).webp({ quality: 80 }).toBuffer();
      return 'data:image/webp;base64,' + buf.toString('base64');
    }
  }
  return null;
}
function snd(file) { return 'data:audio/mpeg;base64,' + fs.readFileSync(file).toString('base64'); }

async function main() {
  const I = {};
  for (const c of ['C1', 'C3', 'C4']) I[c] = await imgData(c, 'char', 640);
  const POSE = {};
  for (const c of ['C1', 'C4', 'P0', 'P1', 'P2', 'P3', 'P4', 'P5']) {
    const f = path.join(AS.IMG, 'pose', c + '.png');
    POSE[c] = fs.existsSync(f) ? 'data:image/webp;base64,' + (await sharp(f).resize({ height: 640 }).webp({ quality: 82, alphaQuality: 90 }).toBuffer()).toString('base64') : await imgData(c, 'char', 640);
  }
  for (const c of ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8']) I[c] = await imgData(c, 'sq', 360);
  const B1 = (await sceneData('HUB', 1600)) || (await sceneData('B1', 1400));
  let MEADOW = null;
  for (const e of ['.png', '.jpg']) { const f = path.join(AS.IMG, 'raw', 'B11' + e); if (fs.existsSync(f)) MEADOW = 'data:image/jpeg;base64,' + (await sharp(f).flop().resize({ width: 1200 }).jpeg({ quality: 78 }).toBuffer()).toString('base64'); }
  const R = path.join(ROOT, 'snd', 'raw');
  const S = {
    correct: snd(path.join(R, 'sfx_2870.mp3')), wrong: snd(path.join(R, 'sfx_2876.mp3')), pop: snd(path.join(R, 'sfx_2357.mp3')),
    win: snd(path.join(R, 'sfx_270.mp3')), applause: snd(path.join(R, 'sfx_523.mp3')), bell: snd(path.join(R, 'sfx_600.mp3')),
  };
  const FIZ = snd(path.join(ROOT, 'build', 'fizminutka.mp3'));

  const MINERALS = [
    { id: 'coal', n: 'Каменный уголь', img: 'M1', g: 'fuel' }, { id: 'oil', n: 'Нефть', img: 'M2', g: 'fuel' }, { id: 'gas', n: 'Природный газ', img: 'M3', g: 'fuel' },
    { id: 'iron', n: 'Железная руда', img: 'M4', g: 'ore' }, { id: 'sand', n: 'Песок', img: 'M5', g: 'non' }, { id: 'clay', n: 'Глина', img: 'M6', g: 'non' },
    { id: 'lime', n: 'Известняк', img: 'M7', g: 'non' }, { id: 'salt', n: 'Каменная соль', img: 'M8', g: 'non' }];
  const PAIRS = [['oil', 'Бензин для машин', 'FaGasPump'], ['gas', 'Газовая плита', 'FaFire'], ['coal', 'Тепло и электричество', 'FaBolt'],
    ['iron', 'Металл', 'GiMetalBar'], ['sand', 'Стекло', 'FaWineBottle'], ['clay', 'Кирпич и посуда', 'GiBrickWall'], ['lime', 'Строительные материалы', 'FaTrowelBricks']];
  const RULES = [
    ['Оставить свет включённым в пустой комнате', false, 'Свет горит зря — на электростанции сжигают лишнее топливо.'],
    ['Выключить компьютер после окончания работы', true, 'Так мы экономим электроэнергию.'],
    ['Бросить металлическую банку в лесу', false, 'Банка загрязняет лес, а металл можно было переработать.'],
    ['Сдать металлические отходы на переработку', true, 'Из старого металла сделают новые вещи, и руды понадобится меньше.'],
    ['Оставлять воду и электричество расходоваться без необходимости', false, 'Ресурсы тратятся впустую.'],
    ['Использовать вещи повторно, если это возможно', true, 'Чем дольше служит вещь, тем меньше нужно новых материалов.'],
    ['Бережно относиться к природным богатствам', true, 'Запасы полезных ископаемых ограничены — их нужно беречь.']];
  const QUIZ = [
    ['Что относится к полезным ископаемым?', ['нефть', 'облако', 'птица'], 0],
    ['Что получают из железной руды?', ['металл', 'стекло', 'бумагу'], 0],
    ['Какое полезное ископаемое используют как топливо?', ['природный газ', 'песок', 'глина'], 0],
    ['Как следует относиться к полезным ископаемым?', ['расходовать без ограничений', 'бережно и разумно использовать', 'не использовать никогда'], 1],
    ['Из чего делают стекло?', ['из глины', 'из песка', 'из угля'], 1],
    ['Из чего делают кирпич?', ['из глины', 'из нефти', 'из соли'], 0]];

  const pairIcons = Object.fromEntries(PAIRS.map((p) => [p[0], ic(p[2])]));
  const data = { MINERALS, PAIRS: PAIRS.map((p) => [p[0], p[1]]), RULES, QUIZ, TL: { total: TL.total, lines: TL.lines, moves: TL.moves, events: TL.events } };

  const star = ic('FaStar', 'ic star');
  const css = fs.readFileSync(path.join(__dirname, 'site.css'), 'utf8');
  const js = fs.readFileSync(path.join(__dirname, 'site.js'), 'utf8');

  const hallCard = (id, n, title, text, depth, layer, icon) => `
    <article class="hall layer-${layer}">
      <div class="depth"><span>${depth}</span></div>
      <a class="tag" href="#${id}">
        <span class="tag-ic">${ic(icon)}</span>
        <span class="tag-body"><span class="tag-k">Зал ${n}</span><span class="tag-t">${title}</span><span class="tag-d">${text}</span></span>
        <span class="tag-go">Войти ${ic('FaArrowRight')}</span>
        <span class="tag-star" data-star="${id}">${star}</span>
      </a>
    </article>`;

  const body = `
<header class="bar">
  <a class="logo" href="#home" aria-label="На главную">${ic('GiGems')}<span>Кладовые Земли</span></a>
  <div class="stars" aria-live="polite">${star}<b id="starCount">0</b><span>из 6</span></div>
</header>

<main>
<section id="home" class="view">
  <div class="sky">
    <div class="hero">
      <div class="hero-text">
        <p class="eyebrow">Человек и мир · 3 класс</p>
        <h1>Кладовые Земли</h1>
        <p class="lead">Подземный музей полезных ископаемых. Спускайся по слоям, проходи залы и собирай звёзды!</p>
      </div>
      <figure class="guide"><img src="${I.C1}" alt="Юный геолог Мира машет рукой"><figcaption class="bubble">Привет! Я — Мира, юный геолог. Выбирай зал!</figcaption></figure>
    </div>
    ${B1 ? `<img class="cutaway" src="${B1}" alt="Разрез Земли с полезными ископаемыми">` : ''}
  </div>
  <div class="strata">
    ${hallCard('fiz', 1, 'Физкультминутка с ИИ', 'Повторяй движения за Мирой под стихи', 'поверхность', 'grass', 'FaPersonRunning')}
    ${hallCard('sort', 2, 'Собери коллекцию', 'Разложи камни по трём витринам', 'глубина 2 м', 'sand', 'GiGems')}
    ${hallCard('match', 3, 'Что из чего?', 'Соедини полезное ископаемое и то, что из него получают', 'глубина 10 м', 'clay', 'FaLink')}
    ${hallCard('rules', 4, 'Можно или нельзя?', 'Реши, как беречь природные богатства', 'глубина 40 м', 'lime', 'FaThumbsUp')}
    ${hallCard('quiz', 5, 'Мини-тест', 'Шесть вопросов — шесть шагов к звезде', 'глубина 300 м', 'coal', 'FaListCheck')}
    ${hallCard('mood', 6, 'Светофор', 'Покажи, как прошёл урок', 'глубина 600 м', 'ore', 'FaTrafficLight')}
  </div>
</section>

<section id="sort" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Собери коллекцию</h2><p class="task">Нажми на камень, потом на витрину, куда его положить.</p></div>
  <div class="tray" id="tray"></div>
  <div class="cases">
    <button class="case fuel" data-g="fuel"><span class="case-ic">${ic('FaFire')}</span><b>Горючие</b><span class="case-items"></span></button>
    <button class="case ore" data-g="ore"><span class="case-ic">${ic('GiMetalBar')}</span><b>Рудные</b><span class="case-items"></span></button>
    <button class="case non" data-g="non"><span class="case-ic">${ic('GiBrickWall')}</span><b>Нерудные</b><span class="case-items"></span></button>
  </div>
  <p class="hint" id="sortHint" role="status"></p>
</section>

<section id="match" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Что из чего получают?</h2><p class="task">Нажми на полезное ископаемое, потом на то, что из него получают.</p></div>
  <div class="match" id="matchBox"><svg class="lines" id="lines" aria-hidden="true"></svg><div class="col" id="colL"></div><div class="col" id="colR"></div></div>
  <p class="hint" id="matchHint" role="status"></p>
</section>

<section id="rules" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Можно или нельзя?</h2><p class="task">Прочитай и реши: так поступать можно или нельзя?</p></div>
  <div class="rule-card" id="ruleCard">
    <p class="rule-n" id="ruleN"></p><p class="rule-t" id="ruleT"></p>
    <div class="rule-btns"><button class="yes" id="ruleYes">${ic('FaThumbsUp')}<span>Можно</span></button><button class="no" id="ruleNo">${ic('FaThumbsDown')}<span>Нельзя</span></button></div>
    <p class="rule-fb" id="ruleFb" role="status"></p>
    <button class="next" id="ruleNext" hidden>Дальше ${ic('FaArrowRight')}</button>
  </div>
</section>

<section id="quiz" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Мини-тест</h2><p class="task" id="quizN"></p></div>
  <div class="quiz">
    <div class="progress"><i id="quizBar"></i></div>
    <p class="q" id="quizQ"></p>
    <div class="answers" id="quizA"></div>
    <p class="rule-fb" id="quizFb" role="status"></p>
    <button class="next" id="quizNext" hidden>Дальше ${ic('FaArrowRight')}</button>
  </div>
</section>

<section id="fiz" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Физкультминутка</h2><p class="task"><span class="ai">${ic('FaWandMagicSparkles')} Озвучивает ИИ</span> Встань и повторяй движения за Мирой!</p></div>
  <div class="fiz">
    <ol class="poem" id="poem"></ol>
    <div class="stage"${MEADOW ? ` style="background-image: url(${MEADOW}); background-size: cover; background-position: center bottom;"` : ""}>
      <img id="pose" src="${POSE.C1}" alt="Мира показывает движение">
      <div class="controls">
        <button id="fizPlay" class="play">${ic('FaPlay')}<span>Начать</span></button>
        <button id="fizRestart" class="ghost">${ic('FaArrowsRotate')}<span>Сначала</span></button>
      </div>
      <div class="progress"><i id="fizBar"></i></div>
    </div>
  </div>
</section>

<section id="mood" class="view game" hidden>
  <div class="game-head"><a class="back" href="#home">${ic('FaArrowLeft')} К карте</a><h2>Как прошёл урок?</h2><p class="task">Нажми на огонёк светофора.</p></div>
  <div class="mood">
    <div class="light-box">
      <button class="lamp g" data-m="0" aria-label="Зелёный"></button>
      <button class="lamp y" data-m="1" aria-label="Жёлтый"></button>
      <button class="lamp r" data-m="2" aria-label="Красный"></button>
    </div>
    <div class="mood-side">
      <p class="mood-msg" id="moodMsg" role="status">Зелёный — всё понял(а), жёлтый — остались вопросы, красный — нужна помощь.</p>
      <div class="finish">
        <h3>Закончи предложение</h3>
        <ul><li>Сегодня я узнал(а), что…</li><li>Меня удивило…</li><li>Теперь я понимаю, почему…</li><li>Я могу помочь природе, если…</li></ul>
      </div>
    </div>
  </div>
</section>
</main>
<canvas id="confetti" aria-hidden="true"></canvas>
<footer class="foot">Звуки: Mixkit (бесплатная лицензия). Голос физкультминутки создан нейросетью.</footer>`;

  const script = `<script>
const IMG = ${JSON.stringify(I)};
const POSE = ${JSON.stringify(POSE)};
const SND = ${JSON.stringify(S)};
const FIZ_SRC = ${JSON.stringify(FIZ)};
const DATA = ${JSON.stringify(data)};
const PAIR_ICONS = ${JSON.stringify(pairIcons)};
const STAR_SVG = ${JSON.stringify(star)};
${js}
</script>`;

  const head = `<title>Кладовые Земли</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;800;900&family=Unbounded:wght@600;800&display=swap">
<style>${css}</style>`;

  const fragment = head + body + script;
  fs.writeFileSync(path.join(OUT, 'artifact.html'), fragment);
  const full = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">${head}</head><body>${body}${script}</body></html>`;
  fs.writeFileSync(path.join(OUT, 'index.html'), full);
  console.log('site', (full.length / 1e6).toFixed(2), 'MB');
}
main().catch((e) => { console.error(e); process.exit(1); });
