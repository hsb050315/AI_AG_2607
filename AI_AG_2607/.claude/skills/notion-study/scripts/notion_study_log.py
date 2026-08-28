"""학습 기록을 Notion "학습" DB에 저장하는 헬퍼.

핵심 함수:
  - load_env()        : 프로젝트 루트의 .env 에서 NOTION_API_KEY 를 읽어온다 (토큰 값은 출력하지 않는다)
  - get_schema()      : "학습" DB 의 속성 이름/타입을 반환한다
  - add_log(...)      : DB 에 새 행(페이지)을 하나 만든다
  - main()            : JSON 파일 경로를 인자로 받아 add_log 를 호출한다

Notion 저수준 요청 JSON 을 매번 직접 조립하지 말고 이 함수들을 사용한다.
한글 인자를 셸 명령줄로 넘기면 Windows 에서 깨질 수 있으므로, main() 은 JSON 파일에서 값을 읽는다.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")

# "학습" DB. .env 에 NOTION_STUDY_DB_ID 가 있으면 그 값을 우선한다.
DEFAULT_DB_ID = "3ca24c48-3f29-81af-9b52-d7b5ccde708a"

# DB 속성 이름 (2026-08 기준 실제 스키마)
P_NAME = "이름"          # title      - 학습 주제
P_REPORT = "보고서제목"   # rich_text  - 정리한 보고서/노트 제목
P_SOURCE = "출처"        # rich_text  - 학습 출처(문서, 책, URL, 강의 등)


def load_env():
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _db_id():
    return os.environ.get("NOTION_STUDY_DB_ID") or DEFAULT_DB_ID


def call(path, method="GET", payload=None):
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        raise SystemExit("NOTION_API_KEY 가 .env 에 없습니다.")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "https://api.notion.com/v1" + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + key,
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def get_schema():
    """{속성이름: 타입} 딕셔너리 반환. 스킬이 스키마 변경을 감지하는 용도."""
    s, b = call("/databases/" + _db_id())
    if s != 200:
        raise SystemExit(f"DB 조회 실패 {s}: {b.get('code')} - {b.get('message')}")
    return {name: p.get("type") for name, p in b.get("properties", {}).items()}


def _rt(v):
    return {"rich_text": [{"type": "text", "text": {"content": v}}]}


def add_log(name, report_title=None, source=None):
    """학습 DB 에 행 하나 추가.

    name         : 학습 주제 (필수)
    report_title : 정리한 보고서/노트 제목 (없으면 생략)
    source       : 학습 출처 — 문서명, 책, URL, 강의 등 (없으면 생략)

    성공 시 생성된 페이지 dict 반환, 실패 시 SystemExit.
    """
    props = {P_NAME: {"title": [{"type": "text", "text": {"content": name}}]}}
    if report_title:
        props[P_REPORT] = _rt(report_title)
    if source:
        props[P_SOURCE] = _rt(source)

    s, b = call("/pages", method="POST", payload={
        "parent": {"database_id": _db_id()},
        "properties": props,
    })
    if s != 200:
        raise SystemExit(f"저장 실패 {s}: {b.get('code')} - {b.get('message')}")
    return b


def main():
    load_env()
    if len(sys.argv) < 2:
        raise SystemExit("사용법: python notion_study_log.py <입력.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else [data]
    for item in items:
        page = add_log(
            name=item["name"],
            report_title=item.get("report_title"),
            source=item.get("source"),
        )
        print(f"OK  {item['name']}  -> {page.get('url')}")


if __name__ == "__main__":
    main()
