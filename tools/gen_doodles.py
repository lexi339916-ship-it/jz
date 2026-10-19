# -*- coding: utf-8 -*-
"""生成手绘涂鸦素材（抖动线条 + 低饱和配色 + 透明底）。

用随机抖动模拟铅笔/蜡笔笔触：每条轮廓画两到三遍，宽度略有变化。
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "static" / "doodles"
random.seed(20261019)

INK = (92, 94, 122, 230)
INK_SOFT = (92, 94, 122, 150)
CREAM = (255, 249, 236, 255)
PINK = (246, 201, 207, 210)
PINK_SOFT = (248, 216, 220, 160)
LILAC = (198, 191, 241, 200)
MINT = (191, 231, 214, 200)
YELLOW = (250, 226, 172, 220)
BLUE = (189, 207, 246, 200)


def jitter(pts, amp=1.8):
    return [(x + random.uniform(-amp, amp), y + random.uniform(-amp, amp)) for x, y in pts]


def sketch(d, pts, color=INK, width=3, passes=2, amp=1.8):
    """抖动多遍描线，模拟手绘线条。"""
    for i in range(passes):
        p = jitter(pts, amp)
        d.line(p, fill=color, width=max(1, width - (i % 2)), joint="curve")


def loop(cx, cy, rx, ry, n=64, rot=0.0):
    pts = []
    for i in range(n + 1):
        t = 2 * math.pi * i / n + rot
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


def s_ellipse(d, cx, cy, rx, ry, fill=None, color=INK, width=3, passes=2):
    pts = loop(cx, cy, rx, ry)
    if fill:
        d.polygon(jitter(pts, 2.0)[:-1], fill=fill)
    sketch(d, pts, color, width, passes)


def s_poly(d, pts, fill=None, color=INK, width=3, closed=True):
    if fill:
        d.polygon(jitter(pts, 1.6), fill=fill)
    path = list(pts)
    if closed:
        path = path + [path[0]]
    sketch(d, path, color, width)


def wavy_line(d, x0, y0, x1, y1, amp=2.2, color=INK, width=3, seg=8):
    pts = []
    for i in range(seg + 1):
        t = i / seg
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + math.sin(t * math.pi * 2) * amp
        pts.append((x, y))
    sketch(d, pts, color, width, amp=1.2)


def heart_pts(cx, cy, s):
    pts = []
    for i in range(40):
        t = 2 * math.pi * i / 40
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * s, cy - y * s))
    return pts


def star_pts(cx, cy, r, inner=0.42):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def canvas(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name)
    print("saved", name)


# ---------------- 猫咪 ----------------
def cat():
    img, d = canvas(260, 210)
    # 尾巴
    tail = [(196, 150), (215, 132), (226, 108), (222, 92)]
    sketch(d, tail, INK, 4)
    # 身体
    s_ellipse(d, 150, 140, 66, 40, fill=CREAM)
    # 头
    s_ellipse(d, 82, 112, 38, 34, fill=CREAM)
    # 耳朵
    s_poly(d, [(56, 92), (58, 62), (78, 82)], fill=CREAM)
    s_poly(d, [(96, 82), (110, 60), (116, 90)], fill=CREAM)
    # 耳朵内粉色
    d.polygon([(62, 88), (64, 70), (74, 84)], fill=PINK)
    d.polygon([(101, 84), (109, 70), (112, 88)], fill=PINK)
    # 闭眼
    sketch(d, [(64, 112), (70, 116), (76, 112)], INK, 3)
    sketch(d, [(92, 112), (98, 116), (104, 112)], INK, 3)
    # 鼻子和嘴
    d.polygon([(82, 122), (88, 122), (85, 127)], fill=PINK[:3] + (230,))
    sketch(d, [(85, 127), (85, 131)], INK, 2)
    sketch(d, [(78, 133), (85, 131), (92, 133)], INK, 2)
    # 胡须
    for dy in (-4, 2):
        sketch(d, [(46, 120 + dy), (30, 118 + dy)], INK_SOFT, 2, 1)
        sketch(d, [(114, 118 + dy), (130, 116 + dy)], INK_SOFT, 2, 1)
    # 腮红
    d.ellipse([52, 122, 70, 132], fill=PINK_SOFT)
    d.ellipse([100, 122, 118, 132], fill=PINK_SOFT)
    # 前爪
    s_ellipse(d, 118, 172, 16, 8, fill=CREAM)
    s_ellipse(d, 150, 174, 16, 8, fill=CREAM)
    save(img, "cat.png")


# ---------------- 咖啡杯 ----------------
def coffee():
    img, d = canvas(180, 200)
    # 杯身
    s_poly(d, [(48, 92), (122, 92), (113, 168), (57, 168)], fill=CREAM)
    # 杯口
    s_ellipse(d, 85, 92, 37, 10, fill=(250, 240, 222, 255))
    # 咖啡液面
    s_ellipse(d, 85, 92, 29, 6, fill=(176, 138, 108, 220), width=2)
    # 把手
    s_ellipse(d, 126, 122, 18, 22, color=INK, width=3)
    # 热气
    for x in (66, 85, 104):
        pts = []
        for i in range(9):
            t = i / 8
            pts.append((x + math.sin(t * math.pi * 2 + x) * 5, 74 - t * 44))
        sketch(d, pts, INK_SOFT, 2, 1, 1.0)
    # 杯垫
    s_ellipse(d, 86, 176, 46, 9, fill=(247, 231, 205, 200), width=2)
    save(img, "coffee.png")


# ---------------- 星星 ----------------
def stars():
    img, d = canvas(220, 130)
    s_poly(d, star_pts(60, 55, 26), fill=YELLOW)
    s_poly(d, star_pts(128, 36, 17), fill=YELLOW)
    s_poly(d, star_pts(178, 82, 14), fill=YELLOW)
    d.ellipse([32, 92, 40, 100], fill=INK_SOFT)
    d.ellipse([151, 18, 157, 24], fill=INK_SOFT)
    save(img, "stars.png")


# ---------------- 小花 ----------------
def flower():
    img, d = canvas(150, 190)
    # 花茎
    pts = [(76, 180), (80, 150), (74, 120), (78, 96)]
    sketch(d, pts, INK, 3)
    # 叶子
    s_ellipse(d, 92, 150, 12, 6, fill=MINT, width=2)
    s_ellipse(d, 62, 132, 11, 6, fill=MINT, width=2)
    # 花瓣
    cx, cy = 78, 78
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        px = cx + 22 * math.cos(ang)
        py = cy + 22 * math.sin(ang)
        s_ellipse(d, px, py, 15, 12, fill=PINK, width=2)
    # 花心
    s_ellipse(d, cx, cy, 12, 12, fill=YELLOW, width=2)
    save(img, "flower.png")


# ---------------- 太阳 ----------------
def sun():
    img, d = canvas(180, 180)
    s_ellipse(d, 90, 90, 40, 40, fill=YELLOW)
    for i in range(8):
        ang = i * math.pi / 4
        x0, y0 = 90 + 52 * math.cos(ang), 90 + 52 * math.sin(ang)
        x1, y1 = 90 + 70 * math.cos(ang), 90 + 70 * math.sin(ang)
        sketch(d, [(x0, y0), (x1, y1)], INK, 3, 1)
    save(img, "sun.png")


# ---------------- 云朵 ----------------
def cloud():
    img, d = canvas(220, 130)
    s_ellipse(d, 78, 84, 32, 24, fill=BLUE, width=2)
    s_ellipse(d, 120, 70, 38, 30, fill=BLUE, width=2)
    s_ellipse(d, 160, 86, 28, 22, fill=BLUE, width=2)
    save(img, "cloud.png")


# ---------------- 胶带 ----------------
def tape(name, color):
    img, d = canvas(240, 64)
    # 撕边（两端锯齿）
    pts = [(12, 16), (20, 12)] + [(22 + i * 24, 14) for i in range(9)] + [(228, 14), (236, 20)]
    zig = []
    for i in range(11):
        x = 34 + i * 18
        zig.append((x, 50 if i % 2 == 0 else 46))
    opts = [(236, 44), (228, 50)] + list(reversed(zig)) + [(12, 50)]
    poly = pts + zig + opts
    d.polygon(poly, fill=color)
    # 纹理线
    for i in range(6):
        y = 20 + i * 5
        sketch(d, [(30, y), (210, y)], (255, 255, 255, 45), 1, 1, 1.2)
    save(img, name)


# ---------------- 下划线 ----------------
def underline():
    img, d = canvas(240, 34)
    wavy_line(d, 12, 16, 228, 14, amp=2.6, color=(122, 114, 180, 220), width=3, seg=14)
    wavy_line(d, 24, 24, 214, 22, amp=2.0, color=(122, 114, 180, 130), width=2, seg=12)
    save(img, "underline.png")


# ---------------- 便签纸 ----------------
def sticky():
    img, d = canvas(180, 180)
    s_poly(d, [(28, 26), (150, 22), (154, 142), (32, 146)], fill=CREAM)
    # 折角
    s_poly(d, [(122, 142), (154, 142), (152, 110)], fill=(246, 234, 210, 230))
    # 手写线条
    for i, y in enumerate((56, 78, 100)):
        sketch(d, [(46, y), (128 - i * 12, y - 2)], (150, 146, 168, 150), 2, 1, 1.2)
    # 顶部胶带
    img2, d2 = canvas(92, 24)
    d2.polygon([(4, 6), (86, 4), (88, 18), (6, 20)], fill=(198, 191, 241, 190))
    img.alpha_composite(img2, (46, 14))
    save(img, "sticky.png")


# ---------------- 爱心 ----------------
def heart():
    img, d = canvas(110, 100)
    s_poly(d, heart_pts(55, 52, 2.2), fill=PINK)
    save(img, "heart.png")


if __name__ == "__main__":
    cat()
    coffee()
    stars()
    flower()
    sun()
    cloud()
    tape("tape_lilac.png", (198, 191, 241, 190))
    tape("tape_mint.png", (191, 231, 214, 190))
    underline()
    sticky()
    heart()
