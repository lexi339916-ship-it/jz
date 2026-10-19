# -*- coding: utf-8 -*-
"""验证储蓄目标、生活挑战与 AI 财务分析助手（真实模型）。"""
import json

import httpx

BASE = "http://127.0.0.1:8000"

QUESTIONS = [
    "这个月钱主要花在哪里了？",
    "和上个月相比，我的餐饮支出增加了多少？",
    "帮我制定下个月的预算。",
    "如果我每天少花15元，一个月能省多少钱？",
]


def main():
    c = httpx.Client(base_url=BASE, timeout=120, trust_env=False)
    token = c.post("/api/auth/login", json={
        "username": "demo", "password": "demo123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    print("===== 储蓄目标 =====")
    r = c.post("/api/goals", headers=H, json={"name": "攒够5000元旅行基金", "target_amount": "5000"})
    print("create:", r.status_code, json.dumps(r.json(), ensure_ascii=False))
    goal_id = r.json()["id"]
    r = c.post(f"/api/goals/{goal_id}/deposit", headers=H, json={"amount": "800"})
    print("deposit 800:", r.status_code, json.dumps(r.json(), ensure_ascii=False))

    print("\n===== 生活挑战 =====")
    r = c.post("/api/challenges", headers=H, json={
        "name": "本周减少外卖支出", "category": "餐饮",
        "period_days": 7, "target_amount": "40"})
    print("create:", r.status_code, json.dumps(r.json(), ensure_ascii=False))
    r = c.get("/api/challenges", headers=H)
    print("list:", r.status_code, json.dumps(r.json(), ensure_ascii=False))

    print("\n===== 周总结 =====")
    r = c.get("/api/ai/summary", headers=H, params={"period": "week"})
    j = r.json()
    print("status:", r.status_code, "| label:", j.get("month"),
          "| 支出:", j.get("expense"), "| 收入:", j.get("income"))
    print("summary:", j.get("summary"))

    print("\n===== AI 财务分析助手（4 个新问题） =====")
    for q in QUESTIONS:
        r = c.post("/api/ai/ask", headers=H, json={"question": q})
        j = r.json()
        print(f"\nQ: {q}\nstatus: {r.status_code}")
        print("answer:", j.get("answer"))
        print("tool:", j.get("tool"), "| data:", json.dumps(j.get("data_used"), ensure_ascii=False))


if __name__ == "__main__":
    main()
