# Сборка презентации «Опора тела и движение»

Исходники, из которых собирается `presentations/Опора_тела_и_движение.pptx`.
Дизайн: только картинки, дизайнерские фоны и шрифты (Unbounded, Nunito, Caveat), без значков и рисованной графики.

1. Шрифты: `python3 mkfonts.py Nunito-VF.ttf` и `python3 mkfonts2.py <папка>` (вариативные шрифты из google/fonts)
   делают статичные начертания; готовые файлы лежат в `../fonts`, их нужно положить в `~/.fonts`.
2. `python3 process_uploads.py <папка с картинками Higgsfield>` убирает водяной знак и вырезает Костика с зелёного фона.
   Готовый результат уже лежит в `img/`.
3. `python3 make_assets.py` делает звуки викторины, `python3 make_backgrounds.py` делает фоны,
   `python3 make_composites.py` делает плитки маршрута, билеты в залы и карточку цели.
   Видео физминутки (`assets/fizminutka.mp4`) — файл автора.
4. QR-коды: `python3 make_qr.py https://kostik-skeleton.lovable.app img/qr_game.png` и
   `python3 make_qr.py https://youtu.be/6C_RWeZtCNg assets/qr_video.png`.
5. `python3 build_deck.py out/deck.pptx && python3 postprocess.py out/deck.pptx` собирает презентацию и встраивает шрифты.

`pptx_fx.py` пишет анимации, триггеры, звуки, видео и 3D-переходы (морф, куб, вихрь и др.) прямо в XML слайдов.
`qa_initial.py` делает копию, где видно, что показано на слайде до первых анимаций.
