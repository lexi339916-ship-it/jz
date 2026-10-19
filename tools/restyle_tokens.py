# -*- coding: utf-8 -*-
"""全站 UI 设计令牌替换：手账风配色 / 更圆润的圆角 / 柔和紫色阴影。

单次扫描替换，避免链式替换互相影响。
"""
import pathlib
import re

FRONTEND = pathlib.Path(__file__).resolve().parents[1] / "frontend"

# 旧值 -> 新值（颜色 + 圆角 + 阴影）
MAP = {
    # 主色：清新蓝紫
    "#2f6fed": "#6C7BF5",
    "#63a7ff": "#9DA9FF",
    "#6fb0ff": "#A8B2FF",
    "#2b5fd9": "#6C7BF5",
    "#4a86f7": "#8B97FF",
    # 浅色底
    "#eef3ff": "#EFF1FF",
    "#e8f8f2": "#E9F8F2",
    "#f5f7fb": "#F6F4FB",
    "#f8faff": "#FBFAFF",
    "#e3ebfd": "#E4E7FB",
    "#f0f3f9": "#F1EFF9",
    "#f0f2f6": "#F2F0F8",
    "#edf0f5": "#EFEDF7",
    "#fafbfe": "#FBFAFE",
    "#e8edf5": "#E9E6F4",
    "#f4f6fa": "#F4F2FA",
    "#f2f4f8": "#F4F2FA",
    "#f5f3ff": "#F4F0FF",
    "#f3f0ff": "#F4F0FF",
    # 文字
    "#263246": "#3A3F58",
    "#33415c": "#4A4F6B",
    "#4a5568": "#5A5F78",
    "#5b6473": "#6B7089",
    "#7c8595": "#8A90A8",
    "#9aa3b5": "#A6AAC2",
    "#b6bdcc": "#C3C7DA",
    "#c4ccda": "#D3D7E7",
    "#cbd2e0": "#D6D9E8",
    "#d3d8e2": "#DCE0EC",
    # 强调色（柔和化）
    "#16b07a": "#45C39A",
    "#0f9d6e": "#33B98E",
    "#e5484d": "#F27E7E",
    "#c53030": "#D96363",
    "#f59f0b": "#F2B45C",
    "#d97706": "#D98A32",
    "#b45309": "#C1823F",
    "#fdf6ec": "#FFF6E7",
    "#fdecec": "#FFEDEE",
    "#d64550": "#E86A72",
    "#b8ffdf": "#CFF7E9",
    "#ffd9d9": "#FFDCE1",
    # 阴影（蓝灰 → 紫）
    "rgba(40, 70, 120, .06)": "rgba(124, 139, 255, .10)",
    "rgba(40, 70, 120, 0.06)": "rgba(124, 139, 255, .10)",
    "rgba(47, 111, 237, .4)": "rgba(124, 139, 255, .35)",
    "rgba(47, 111, 237, .35)": "rgba(124, 139, 255, .30)",
    # 圆角（更圆润）
    "border-radius: 14rpx": "border-radius: 18rpx",
    "border-radius: 16rpx": "border-radius: 20rpx",
    "border-radius: 18rpx": "border-radius: 22rpx",
    "border-radius: 20rpx": "border-radius: 24rpx",
    "border-radius: 22rpx": "border-radius: 26rpx",
    "border-radius: 24rpx": "border-radius: 28rpx",
    "border-radius: 26rpx": "border-radius: 30rpx",
    "border-radius: 28rpx": "border-radius: 32rpx",
    "border-radius: 30rpx": "border-radius: 34rpx",
    "border-radius: 32rpx": "border-radius: 36rpx",
}

KEYS = sorted(MAP.keys(), key=len, reverse=True)
PATTERN = re.compile("|".join(re.escape(k) for k in KEYS))
LOWER_MAP = {k.lower(): v for k, v in MAP.items()}


def repl(match: re.Match) -> str:
    token = match.group(0)
    return LOWER_MAP.get(token.lower(), token)


def main():
    changed = []
    for path in FRONTEND.rglob("*.vue"):
        text = path.read_text(encoding="utf-8")
        new = PATTERN.sub(repl, text)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(path)
    # pages.json 的 tabBar / 导航颜色
    pages_json = FRONTEND / "pages.json"
    text = pages_json.read_text(encoding="utf-8")
    new = PATTERN.sub(repl, text)
    if new != text:
        pages_json.write_text(new, encoding="utf-8")
        changed.append(pages_json)
    for p in changed:
        print("updated:", p.relative_to(FRONTEND))


if __name__ == "__main__":
    main()
