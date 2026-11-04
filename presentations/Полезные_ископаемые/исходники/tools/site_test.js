const { chromium } = require('playwright');
(async () => {
  const file = 'file://' + process.argv[2];
  const out = process.argv[3];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const errs = [];
  p.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  await p.goto(file);
  await p.waitForTimeout(800);
  await p.screenshot({ path: out + '_home.png' });
  await p.goto(file + '#sort'); await p.waitForTimeout(300);
  const groups = { 'Каменный уголь': 'fuel', 'Нефть': 'fuel', 'Природный газ': 'fuel', 'Железная руда': 'ore', 'Песок': 'non', 'Глина': 'non', 'Известняк': 'non', 'Каменная соль': 'non' };
  for (let k = 0; k < 8; k++) {
    const s = await p.$('.stone'); if (!s) break;
    const n = (await s.innerText()).trim();
    await s.click(); await p.click('.case.' + groups[n]);
  }
  console.log('sort hint:', await p.innerText('#sortHint'));
  await p.screenshot({ path: out + '_sort.png' });
  await p.goto(file + '#match'); await p.waitForTimeout(300);
  for (const id of ['oil', 'gas', 'coal', 'iron', 'sand', 'clay', 'lime']) {
    await p.click('#colL .item[data-id="' + id + '"]'); await p.click('#colR .item[data-id="' + id + '"]');
  }
  console.log('match hint:', await p.innerText('#matchHint'));
  await p.screenshot({ path: out + '_match.png' });
  await p.goto(file + '#rules'); await p.waitForTimeout(300);
  for (let k = 0; k < 7; k++) { await p.click('#ruleYes'); await p.click('#ruleNext'); }
  console.log('rules:', (await p.innerText('#ruleCard')).replace(/\n/g, ' | '));
  await p.goto(file + '#home'); await p.goto(file + '#rules'); await p.waitForTimeout(200);
  console.log('rules again:', (await p.innerText('#ruleN')));
  await p.goto(file + '#quiz'); await p.waitForTimeout(300);
  const okIdx = [0, 0, 0, 1, 1, 0];
  for (const i of okIdx) { const bs = await p.$$('#quizA button'); await bs[i].click(); await p.click('#quizNext'); }
  console.log('quiz:', (await p.innerText('.quiz')).replace(/\n/g, ' | '));
  await p.goto(file + '#fiz'); await p.waitForTimeout(300);
  await p.click('#fizPlay'); await p.waitForTimeout(9000);
  console.log('fiz line on:', await p.$$eval('#poem li.on', (x) => x.map((e) => e.innerText.split('\n')[1])), 'time', await p.evaluate(() => fizAudio.currentTime.toFixed(1)));
  await p.screenshot({ path: out + '_fiz.png' });
  await p.goto(file + '#mood'); await p.click('.lamp.g');
  console.log('stars:', await p.innerText('#starCount'));
  await p.goto(file + '#home'); await p.waitForTimeout(300);
  await p.screenshot({ path: out + '_homefull.png', fullPage: true });
  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  await m.goto(file); await m.waitForTimeout(500);
  console.log('mobile scrollWidth', await m.evaluate(() => document.documentElement.scrollWidth));
  await m.screenshot({ path: out + '_mobile.png' });
  console.log('errors:', errs);
  await b.close();
})();
