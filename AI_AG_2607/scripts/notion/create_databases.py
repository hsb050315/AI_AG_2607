"""연동된 노션 페이지에 데이터베이스(표) 5개를 생성한다.

각 DB 는 title 속성만 가진 최소 구성. 토큰 값은 출력하지 않는다.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
PARENT_PAGE_ID = "3c924c48-3f29-80aa-aab1-cdfdf4c156a4"
DB_TITLES = ["개인 일정", "업무", "학습", "완료작업", "프로젝트"]


def load_env():
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def call(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "https://api.notion.com/v1" + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + os.environ["NOTION_API_KEY"],
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
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

    for title in DB_TITLES:
        payload = {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": {"이름": {"title": {}}},
        }
        status, body = call("/databases", method="POST", payload=payload)
        if status == 200:
            print(f"OK  '{title}'  -> {body.get('url')}")
        else:
            print(f"ERR '{title}'  {status}  {body.get('code')} - {body.get('message')}")


if __name__ == "__main__":
    main()
