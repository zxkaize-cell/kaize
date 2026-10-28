# Сборка презентации «Опора тела и движение»

Исходники, из которых собирается `Опора_тела_и_движение.pptx`.

1. `python3 mkfonts.py Nunito-VF.ttf` — статичные начертания Nunito (вариативный шрифт берётся из google/fonts), положить в `~/.fonts`.
2. `python3 make_assets.py` — фоны, иконки (Noto Color Emoji), звуки викторины, QR-код видео.
3. `python3 img/fetch_images.py [папка_с_картинками]` — иллюстрации Higgsfield из `img/manifest.json`; маскот вырезается с зелёного фона.
4. `python3 make_qr.py https://kostik-skeleton.lovable.app img/qr_game.png`
5. `python3 build_deck.py out/deck.pptx && python3 postprocess.py out/deck.pptx` — сборка и встраивание шрифта.

`pptx_fx.py` пишет анимации, триггеры, звуки и 3D-переходы (морф, куб, вихрь и др.) прямо в XML слайдов.
`qa_initial.py` делает копию, где видно, что показано на слайде до первых анимаций.
