#!/usr/bin/env python3
"""Fix Android adaptive launcher icons after @capacitor/assets generation.

Capacitor emits a black background layer plus an inset green-circle foreground,
which shows black borders under circle/squircle launcher masks. This script
switches to a solid brand-green background and renders a crisp, transparent
arrow-only foreground (from the bundled SVG path) sized for the safe zone.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cairosvg
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
RES = REPO_ROOT / 'frontend/android/app/src/main/res'
BRAND_GREEN = '#1AD35D'
# Arrow longest side as a fraction of the full adaptive-icon canvas. Adaptive
# icons reserve the outer ~33% for masking, so keep the logo comfortably inside.
TARGET_FILL = 0.42
DENSITIES = ('ldpi', 'mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi')

# Solid download arrow (the Downtify mark) with no circle/background, matched to
# frontend/src/assets/downtify.svg so foregrounds render crisply at any size.
ARROW_SVG = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="1024" height="1024" viewBox="0 0 67.733332 67.733333"
     version="1.1" xmlns="http://www.w3.org/2000/svg">
  <g style="fill:#040000;fill-opacity:1"
     transform="matrix(0.06566918,0,0,0.06566918,17.061212,17.059932)">
    <path d="M 480.6,111.5 H 406.5 V 35.6 c 0,-10.7 -8.3,-19.6 -19,-20.4 -104,-7.5 -200.4,-3.7 -263,0.8 -10.7,0.8 -19,9.8 -19,20.5 v 74.9 H 31.4 c -10.9,0 -20.9,8.8 -20.6,22 40.6,166 230.9,361.7 230.9,361.7 9.8,10.8 25.6,4 28.6,0 0,0 177.1,-165.8 230.3,-359.4 1.6,-5.8 -0.5,-24.3 -20,-24.2 z"
          style="fill:#040000;fill-opacity:1" />
  </g>
</svg>
"""

ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@mipmap/ic_launcher_foreground" />
</adaptive-icon>
"""

COLOR_XML = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">{BRAND_GREEN}</color>
</resources>
"""


def arrow_master() -> Image.Image:
    png = cairosvg.svg2png(
        bytestring=ARROW_SVG.encode('utf-8'),
        output_width=1024,
        output_height=1024,
    )
    im = Image.open(BytesIO(png)).convert('RGBA')
    bbox = im.getbbox()
    if not bbox:
        raise SystemExit('arrow SVG rendered empty')
    return im.crop(bbox)


def fix_foregrounds() -> None:
    arrow = arrow_master()
    aw, ah = arrow.size
    for density in DENSITIES:
        path = RES / f'mipmap-{density}' / 'ic_launcher_foreground.png'
        if not path.is_file():
            continue
        cw, ch = Image.open(path).size
        scale = (TARGET_FILL * min(cw, ch)) / max(aw, ah)
        nw, nh = max(1, round(aw * scale)), max(1, round(ah * scale))
        resized = arrow.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        canvas.paste(resized, ((cw - nw) // 2, (ch - nh) // 2), resized)
        canvas.save(path)


def fix_xml() -> None:
    (RES / 'values' / 'ic_launcher_background.xml').write_text(
        COLOR_XML, encoding='utf-8'
    )
    for name in ('ic_launcher.xml', 'ic_launcher_round.xml'):
        (RES / 'mipmap-anydpi-v26' / name).write_text(
            ADAPTIVE_XML, encoding='utf-8'
        )


def main() -> None:
    fix_foregrounds()
    fix_xml()
    print('Fixed Android adaptive launcher icons')


if __name__ == '__main__':
    main()
