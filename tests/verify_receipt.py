# -*- coding: utf-8 -*-
"""生成模拟微信支付截图并测试 /api/ai/parse-receipt 全链路。"""
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent / "fixtures"
OUT.mkdir(exist_ok=True)
IMG_PATH = OUT / "mock_payment.png"


def _font(size):
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_mock():
    img = Image.new("RGB", (750, 1200), "#f6f6f6")
    d = ImageDraw.Draw(img)
    # 顶部栏
    d.rectangle([0, 0, 750, 96], fill="#ededed")
    d.text((40, 32), "‹", font=_font(44), fill="#333333")
    d.text((300, 32), "微信支付", font=_font(34), fill="#111111")
    # 成功图标
    d.ellipse([315, 180, 435, 300], fill="#07c160")
    d.line([345, 242, 372, 268], fill="white", width=10)
    d.line([372, 268, 410, 218], fill="white", width=10)
    # 文案与金额
    d.text((318, 340), "支付成功", font=_font(40), fill="#111111")
    d.text((292, 430), "¥32.50", font=_font(76), fill="#111111")
    # 商户
    d.text((312, 560), "老王面馆", font=_font(32), fill="#555555")
    # 信息区
    d.rectangle([0, 700, 750, 960], fill="#ffffff")
    rows = [("支付方式", "零钱"), ("支付时间", "2026-10-19 12:31:05"),
            ("交易单号", "4200002233202610191234567890")]
    y = 740
    for k, v in rows:
        d.text((48, y), k, font=_font(30), fill="#888888")
        d.text((260, y), v, font=_font(30), fill="#222222")
        y += 80
    # 底部按钮
    d.rounded_rectangle([60, 1040, 690, 1130], radius=45, fill="#07c160")
    d.text((330, 1065), "完成", font=_font(32), fill="#ffffff")
    img.save(IMG_PATH)
    print("mock screenshot saved:", IMG_PATH)


def test_upload():
    c = httpx.Client(base_url=BASE, timeout=180, trust_env=False)
    token = c.post("/api/auth/login", json={
        "username": "demo", "password": "demo123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}
    with open(IMG_PATH, "rb") as f:
        r = c.post("/api/ai/parse-receipt", headers=H,
                   files={"file": ("mock_payment.png", f, "image/png")})
    print("status:", r.status_code)
    import json
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    make_mock()
    test_upload()
