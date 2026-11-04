# Исходники презентации и сайта

Сборка (Node 22, Python 3, ffmpeg):

1. `tools/tts.py` — нейросетевая озвучка фраз физкультминутки (`media/phrases.json`).
2. `tools/mix_exercise.py` — сведение голоса с музыкой → `media/fizminutka.mp3` и тайминги `media/fizminutka_timeline.json`.
3. `deck/build.js` — слайды (pptxgenjs).
4. `tools/anim.py` — анимации появления, триггеры со звуками, переходы по ссылкам, автозапуск озвучки.
5. `tools/xsdcheck.py` — проверка слайдов по схеме PowerPoint.
6. `deck/build_site.js` — сайт «Кладовые Земли» одним файлом.

Картинки кладутся в `img/raw/<код>.png` (сцены) и `img/cut/<код>.png` (персонаж, минералы и предметы с прозрачным фоном). Коды — в `Промты_для_картинок.md`.
Звуки: Mixkit (бесплатная лицензия), музыка «Gummies» (Mixkit). Голос: Microsoft Neural TTS (ru-RU-SvetlanaNeural).
