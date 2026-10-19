# -*- coding: utf-8 -*-
"""生成手绘风 tabBar 图标（81x81 PNG，抖动描边，透明底）。
用法：python tools/gen_tabbar_icons.py
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "static" / "tabbar"
GRAY = (160, 164, 190, 255)
LILAC = (108, 123, 245, 255)
W = 4
random.seed(7)


def jitter(pts, amp=1.4):
    return [(x + random.uniform(-amp, amp), y + random.uniform(-amp, amp)) for x, y in pts]


def sketch(d, pts, c, width=W, passes=2, closed=False):
    path = list(pts) + ([pts[0]] if closed else [])
    for i in range(passes):
        d.line(jitter(path, 1.2), fill=c, width=max(1, width - (i % 2)), joint="curve")


def loop(cx, cy, rx, ry, n=48):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def home(d, c):
    sketch(d, [(40, 14), (66, 36), (14, 36)], c, closed=True)
    sketch(d, [(22, 38), (22, 66), (58, 66), (58, 38)], c)
    sketch(d, [(36, 50), (36, 66)], c, W - 1)
    sketch(d, [(46, 50), (46, 66)], c, W - 1)


def bill(d, c):
    sketch(d, [(19, 14), (62, 13), (63, 67), (19, 68)], c, closed=True)
    for y in (28, 40, 52):
        sketch(d, [(28, y), (52, y - 1)], c, W - 1, 1)


def ai(d, c):
    star = [(40, 12), (46, 34), (68, 40), (46, 46), (40, 68),
            (34, 46), (12, 40), (34, 34)]
    rough = []
    for x, y in star:
        rough.append((x + random.uniform(-1.6, 1.6), y + random.uniform(-1.6, 1.6)))
    sketch(d, rough, c, closed=True)
    d.ellipse([36, 36, 44, 44], fill=c)
    d.ellipse([59, 12, 65, 18], outline=c, width=2)
    d.ellipse([15, 59, 21, 65], outline=c, width=2)


def note(d, c):
    sketch(d, [(18, 14), (62, 12), (64, 65), (17, 67)], c, closed=True)
    for y in (28, 40, 52):
        sketch(d, [(27, y), (51, y + 1)], c, W - 1, 1)


def profile(d, c):
    sketch(d, loop(40, 26, 12, 13), c)
    d.arc([16, 42, 64, 84], 180, 360, fill=c, width=W)


ICONS = {"home": home, "bill": bill, "ai": ai, "note": note, "profile": profile}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in ICONS.items():
        for suffix, color in (("", GRAY), ("-active", LILAC)):
            img = Image.new("RGBA", (81, 81), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            fn(d, color)
            img.save(OUT / f"{name}{suffix}.png")
            print("saved", OUT / f"{name}{suffix}.png")


if __name__ == "__main__":
    main()
