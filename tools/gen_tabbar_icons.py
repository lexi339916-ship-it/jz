# -*- coding: utf-8 -*-
"""生成 uni-app tabBar 图标（81x81 PNG，透明底，线条风格）。
用法：python tools/gen_tabbar_icons.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "static" / "tabbar"
GRAY = (124, 133, 149, 255)
BLUE = (47, 111, 237, 255)
W = 5  # 线宽


def home(d, c):
    d.polygon([(40, 14), (68, 38), (13, 38)], outline=c, width=W)
    d.rounded_rectangle([21, 38, 60, 66], radius=6, outline=c, width=W)
    d.rectangle([36, 50, 46, 66], outline=c, width=W - 1)


def bill(d, c):
    d.rounded_rectangle([18, 13, 63, 68], radius=8, outline=c, width=W)
    d.line([28, 28, 53, 28], fill=c, width=W - 1)
    d.line([28, 40, 53, 40], fill=c, width=W - 1)
    d.line([28, 52, 44, 52], fill=c, width=W - 1)


def ai(d, c):
    # 四角星形（AI 助手）
    d.polygon([(40, 12), (46, 34), (68, 40), (46, 46),
               (40, 68), (34, 46), (12, 40), (34, 34)], outline=c, width=W)
    d.ellipse([36, 36, 44, 44], fill=c)
    d.ellipse([58, 12, 66, 20], outline=c, width=W - 2)
    d.ellipse([14, 58, 22, 66], outline=c, width=W - 2)


def note(d, c):
    d.rounded_rectangle([16, 13, 64, 66], radius=8, outline=c, width=W)
    d.line([28, 28, 52, 28], fill=c, width=W - 1)
    d.line([28, 40, 52, 40], fill=c, width=W - 1)
    d.line([28, 52, 52, 52], fill=c, width=W - 1)


def profile(d, c):
    d.ellipse([28, 13, 53, 38], outline=c, width=W)
    d.arc([17, 42, 64, 84], start=180, end=360, fill=c, width=W)


ICONS = {"home": home, "bill": bill, "ai": ai, "note": note, "profile": profile}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw_fn in ICONS.items():
        for suffix, color in (("", GRAY), ("-active", BLUE)):
            img = Image.new("RGBA", (81, 81), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            draw_fn(d, color)
            img.save(OUT / f"{name}{suffix}.png")
            print("saved", OUT / f"{name}{suffix}.png")


if __name__ == "__main__":
    main()
