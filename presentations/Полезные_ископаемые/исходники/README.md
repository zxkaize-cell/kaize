# Исходники презентации и сайта

Сборка (Node 22, Python 3, ffmpeg):

1. `tools/tts.py` — нейросетевая озвучка фраз физкультминутки (`media/phrases.json`).
2. `tools/mix_exercise.py` — сведение голоса с музыкой → `media/fizminutka.mp3` и тайминги `media/fizminutka_timeline.json`.
3. `deck/build.js` — слайды (pptxgenjs).
4. `tools/anim.py` — анимации появления, триггеры со звуками, переходы по ссылкам, автозапуск озвучки.
5. `tools/xsdcheck.py` — проверка слайдов по схеме PowerPoint.
6. `deck/build_site.js` — сайт «Кладовые Земли» одним файлом.

Картинки: 20 из OpenART (Wan 2.7 Image, четыре листа) и 8 из Figma (GPT Image 2.5 Flare), промты — в `Промты_для_картинок.md`:
- `tools/split_sheets.py` — разрезает листы на отдельные картинки и вырезает белый фон;
- `tools/unwatermark2.py` — снимает логотип бесплатного тарифа OpenART со сцен (шаблон логотипа — `tools/tmpl_M.png`);
- `tools/pose_norm.py` — приводит позы физкультминутки к одному масштабу.
Готовые картинки: `img/cut` (персонаж и минералы без фона), `img/pose` (позы физкультминутки), `img/raw` (сцены и титульное фото).
Звуки: Mixkit (бесплатная лицензия), музыка «Gummies» (Mixkit). Голос: Microsoft Neural TTS (ru-RU-SvetlanaNeural).

## Сайт на Lovable

Основная версия сайта — https://kladovye-zemli.lovable.app (проект Lovable «Кладовые Земли»). Картинки, звуки и тайминги физкультминутки он берёт из папки `lovable-assets/minerals/` этого репозитория через jsDelivr, поэтому репозиторий должен оставаться публичным. `tools/lovable_test.js` — автотест опубликованного сайта.
Запасные версии: `Сайт_Кладовые_Земли.html` (работает без интернета) и страница на claude.ai.
