# -*- coding: utf-8 -*-
"""快速验证 AI 配置：登录 demo 账号并调用一次 parse-bill。"""
import json
import sys

import httpx

BASE = "http://127.0.0.1:8000"


def main():
    c = httpx.Client(base_url=BASE, timeout=90, trust_env=False)
    print("health:", c.get("/api/health").json())
    r = c.post("/api/auth/login", json={"username": "demo", "password": "demo123"})
    if r.status_code != 200:
        sys.exit(f"登录失败：{r.status_code} {r.text}")
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}
    print("login: OK (demo)")

    r = c.post("/api/ai/parse-bill", headers=H,
               json={"text": "午饭花了32元，打车回家12块"})
    print("parse-bill status:", r.status_code)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
