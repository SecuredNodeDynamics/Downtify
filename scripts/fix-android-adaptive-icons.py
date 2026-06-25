#!/usr/bin/env python3
"""Fix Android adaptive launcher icons after @capacitor/assets generation.

Capacitor emits a black background layer plus an inset green-circle foreground,
which shows black borders under circle/squircle launcher masks. This script
switches to a solid brand-green background and transparent arrow-only foregrounds.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
RES = REPO_ROOT / 'frontend/android/app/src/main/res'
BRAND_GREEN = '#1AD35D'
TARGET_FILL = 0.60
DENSITIES = ('ldpi', 'mdpi', 'hdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi')

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


def arrow_only(im: Image.Image) -> Image.Image:
    im = im.convert('RGBA')
    w, h = im.size
    src = im.load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = src[x, y]
            if a < 250:
                continue
            bright = max(r, g, b)
            t = (200 - bright) / 200.0
            if t <= 0.05:
                continue
            dst[x, y] = (0, 0, 0, int(max(0.0, min(1.0, t)) * 255))
    return out


def fix_foregrounds() -> None:
    for density in DENSITIES:
        path = RES / f'mipmap-{density}' / 'ic_launcher_foreground.png'
        if not path.is_file():
            continue
        im = Image.open(path)
        cw, ch = im.size
        arrow = arrow_only(im)
        bbox = arrow.getbbox()
        if not bbox:
            raise SystemExit(f'no arrow found in {path}')
        cropped = arrow.crop(bbox)
        aw, ah = cropped.size
        scale = (TARGET_FILL * min(cw, ch)) / max(aw, ah)
        nw, nh = max(1, round(aw * scale)), max(1, round(ah * scale))
        cropped = cropped.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        canvas.paste(cropped, ((cw - nw) // 2, (ch - nh) // 2), cropped)
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
