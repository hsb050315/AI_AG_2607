"""Notion API 연동 확인 스크립트.

.env 의 NOTION_API_KEY 로 읽기 전용 API 를 호출해 연동 상태만 출력한다.
토큰 값은 절대 출력하지 않는다.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
PAGE_ID = "3c924c48-3f29-80aa-aab1-cdfdf4c156a4"


def load_env():
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def call(path):
    req = urllib.request.Request(
        "https://api.notion.com/v1" + path,
        headers={
            "Authorization": "Bearer " + os.environ["NOTION_API_KEY"],
            "Notion-Version": "2022-06-28",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    load_env()
    if not os.environ.get("NOTION_API_KEY"):
        print("NOTION_API_KEY 가 .env 에 없습니다.")
        sys.exit(1)

    s1, b1 = call("/users/me")
    print(f"[1] GET /users/me -> {s1}")
    if s1 == 200:
        bot = b1.get("bot", {})
        print(f"    통합 이름: {b1.get('name')}  타입: {b1.get('type')}")
        ws = bot.get("workspace_name")
        if ws:
            print(f"    워크스페이스: {ws}")
    else:
        print(f"    오류: {b1.get('code')} - {b1.get('message')}")

    s2, b2 = call(f"/pages/{PAGE_ID}")
    print(f"[2] GET /pages/{PAGE_ID} -> {s2}")
    if s2 == 200:
        title = ""
        for prop in b2.get("properties", {}).values():
            if prop.get("type") == "title":
                title = "".join(t["plain_text"] for t in prop["title"])
        print(f"    페이지 제목: {title or '(제목 없음)'}")
        print("    => 통합이 이 페이지에 연결되어 있습니다. 연동 정상.")
    else:
        print(f"    오류: {b2.get('code')} - {b2.get('message')}")
        if s2 in (403, 404):
            print("    => 토큰은 유효하나 이 페이지에 통합이 공유되지 않았습니다.")
            print('       페이지 우상단 ••• → "연결" → "AI_AG_2607" 추가 필요.')


if __name__ == "__main__":
    main()
