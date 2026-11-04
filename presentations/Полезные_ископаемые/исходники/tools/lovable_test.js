const { chromium } = require('playwright');
(async () => {
  const base = process.argv[2].replace(/\/$/, '');
  const out = process.argv[3];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 820 } });
  const errs = [], failed = [];
  p.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text().slice(0, 200)); });
  p.on('requestfailed', (r) => failed.push(r.url().slice(-60) + ' ' + (r.failure() || {}).errorText));
  const imgsOk = async () => p.$$eval('img', (xs) => xs.map((x) => [x.getAttribute('src') ? x.getAttribute('src').split('/').pop() : '', x.complete && x.naturalWidth > 0]).filter((x) => !x[1]).map((x) => x[0]));

  await p.goto(base + '/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);
  const body = await p.innerText('body');
  console.log('home has title:', body.includes('Кладовые Земли'), '| halls:', ['Физкультминутка с ИИ', 'Собери коллекцию', 'Что из чего', 'Можно или нельзя', 'Мини-тест', 'Светофор'].map((t) => body.includes(t) ? 1 : 0).join(''));
  console.log('home broken images:', await imgsOk());
  await p.screenshot({ path: out + '_home.png' });
  await p.screenshot({ path: out + '_homefull.png', fullPage: true });

  // sort game: pick each stone and drop into right case
  await p.goto(base + '/sort', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  const groups = { 'Каменный уголь': 'Горючие', 'Нефть': 'Горючие', 'Природный газ': 'Горючие', 'Железная руда': 'Рудные', 'Песок': 'Нерудные', 'Глина': 'Нерудные', 'Известняк': 'Нерудные', 'Каменная соль': 'Нерудные' };
  for (const [name, g] of Object.entries(groups)) {
    const tile = p.getByRole('button', { name: new RegExp('^\\s*' + name + '\\s*$') }).first();
    if (await tile.count()) { await tile.click(); await p.getByRole('button', { name: new RegExp(g) }).first().click(); await p.waitForTimeout(150); }
    else console.log('  sort: tile not found', name);
  }
  const sortText = await p.innerText('main').catch(() => p.innerText('body'));
  console.log('sort done msg:', /Коллекция собрана/.test(sortText));
  await p.screenshot({ path: out + '_sort.png' });

  // match game
  await p.goto(base + '/match', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  const pairs = [['Нефть', 'Бензин для машин'], ['Природный газ', 'Газовая плита'], ['Каменный уголь', 'Тепло и электричество'], ['Железная руда', 'Металл'], ['Песок', 'Стекло'], ['Глина', 'Кирпич и посуда'], ['Известняк', 'Строительные материалы']];
  for (const [l, r] of pairs) {
    const L = p.getByRole('button', { name: new RegExp('^\\s*' + l + '\\s*$') }).first();
    const R = p.getByRole('button', { name: new RegExp(r) }).first();
    if (await L.count() && await R.count()) { await L.click(); await R.click(); await p.waitForTimeout(150); } else console.log('  match: not found', l, r);
  }
  console.log('match done msg:', /Все пары найдены/.test(await p.innerText('body')));
  await p.screenshot({ path: out + '_match.png' });

  // quiz
  await p.goto(base + '/quiz', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  for (const a of ['нефть', 'металл', 'природный газ', 'бережно и разумно использовать', 'из песка', 'из глины']) {
    const btn = p.getByRole('button', { name: new RegExp(a) }).first();
    if (await btn.count()) { await btn.click(); await p.waitForTimeout(150); const next = p.getByRole('button', { name: /Дальше/ }).first(); if (await next.count()) await next.click(); await p.waitForTimeout(150); } else console.log('  quiz: answer not found', a);
  }
  console.log('quiz result:', /С первого раза: 6 из 6/.test(await p.innerText('body')));

  // rules
  await p.goto(base + '/rules', { waitUntil: 'networkidle' }); await p.waitForTimeout(800);
  for (let k = 0; k < 7; k++) { const y = p.getByRole('button', { name: /Можно/ }).first(); if (await y.count()) await y.click(); await p.waitForTimeout(120); const n = p.getByRole('button', { name: /Дальше/ }).first(); if (await n.count()) await n.click(); await p.waitForTimeout(120); }
  console.log('rules end:', /Игра окончена/.test(await p.innerText('body')));

  // fiz
  await p.goto(base + '/fiz', { waitUntil: 'networkidle' }); await p.waitForTimeout(1000);
  const start = p.getByRole('button', { name: /Начать/ }).first();
  console.log('fiz start button:', await start.count());
  if (await start.count()) await start.click();
  await p.waitForTimeout(9500);
  const t = await p.evaluate(() => { const a = [...document.querySelectorAll('audio')]; return a.length ? a[0].currentTime : (window.__fizTime || null); });
  const poseSrcs = await p.$$eval('img', (xs) => xs.filter((x) => /pose-/.test(x.src) && x.offsetParent !== null).map((x) => x.src.split('/').pop() + (getComputedStyle(x).transform !== 'none' ? '(t)' : '')));
  console.log('fiz audio element time:', t, '| visible pose imgs:', poseSrcs.slice(0, 4));
  const fizText = await p.innerText('body');
  console.log('fiz lines present:', fizText.includes('Мы копаем глубоко'), fizText.includes('Землю нашу сохраняем'));
  await p.screenshot({ path: out + '_fiz.png' });

  await p.goto(base + '/mood', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
  const lamp = p.getByRole('button', { name: /Зел/ }).first();
  if (await lamp.count()) await lamp.click();
  console.log('mood msg:', /Отлично!/.test(await p.innerText('body')));
  await p.goto(base + '/', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
  console.log('stars text:', (await p.innerText('header').catch(() => '')).replace(/\s+/g, ' '));

  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  await m.goto(base + '/', { waitUntil: 'networkidle' }); await m.waitForTimeout(800);
  console.log('mobile scrollWidth', await m.evaluate(() => document.documentElement.scrollWidth));
  await m.screenshot({ path: out + '_mobile.png' });
  console.log('errors:', errs.slice(0, 8));
  console.log('failed requests:', failed.slice(0, 8));
  await b.close();
})();
