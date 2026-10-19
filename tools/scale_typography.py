# -*- coding: utf-8 -*-
"""移动端可读性调整：整体放大字号与常用图标尺寸。

单次扫描替换，避免链式替换（例如 22→25 后又被 25→27 二次放大）。
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1] / "frontend"

# 字号映射（rpx）：整体约 +2~4rpx，小字号增幅更大
FONT_MAP = {
    16: 20, 17: 19, 19: 22, 20: 23, 21: 24, 22: 25, 23: 26, 24: 26,
    25: 27, 26: 28, 27: 29, 28: 30, 29: 31, 30: 32, 31: 33, 32: 34,
    34: 36, 36: 38, 38: 40, 40: 42, 44: 46, 46: 48, 60: 62, 64: 68,
    74: 76,
}
FONT_RE = re.compile(r"font-size:\s*(\d+)rpx")


def font_repl(m: re.Match) -> str:
    v = int(m.group(1))
    return f"font-size: {FONT_MAP.get(v, v)}rpx"


# 图标尺寸（成对出现的 width/height）
PAIR_MAP = {
    "width: 54rpx; height: 54rpx;": "width: 60rpx; height: 60rpx;",
    "width: 56rpx; height: 56rpx;": "width: 62rpx; height: 62rpx;",
    "width: 58rpx; height: 58rpx;": "width: 64rpx; height: 64rpx;",
    "width: 52rpx; height: 52rpx;": "width: 56rpx; height: 56rpx;",
    "width: 44rpx; height: 44rpx;": "width: 48rpx; height: 48rpx;",
    "width: 40rpx; height: 40rpx;": "width: 44rpx; height: 44rpx;",
    "width: 30rpx; height: 30rpx;": "width: 34rpx; height: 34rpx;",
    # 日历格高度（容纳更大的标签）
    "min-height: 118rpx": "min-height: 136rpx",
    "min-height: 114rpx": "min-height: 130rpx",
}

targets = list((ROOT / "pages").rglob("*.vue")) + [ROOT / "App.vue"]
changed = []
for path in targets:
    text = path.read_text(encoding="utf-8")
    new = FONT_RE.sub(font_repl, text)
    for old, rep in PAIR_MAP.items():
        new = new.replace(old, rep)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed.append(path.relative_to(ROOT))
print("updated:", len(changed), "files")
for p in changed:
    print(" -", p)
