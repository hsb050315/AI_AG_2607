"""업무 항목을 Notion "업무" DB에 등록하는 헬퍼.

핵심 함수:
  - load_env()        : 프로젝트 루트의 .env 에서 NOTION_API_KEY 를 읽어온다 (토큰 값은 출력하지 않는다)
  - get_schema()      : "업무" DB 의 속성 이름/타입을 반환한다
  - add_task(...)     : DB 에 새 행(페이지)을 하나 만든다
  - main()            : JSON 파일 경로를 인자로 받아 add_task 를 호출한다

Notion 저수준 요청 JSON 을 매번 직접 조립하지 말고 이 함수들을 사용한다.
한글 인자를 셸 명령줄로 넘기면 Windows 에서 깨질 수 있으므로, main() 은 JSON 파일에서 값을 읽는다.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")

# "업무" DB. .env 에 NOTION_WORK_DB_ID 가 있으면 그 값을 우선한다.
DEFAULT_DB_ID = "3ca24c48-3f29-81ac-bfef-d5842e3ead82"

# DB 속성 이름 (2026-08 기준 실제 스키마)
P_NAME = "이름"       # title    - 업무 제목
P_REGISTERED = "등록일"  # date  - 업무를 등록/시작한 날
P_DUE = "잔여기한"      # date   - 마감일
P_SUBMIT = "제출처"     # rich_text - 제출 대상(팀/담당자/채널)


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
    return os.environ.get("NOTION_WORK_DB_ID") or DEFAULT_DB_ID


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


def _date(v):
    v = v.strip()
    if "/" in v:
        start, end = v.split("/", 1)
        return {"date": {"start": start.strip(), "end": end.strip()}}
    return {"date": {"start": v}}


def add_task(name, registered=None, due=None, submit_to=None):
    """업무 DB 에 행 하나 추가.

    name       : 업무 제목 (필수)
    registered : 등록일. ISO 날짜 "2026-08-28" (기본값 없음 — 보통 오늘 날짜를 넘긴다)
    due        : 잔여기한(마감일). ISO 날짜 "2026-09-05" 또는 범위 "2026-09-01/2026-09-05"
    submit_to  : 제출처 (팀/담당자/채널). 없으면 생략.

    성공 시 생성된 페이지 dict 반환, 실패 시 SystemExit.
    """
    props = {P_NAME: {"title": [{"type": "text", "text": {"content": name}}]}}
    if registered:
        props[P_REGISTERED] = _date(registered)
    if due:
        props[P_DUE] = _date(due)
    if submit_to:
        props[P_SUBMIT] = _rt(submit_to)

    s, b = call("/pages", method="POST", payload={
        "parent": {"database_id": _db_id()},
        "properties": props,
    })
    if s != 200:
        raise SystemExit(f"등록 실패 {s}: {b.get('code')} - {b.get('message')}")
    return b


def main():
    load_env()
    if len(sys.argv) < 2:
        raise SystemExit("사용법: python notion_work_task.py <입력.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else [data]
    for item in items:
        page = add_task(
            name=item["name"],
            registered=item.get("registered"),
            due=item.get("due"),
            submit_to=item.get("submit_to"),
        )
        print(f"OK  {item['name']}  -> {page.get('url')}")


if __name__ == "__main__":
    main()
