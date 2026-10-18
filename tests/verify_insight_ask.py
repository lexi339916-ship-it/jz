# -*- coding: utf-8 -*-
"""测试新增的 /api/ai/insight 与 /api/ai/ask 接口。"""
import json

import httpx

BASE = "http://127.0.0.1:8000"

QUESTIONS = [
    "这个月餐饮花了多少？",
    "本月收支情况怎么样？",
    "上月最大的支出是什么？",
    "帮我预测下个月的支出",  # 超出工具范围，应返回提示
]


def main():
    c = httpx.Client(base_url=BASE, timeout=120, trust_env=False)
    token = c.post("/api/auth/login", json={
        "username": "demo", "password": "demo123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    print("===== insight =====")
    r = c.get("/api/ai/insight", headers=H)
    print(r.status_code, json.dumps(r.json(), ensure_ascii=False, indent=2))
    r2 = c.get("/api/ai/insight", headers=H)
    print("second call cached:", r2.json().get("cached"))

    print("\n===== ask =====")
    for q in QUESTIONS:
        r = c.post("/api/ai/ask", headers=H, json={"question": q})
        j = r.json()
        print(f"\nQ: {q}\nstatus: {r.status_code}")
        print("answer:", j.get("answer"))
        print("tool:", j.get("tool"), "| params:", j.get("tool_params"))
        print("data:", json.dumps(j.get("data_used"), ensure_ascii=False))
        print("steps:", j.get("steps"))


if __name__ == "__main__":
    main()
