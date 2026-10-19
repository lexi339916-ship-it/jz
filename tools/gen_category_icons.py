# -*- coding: utf-8 -*-
"""生成手绘风分类图标（15 个）与功能图标（5 个）。

96x96 透明底；抖动描边 + 低饱和填色，与手账涂鸦风格统一。
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "frontend" / "static" / "icons"
random.seed(1024)

INK = (84, 86, 112, 235)
INK_SOFT = (84, 86, 112, 150)
CREAM = (255, 250, 240, 255)
# 分类主题色（低饱和）
ORANGE = (247, 190, 130, 255)
BLUE = (160, 190, 240, 255)
PINK = (243, 180, 190, 255)
PURPLE = (190, 178, 235, 255)
TEAL = (160, 215, 205, 255)
YELLOW = (247, 216, 150, 255)
GREEN = (165, 215, 185, 255)
GREY = (200, 203, 218, 255)
RED = (238, 160, 160, 255)


def jitter(pts, amp=1.1):
    return [(x + random.uniform(-amp, amp), y + random.uniform(-amp, amp)) for x, y in pts]


def sketch(d, pts, color=INK, width=3, passes=2, closed=False, amp=1.1):
    path = list(pts) + ([pts[0]] if closed else [])
    for i in range(passes):
        d.line(jitter(path, amp), fill=color, width=max(1, width - (i % 2)), joint="curve")


def s_poly(d, pts, fill=None, color=INK, width=3):
    if fill:
        d.polygon(jitter(pts, 1.2), fill=fill)
    sketch(d, pts, color, width, closed=True)


def s_ellipse(d, cx, cy, rx, ry, fill=None, color=INK, width=3):
    pts = [(cx + rx * math.cos(2 * math.pi * i / 60),
            cy + ry * math.sin(2 * math.pi * i / 60)) for i in range(61)]
    if fill:
        d.polygon(pts[:-1], fill=fill)
    sketch(d, pts, color, width, 2, False, 1.0)


def s_rect(d, x0, y0, x1, y1, fill=None, r=0, color=INK, width=3):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    s_poly(d, pts, fill, color, width)


def canvas():
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, name):
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name)
    print("saved", name)


# ---------------- 分类图标 ----------------
def food():
    img, d = canvas()
    # 碗
    s_poly(d, [(18, 52), (78, 52), (70, 80), (26, 80)], fill=ORANGE)
    # 碗口
    s_ellipse(d, 48, 52, 30, 7, fill=CREAM, width=2)
    # 面条
    for x in (38, 48, 58):
        sketch(d, [(x, 40), (x + 2, 30), (x - 1, 22)], INK_SOFT, 2, 1)
    # 筷子
    sketch(d, [(62, 16), (74, 42)], INK, 3)
    sketch(d, [(68, 14), (80, 40)], INK, 3)
    save(img, "cat_food.png")


def transport():
    img, d = canvas()
    s_poly(d, [(18, 48), (26, 34), (66, 34), (76, 48), (76, 64), (18, 64)],
           fill=BLUE)
    s_poly(d, [(30, 36), (64, 36), (68, 46), (26, 46)], fill=CREAM, width=2)
    s_ellipse(d, 32, 68, 8, 8, fill=GREY)
    s_ellipse(d, 64, 68, 8, 8, fill=GREY)
    s_ellipse(d, 32, 68, 3, 3, fill=CREAM, width=2)
    s_ellipse(d, 64, 68, 3, 3, fill=CREAM, width=2)
    save(img, "cat_transport.png")


def shopping():
    img, d = canvas()
    s_poly(d, [(24, 36), (72, 36), (78, 82), (18, 82)], fill=PINK)
    # 提手
    pts = [(34 + 14 * math.cos(math.pi * i / 20), 36 - 16 * math.sin(math.pi * i / 20))
           for i in range(21)]
    sketch(d, pts, INK, 3)
    d.ellipse([40, 50, 44, 54], fill=INK)
    d.ellipse([52, 50, 56, 54], fill=INK)
    save(img, "cat_shopping.png")


def house():
    img, d = canvas()
    s_poly(d, [(48, 14), (82, 44), (14, 44)], fill=PURPLE)
    s_poly(d, [(22, 44), (74, 44), (74, 82), (22, 82)], fill=CREAM)
    s_poly(d, [(42, 62), (54, 62), (54, 82), (42, 82)], fill=PURPLE, width=2)
    save(img, "cat_home.png")


def study():
    img, d = canvas()
    s_poly(d, [(14, 28), (48, 24), (48, 76), (14, 80)], fill=TEAL)
    s_poly(d, [(48, 24), (82, 28), (82, 80), (48, 76)], fill=CREAM)
    sketch(d, [(48, 24), (48, 76)], INK, 3)
    for y in (38, 50, 62):
        sketch(d, [(22, y), (40, y - 1)], INK_SOFT, 2, 1)
        sketch(d, [(56, y), (74, y + 1)], INK_SOFT, 2, 1)
    save(img, "cat_study.png")


def fun():
    img, d = canvas()
    s_rect(d, 14, 36, 82, 68, fill=PINK, r=14)
    # 方向键
    sketch(d, [(32, 46), (32, 58)], INK, 3)
    sketch(d, [(26, 52), (38, 52)], INK, 3)
    s_ellipse(d, 62, 48, 4, 4, fill=CREAM, width=2)
    s_ellipse(d, 70, 56, 4, 4, fill=CREAM, width=2)
    save(img, "cat_fun.png")


def medical():
    img, d = canvas()
    s_rect(d, 16, 16, 80, 80, fill=CREAM, r=10)
    s_rect(d, 42, 30, 54, 66, fill=RED, width=2)
    s_rect(d, 30, 42, 66, 54, fill=RED, width=2)
    save(img, "cat_medical.png")


def comm():
    img, d = canvas()
    s_rect(d, 30, 12, 66, 84, fill=BLUE, r=10)
    sketch(d, [(42, 22), (54, 22)], INK, 2)
    s_ellipse(d, 48, 74, 4, 4, fill=CREAM, width=2)
    save(img, "cat_comm.png")


def other():
    img, d = canvas()
    s_poly(d, [(20, 34), (76, 34), (72, 82), (24, 82)], fill=GREY)
    sketch(d, [(16, 26), (80, 26), (76, 36), (20, 36)], INK, 3, 1)
    sketch(d, [(48, 36), (48, 82)], INK_SOFT, 2, 1)
    save(img, "cat_other.png")


def salary():
    img, d = canvas()
    s_rect(d, 12, 30, 84, 70, fill=GREEN, r=6)
    sketch(d, [(12, 34), (48, 54), (84, 34)], INK, 3)
    s_ellipse(d, 48, 56, 9, 9, fill=YELLOW, width=2)
    save(img, "cat_salary.png")


def parttime():
    img, d = canvas()
    s_rect(d, 16, 38, 80, 78, fill=YELLOW, r=8)
    pts = [(36 + 12 * math.cos(math.pi * i / 20), 38 - 12 * math.sin(math.pi * i / 20))
           for i in range(21)]
    sketch(d, pts, INK, 3)
    sketch(d, [(44, 38), (44, 50), (52, 50), (52, 38)], INK, 2, 1)
    save(img, "cat_parttime.png")


def finance():
    img, d = canvas()
    sketch(d, [(20, 20), (20, 78), (80, 78)], INK, 3)
    pts = [(28, 64), (40, 52), (50, 58), (66, 36), (74, 30)]
    sketch(d, pts, INK, 4)
    sketch(d, [(66, 36), (62, 32)], INK, 3)
    sketch(d, [(66, 36), (64, 42)], INK, 3)
    save(img, "cat_finance.png")


def redpacket():
    img, d = canvas()
    s_rect(d, 22, 16, 74, 80, fill=RED, r=6)
    pts = [(24, 20), (48, 36), (72, 20)]
    sketch(d, pts, INK, 2, 1)
    s_ellipse(d, 48, 52, 9, 9, fill=YELLOW, width=2)
    save(img, "cat_redpacket.png")


def refund():
    img, d = canvas()
    pts = [(48 + 28 * math.cos(math.radians(a)), 48 + 28 * math.sin(math.radians(a)))
           for a in range(40, 320, 8)]
    sketch(d, pts, INK, 4)
    sketch(d, [(48 + 28 * math.cos(math.radians(40)), 48 + 28 * math.sin(math.radians(40))),
               (38, 22), (44, 34)], INK, 3)
    save(img, "cat_refund.png")


def other_income():
    img, d = canvas()
    s_ellipse(d, 38, 60, 18, 14, fill=YELLOW)
    s_ellipse(d, 60, 42, 16, 12, fill=YELLOW, width=2)
    # 小闪光
    sketch(d, [(72, 20), (76, 30), (86, 34), (76, 38), (72, 48), (68, 38),
               (58, 34), (68, 30)], INK_SOFT, 2, 1)
    save(img, "cat_otherincome.png")


def default_icon():
    img, d = canvas()
    s_poly(d, [(22, 18), (52, 18), (78, 44), (48, 78), (18, 48)], fill=GREY)
    s_ellipse(d, 34, 32, 4, 4, fill=CREAM, width=2)
    save(img, "cat_default.png")


# ---------------- 功能图标 ----------------
def pencil():
    img, d = canvas()
    s_poly(d, [(22, 74), (30, 56), (66, 20), (78, 32), (42, 68)], fill=YELLOW)
    s_poly(d, [(22, 74), (26, 62), (34, 70)], fill=CREAM, width=2)
    sketch(d, [(30, 56), (42, 68)], INK, 2, 1)
    save(img, "act_pencil.png")


def sparkle():
    img, d = canvas()
    star = [(48, 12), (56, 40), (84, 48), (56, 56), (48, 84),
            (40, 56), (12, 48), (40, 40)]
    s_poly(d, star, fill=YELLOW)
    d.ellipse([70, 18, 76, 24], fill=INK_SOFT)
    d.ellipse([18, 66, 24, 72], fill=INK_SOFT)
    save(img, "act_sparkle.png")


def note_icon():
    img, d = canvas()
    s_poly(d, [(20, 16), (72, 14), (78, 66), (26, 72)], fill=CREAM)
    s_poly(d, [(56, 70), (78, 66), (74, 44)], fill=PINK, width=2)
    for y in (30, 42, 54):
        sketch(d, [(30, y), (58, y - 1)], INK_SOFT, 2, 1)
    save(img, "act_note.png")


def chart():
    img, d = canvas()
    sketch(d, [(18, 16), (18, 80), (82, 80)], INK, 3)
    s_rect(d, 28, 56, 40, 78, fill=BLUE, width=2)
    s_rect(d, 46, 42, 58, 78, fill=TEAL, width=2)
    s_rect(d, 64, 28, 76, 78, fill=PURPLE, width=2)
    save(img, "act_chart.png")


def camera():
    img, d = canvas()
    s_rect(d, 12, 30, 84, 76, fill=CREAM, r=8)
    s_poly(d, [(30, 30), (36, 20), (58, 20), (64, 30)], fill=CREAM)
    s_ellipse(d, 48, 54, 16, 16, fill=BLUE)
    s_ellipse(d, 48, 54, 7, 7, fill=CREAM, width=2)
    d.ellipse([70, 38, 76, 44], fill=INK_SOFT)
    save(img, "act_camera.png")


def lock():
    img, d = canvas()
    pts = [(30 + 18 * math.cos(math.pi * i / 20), 44 - 22 * math.sin(math.pi * i / 20))
           for i in range(21)]
    sketch(d, pts, INK, 4)
    s_rect(d, 18, 44, 78, 84, fill=YELLOW, r=8)
    s_ellipse(d, 48, 60, 6, 6, fill=CREAM, width=2)
    sketch(d, [(48, 66), (48, 74)], INK, 3)
    save(img, "act_lock.png")


def wallet():
    img, d = canvas()
    s_rect(d, 12, 30, 84, 74, fill=PURPLE, r=8)
    s_rect(d, 58, 42, 84, 62, fill=CREAM, r=6, width=2)
    d.ellipse([68, 48, 74, 54], fill=INK_SOFT)
    save(img, "act_wallet.png")


def target():
    img, d = canvas()
    s_ellipse(d, 48, 48, 32, 32, fill=CREAM)
    s_ellipse(d, 48, 48, 22, 22, fill=PINK, width=2)
    s_ellipse(d, 48, 48, 11, 11, fill=RED, width=2)
    s_ellipse(d, 48, 48, 3, 3, fill=INK, width=1)
    save(img, "act_target.png")


def info():
    img, d = canvas()
    s_ellipse(d, 48, 48, 32, 32, fill=BLUE)
    s_ellipse(d, 48, 30, 4, 4, fill=CREAM, width=2)
    sketch(d, [(48, 42), (48, 64)], CREAM, 4)
    save(img, "act_info.png")


if __name__ == "__main__":
    food(); transport(); shopping(); house(); study(); fun(); medical()
    comm(); other(); salary(); parttime(); finance(); redpacket(); refund()
    other_income(); default_icon()
    pencil(); sparkle(); note_icon(); chart(); camera()
    lock(); wallet(); target(); info()
