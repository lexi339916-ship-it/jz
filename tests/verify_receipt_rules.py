# -*- coding: utf-8 -*-
"""测试收据识别的两条关键业务规则：
1. 截图未显示扣款账户 → 标记待确认（不猜测）；
2. 金额与近期账单相同 → 疑似重复告警。
"""
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent / "fixtures"
OUT.mkdir(exist_ok=True)
IMG_PATH = OUT / "mock_alipay_nofund.png"


def _font(size):
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_mock():
    img = Image.new("RGB", (750, 1200), "#ffffff")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 750, 96], fill="#1677ff")
    d.text((300, 30), "支付宝", font=_font(36), fill="#ffffff")
    d.text((312, 200), "支付成功", font=_font(44), fill="#111111")
    d.text((300, 300), "¥32.00", font=_font(80), fill="#111111")
    d.text((300, 440), "街角咖啡", font=_font(34), fill="#555555")
    d.text((48, 640), "付款时间", font=_font(30), fill="#888888")
    d.text((280, 640), "2026-10-19 09:12:45", font=_font(30), fill="#222222")
    d.text((48, 720), "商品说明", font=_font(30), fill="#888888")
    d.text((280, 720), "拿铁咖啡", font=_font(30), fill="#222222")
    # 故意不显示任何支付渠道/扣款账户
    img.save(IMG_PATH)
    print("saved:", IMG_PATH)


def test_upload():
    c = httpx.Client(base_url=BASE, timeout=180, trust_env=False)
    token = c.post("/api/auth/login", json={
        "username": "demo", "password": "demo123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}
    with open(IMG_PATH, "rb") as f:
        r = c.post("/api/ai/parse-receipt", headers=H,
                   files={"file": ("mock.png", f, "image/png")})
    import json
    print("status:", r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    make_mock()
    test_upload()
