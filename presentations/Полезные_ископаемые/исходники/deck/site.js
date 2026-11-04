// ---------- sounds ----------
const sounds = {};
for (const k in SND) { sounds[k] = new Audio(SND[k]); sounds[k].preload = 'auto'; }
function play(k) { const a = sounds[k]; if (!a) return; try { a.pause(); a.currentTime = 0; const p = a.play(); if (p) p.catch(() => {}); } catch (e) {} }
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const shuffle = (arr) => { const a = arr.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const MIN = Object.fromEntries(DATA.MINERALS.map((m) => [m.id, m]));

// ---------- stars ----------
const HALLS = ['fiz', 'sort', 'match', 'rules', 'quiz', 'mood'];
let done = new Set();
function loadStars(saved) {
  let arr = saved && saved.done;
  if (!arr) { try { arr = JSON.parse(localStorage.getItem('kladovye-stars') || '[]'); } catch (e) { arr = []; } }
  done = new Set(arr.filter((h) => HALLS.includes(h)));
}
function saveStars() { try { localStorage.setItem('kladovye-stars', JSON.stringify([...done])); } catch (e) {} }
function renderStars(animate) {
  $('#starCount').textContent = done.size;
  for (const el of $$('[data-star]')) el.classList.toggle('got', done.has(el.dataset.star));
  if (animate) { const s = $('.stars'); s.classList.remove('bump'); void s.offsetWidth; s.classList.add('bump'); }
}
function award(hall) {
  if (done.has(hall)) return;
  done.add(hall); saveStars(); renderStars(true);
  if (done.size === HALLS.length) { setTimeout(() => { play('applause'); confetti(260); }, 600); }
}

// ---------- router ----------
function route() {
  const id = (location.hash || '#home').slice(1);
  const target = document.getElementById(id) && $('#' + id).classList.contains('view') ? id : 'home';
  for (const v of $$('.view')) v.hidden = v.id !== target;
  if (target !== 'fiz') fizStop();
  if (target === 'sort') sortInit();
  if (target === 'match') matchInit();
  if (target === 'rules') rulesInit();
  if (target === 'quiz') quizInit();
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);

// ---------- hall: sort ----------
let sortSel = null, sortLeft = 0;
function sortInit() {
  const tray = $('#tray'); tray.innerHTML = '';
  for (const c of $$('.case-items')) c.innerHTML = '';
  $('#sortHint').textContent = ''; $('#sortHint').className = 'hint';
  sortSel = null; sortLeft = DATA.MINERALS.length;
  for (const m of shuffle(DATA.MINERALS)) {
    const b = document.createElement('button');
    b.className = 'stone'; b.dataset.id = m.id;
    b.innerHTML = `<img src="${IMG[m.img]}" alt=""><span>${m.n}</span>`;
    b.addEventListener('click', () => { play('pop'); for (const s of $$('.stone')) s.classList.remove('sel'); b.classList.add('sel'); sortSel = m.id; });
    tray.appendChild(b);
  }
}
const GROUP_HINT = { fuel: 'Подумай: горит ли он?', ore: 'Подумай: получают ли из него металл?', non: 'Подумай: его используют в стройке или в быту?' };
for (const c of $$('.case')) c.addEventListener('click', () => {
  const hint = $('#sortHint');
  if (!sortSel) { hint.textContent = 'Сначала выбери камень!'; hint.className = 'hint'; return; }
  const m = MIN[sortSel], stone = $(`.stone[data-id="${sortSel}"]`);
  if (m.g === c.dataset.g) {
    play('correct');
    const img = document.createElement('img'); img.src = IMG[m.img]; img.alt = m.n; img.title = m.n;
    c.querySelector('.case-items').appendChild(img);
    stone.remove(); sortSel = null; sortLeft--;
    hint.textContent = `Верно! ${m.n} — ${c.querySelector('b').textContent.toLowerCase()}.`; hint.className = 'hint good';
    if (sortLeft === 0) { hint.textContent = 'Коллекция собрана! Ты получаешь звезду!'; play('win'); confetti(120); award('sort'); }
  } else {
    play('wrong'); c.classList.remove('shake'); void c.offsetWidth; c.classList.add('shake');
    hint.textContent = `Не сюда. ${GROUP_HINT[m.g]}`; hint.className = 'hint bad';
  }
});

// ---------- hall: match ----------
let matchSel = null, matchLeft = 0, matchDone = [];
function matchInit() {
  const L = $('#colL'), R = $('#colR');
  L.innerHTML = ''; R.innerHTML = ''; $('#lines').innerHTML = ''; matchSel = null; matchDone = [];
  $('#matchHint').textContent = ''; $('#matchHint').className = 'hint';
  matchLeft = DATA.PAIRS.length;
  for (const [id] of shuffle(DATA.PAIRS)) {
    const b = document.createElement('button'); b.className = 'item'; b.dataset.id = id;
    b.innerHTML = `<img src="${IMG[MIN[id].img]}" alt=""><span>${MIN[id].n}</span>`;
    b.addEventListener('click', () => { if (b.classList.contains('done')) return; play('pop'); for (const x of $$('#colL .item')) x.classList.remove('sel'); b.classList.add('sel'); matchSel = id; });
    L.appendChild(b);
  }
  for (const [id, use] of shuffle(DATA.PAIRS)) {
    const b = document.createElement('button'); b.className = 'item'; b.dataset.id = id;
    b.innerHTML = `${PAIR_ICONS[id]}<span>${use}</span>`;
    b.addEventListener('click', () => matchPick(b, id));
    R.appendChild(b);
  }
}
function matchPick(b, id) {
  const hint = $('#matchHint');
  if (b.classList.contains('done')) return;
  if (!matchSel) { hint.textContent = 'Сначала выбери полезное ископаемое слева!'; hint.className = 'hint'; return; }
  const left = $(`#colL .item[data-id="${matchSel}"]`);
  if (id === matchSel) {
    play('correct'); left.classList.remove('sel'); left.classList.add('done'); b.classList.add('done');
    matchDone.push(id); drawLines(); matchSel = null; matchLeft--;
    hint.textContent = 'Верно!'; hint.className = 'hint good';
    if (matchLeft === 0) { hint.textContent = 'Все пары найдены! Звезда твоя!'; play('win'); confetti(120); award('match'); }
  } else {
    play('wrong'); b.classList.remove('shake'); void b.offsetWidth; b.classList.add('shake');
    hint.textContent = 'Попробуй другой ответ.'; hint.className = 'hint bad';
  }
}
function drawLines() {
  const svg = $('#lines'), box = $('#matchBox').getBoundingClientRect();
  svg.innerHTML = matchDone.map((id) => {
    const a = $(`#colL .item[data-id="${id}"]`).getBoundingClientRect(), b = $(`#colR .item[data-id="${id}"]`).getBoundingClientRect();
    return `<line x1="${a.right - box.left}" y1="${a.top + a.height / 2 - box.top}" x2="${b.left - box.left}" y2="${b.top + b.height / 2 - box.top}"/>`;
  }).join('');
}
window.addEventListener('resize', () => { if (!$('#match').hidden) drawLines(); });

// ---------- hall: rules ----------
let ruleI = 0, ruleScore = 0;
const ruleHTML = $('#ruleCard').innerHTML;
function rulesInit() {
  $('#ruleCard').innerHTML = ruleHTML;
  $('#ruleYes').addEventListener('click', () => ruleAnswer(true));
  $('#ruleNo').addEventListener('click', () => ruleAnswer(false));
  $('#ruleNext').addEventListener('click', () => { ruleI++; ruleShow(); });
  ruleI = 0; ruleScore = 0; ruleShow();
}
function ruleShow() {
  const card = $('#ruleCard');
  if (ruleI >= DATA.RULES.length) {
    card.innerHTML = `<div class="result"><p class="rule-n">Игра окончена</p><p class="rule-t">Правильных ответов: ${ruleScore} из ${DATA.RULES.length}</p><p class="rule-fb good">${ruleScore >= 6 ? 'Ты знаешь, как беречь природные богатства!' : 'Хорошо! Сыграй ещё раз — получится ещё лучше.'}</p><button class="ghost" id="ruleAgain">Сыграть ещё раз</button><a class="next" href="#home">К карте музея</a></div>`;
    $('#ruleAgain').addEventListener('click', rulesInit); play('win'); confetti(100); award('rules'); return;
  }
  const [t] = DATA.RULES[ruleI];
  $('#ruleN').textContent = `Ситуация ${ruleI + 1} из ${DATA.RULES.length}`;
  $('#ruleT').textContent = t; $('#ruleFb').textContent = ''; $('#ruleFb').className = 'rule-fb';
  $('#ruleYes').disabled = false; $('#ruleNo').disabled = false; $('#ruleNext').hidden = true;
}
function ruleAnswer(yes) {
  const [, ok, why] = DATA.RULES[ruleI];
  const fb = $('#ruleFb');
  if (yes === ok) { play('correct'); ruleScore++; fb.textContent = `Верно! ${why}`; fb.className = 'rule-fb good'; }
  else { play('wrong'); fb.textContent = `Не совсем. ${ok ? 'Так поступать можно.' : 'Так поступать нельзя.'} ${why}`; fb.className = 'rule-fb bad'; $('#ruleCard').classList.remove('shake'); void $('#ruleCard').offsetWidth; $('#ruleCard').classList.add('shake'); }
  $('#ruleYes').disabled = true; $('#ruleNo').disabled = true; $('#ruleNext').hidden = false; $('#ruleNext').focus();
}

// ---------- hall: quiz ----------
let qI = 0, qScore = 0, qTried = false;
const quizHTML = $('.quiz').innerHTML;
function quizInit() { $('.quiz').innerHTML = quizHTML; bindQuiz(); qI = 0; qScore = 0; quizShow(); }
function bindQuiz() { $('#quizNext').addEventListener('click', () => { qI++; quizShow(); }); }
function quizShow() {
  if (qI >= DATA.QUIZ.length) {
    const n = qScore >= 6 ? 3 : qScore >= 4 ? 2 : qScore >= 2 ? 1 : 0;
    $('#quizN').textContent = 'Результат';
    $('.quiz').innerHTML = `<div class="result"><div class="big-stars">${[0, 1, 2].map((i) => `<span class="${i < n ? 'on' : ''}">${STAR_SVG}</span>`).join('')}</div>
      <p class="q">С первого раза: ${qScore} из ${DATA.QUIZ.length}</p><p class="rule-fb good">${n === 3 ? 'Превосходно! Ты знаток полезных ископаемых!' : 'Молодец! Можно пройти тест ещё раз.'}</p>
      <div class="controls"><button class="ghost" id="quizAgain">Пройти ещё раз</button><a class="next" href="#home">К карте музея</a></div></div>`;
    $('#quizAgain').addEventListener('click', quizInit);
    play(n === 3 ? 'applause' : 'win'); confetti(n * 60 + 40); award('quiz'); return;
  }
  const [q, ans, ok] = DATA.QUIZ[qI];
  qTried = false;
  $('#quizN').textContent = `Вопрос ${qI + 1} из ${DATA.QUIZ.length}`;
  $('#quizBar').style.width = `${(qI / DATA.QUIZ.length) * 100}%`;
  $('#quizQ').textContent = q; $('#quizFb').textContent = ''; $('#quizFb').className = 'rule-fb'; $('#quizNext').hidden = true;
  const box = $('#quizA'); box.innerHTML = '';
  ans.forEach((a, i) => {
    const b = document.createElement('button');
    b.innerHTML = `<span class="letter">${'АБВ'[i]}</span><span>${a}</span>`;
    b.addEventListener('click', () => {
      if (!$('#quizNext').hidden) return;
      if (i === ok) {
        play('correct'); b.classList.add('right'); if (!qTried) qScore++;
        $('#quizFb').textContent = 'Верно!'; $('#quizFb').className = 'rule-fb good'; $('#quizNext').hidden = false;
        $('#quizBar').style.width = `${((qI + 1) / DATA.QUIZ.length) * 100}%`;
      } else {
        play('wrong'); qTried = true; b.classList.add('wrong'); b.classList.remove('shake'); void b.offsetWidth; b.classList.add('shake');
        $('#quizFb').textContent = 'Попробуй ещё раз!'; $('#quizFb').className = 'rule-fb bad';
      }
    });
    box.appendChild(b);
  });
}

// ---------- hall: fiz (same audio, poses and timing as in the presentation) ----------
const fizAudio = new Audio(FIZ_SRC); fizAudio.preload = 'auto';
const poem = $('#poem');
DATA.TL.lines.forEach((l, i) => { const li = document.createElement('li'); li.innerHTML = `<span class="n">${i + 1}</span><span><b>${l}</b><small>${DATA.TL.moves[i]}</small></span>`; poem.appendChild(li); });
const EVENTS = DATA.TL.events.slice().sort((a, b) => a.t - b.t);
let fizRaf = 0, lastPose = '', lastLine = -2;
function setPose(code) {
  if (code === lastPose) return; lastPose = code;
  const img = $('#pose'); const flip = code === 'P3m';
  img.src = POSE[flip ? 'P3' : code] || POSE.C1; img.classList.toggle('flip', flip);
}
function setLine(i) {
  if (i === lastLine) return; lastLine = i;
  $$('#poem li').forEach((li, k) => li.classList.toggle('on', k === i));
}
function fizTick() {
  const t = fizAudio.currentTime;
  let ev = null;
  for (const e of EVENTS) { if (e.t <= t + 0.02) ev = e; else break; }
  if (ev) { setPose(ev.pose); setLine(ev.line); }
  $('#fizBar').style.width = `${Math.min(100, (t / DATA.TL.total) * 100)}%`;
  if (!fizAudio.paused) fizRaf = requestAnimationFrame(fizTick);
}
function fizSetBtn(playing) { $('#fizPlay').innerHTML = playing ? `${ICON_PAUSE}<span>Пауза</span>` : `${ICON_PLAY}<span>${fizAudio.currentTime > 0 && !fizAudio.ended ? 'Дальше' : 'Начать'}</span>`; }
const ICON_PLAY = $('#fizPlay svg').outerHTML;
const ICON_PAUSE = '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="4" width="5" height="16" rx="1.5"/><rect x="14" y="4" width="5" height="16" rx="1.5"/></svg>';
$('#fizPlay').addEventListener('click', () => {
  if (fizAudio.paused) { const p = fizAudio.play(); if (p) p.catch(() => {}); fizSetBtn(true); cancelAnimationFrame(fizRaf); fizRaf = requestAnimationFrame(fizTick); }
  else { fizAudio.pause(); fizSetBtn(false); }
});
$('#fizRestart').addEventListener('click', () => { fizAudio.currentTime = 0; lastPose = ''; lastLine = -2; const p = fizAudio.play(); if (p) p.catch(() => {}); fizSetBtn(true); cancelAnimationFrame(fizRaf); fizRaf = requestAnimationFrame(fizTick); });
fizAudio.addEventListener('ended', () => { fizSetBtn(false); setLine(-1); setPose('C4'); $('#fizBar').style.width = '100%'; award('fiz'); confetti(80); });
function fizStop() { if (!fizAudio.paused) { fizAudio.pause(); fizSetBtn(false); } }

// ---------- hall: mood ----------
const MOOD = ['Отлично! Ты всё понял(а) и можешь объяснить другу.', 'Хорошо! Задай учителю свой вопрос — вместе разберётесь.', 'Ничего страшного! Учитель обязательно поможет.'];
for (const l of $$('.lamp')) l.addEventListener('click', () => {
  for (const x of $$('.lamp')) x.classList.remove('on');
  l.classList.add('on'); play('bell'); $('#moodMsg').textContent = MOOD[+l.dataset.m]; award('mood');
});

// ---------- confetti ----------
const cv = $('#confetti'), cx = cv.getContext('2d');
let parts = [], confRaf = 0;
function confetti(n) {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  cv.width = innerWidth * devicePixelRatio; cv.height = innerHeight * devicePixelRatio;
  const cols = ['#F5A524', '#1FA463', '#4A7BD0', '#F2643D', '#EF5B5B', '#FFD27A'];
  for (let i = 0; i < n; i++) parts.push({ x: Math.random() * cv.width, y: -20 - Math.random() * cv.height * 0.3, vx: (Math.random() - 0.5) * 4, vy: 3 + Math.random() * 5, r: Math.random() * 6.3, vr: (Math.random() - 0.5) * 0.3, s: (6 + Math.random() * 8) * devicePixelRatio, c: cols[i % cols.length] });
  if (!confRaf) confRaf = requestAnimationFrame(confStep);
}
function confStep() {
  cx.clearRect(0, 0, cv.width, cv.height);
  parts = parts.filter((p) => p.y < cv.height + 40);
  for (const p of parts) { p.x += p.vx; p.y += p.vy; p.r += p.vr; p.vy += 0.05; cx.save(); cx.translate(p.x, p.y); cx.rotate(p.r); cx.fillStyle = p.c; cx.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2); cx.restore(); }
  confRaf = parts.length ? requestAnimationFrame(confStep) : 0;
  if (!confRaf) cx.clearRect(0, 0, cv.width, cv.height);
}

// ---------- boot ----------
function start(saved) { loadStars(saved); renderStars(false); route(); }
window.claude?.hot?.snapshot?.(() => ({ done: [...done] }));
window.claude?.hot?.ready ? window.claude.hot.ready(start) : start(window.claude?.hot?.data ?? {});
