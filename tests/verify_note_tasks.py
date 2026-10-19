# -*- coding: utf-8 -*-
"""验证便签/任务多任务提取（真实模型）。"""
import json

import httpx

BASE = "http://127.0.0.1:8000"
TEXTS = [
    "周五之前交课程设计报告，明天下午去超市买生活用品。",
    "重要：下周一上午把答辩PPT发给老师；顺便记一下，咖啡豆快用完了",
]


def main():
    c = httpx.Client(base_url=BASE, timeout=120, trust_env=False)
    token = c.post("/api/auth/login", json={
        "username": "demo", "password": "demo123"}).json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}
    for text in TEXTS:
        r = c.post("/api/ai/parse-note", headers=H, json={"text": text})
        print("=" * 30, "\n输入:", text)
        print("status:", r.status_code)
        j = r.json()
        for i, d in enumerate(j.get("drafts", []), 1):
            print(f"  {i}. {d['title']} | {d['note_type']} | {d['due_at']} | 优先级 {d['priority']} | 缺失 {d['missing_fields']}")
        if j.get("notice"):
            print("  notice:", j["notice"])
        print("  模型:", j.get("model"), "| 提示词:", j.get("prompt_version"))


if __name__ == "__main__":
    main()
