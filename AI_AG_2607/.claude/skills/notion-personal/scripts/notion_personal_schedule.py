"""개인 일정을 Notion "개인 일정" DB에 등록하는 헬퍼.

핵심 함수:
  - load_env()          : 프로젝트 루트의 .env 에서 NOTION_API_KEY 를 읽어온다 (토큰 값은 출력하지 않는다)
  - get_schema()        : "개인 일정" DB 의 속성 이름/타입을 반환한다
  - add_schedule(...)   : DB 에 새 행(페이지)을 하나 만든다
  - main()              : JSON 파일 경로를 인자로 받아 add_schedule 을 호출한다

Notion 저수준 요청 JSON 을 매번 직접 조립하지 말고 이 함수들을 사용한다.
한글 인자를 셸 명령줄로 넘기면 Windows 에서 깨질 수 있으므로, main() 은 JSON 파일에서 값을 읽는다.
"""
import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")

# "개인 일정" DB. .env 에 NOTION_PERSONAL_DB_ID 가 있으면 그 값을 우선한다.
DEFAULT_DB_ID = "3ca24c48-3f29-8144-bc14-cb974b431278"

# DB 속성 이름 (2026-08 기준 실제 스키마)
P_NAME = "이름"            # title
P_TIME = "시간"            # date
P_PLACE = "장소"           # rich_text
P_PEOPLE = "함께하는 사람"  # rich_text


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
    return os.environ.get("NOTION_PERSONAL_DB_ID") or DEFAULT_DB_ID


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
    """{속성이름: 타입} 딕셔너리를 반환. 스킬이 스키마 변경을 감지하는 용도."""
    s, b = call("/databases/" + _db_id())
    if s != 200:
        raise SystemExit(f"DB 조회 실패 {s}: {b.get('code')} - {b.get('message')}")
    return {name: p.get("type") for name, p in b.get("properties", {}).items()}


def _rt(v):
    return {"rich_text": [{"type": "text", "text": {"content": v}}]}


def add_schedule(name, when=None, place=None, people=None):
    """개인 일정 DB 에 행 하나 추가.

    name   : 일정 제목 (필수)
    when   : ISO8601 문자열. 날짜만이면 "2026-09-03", 시각 포함이면
             "2026-09-03T10:30:00+09:00" 처럼 타임존 오프셋까지 붙여서 넘긴다.
             범위 일정이면 "start/end" 형태로 "2026-09-03/2026-09-05" 처럼 넘긴다.
    place  : 장소 (없으면 생략)
    people : 함께하는 사람 (없으면 생략, 여러 명이면 "김지훈, 박서연" 처럼 콤마로)

    성공 시 생성된 페이지 dict 반환, 실패 시 SystemExit.
    """
    props = {P_NAME: {"title": [{"type": "text", "text": {"content": name}}]}}

    if when:
        if "/" in when:
            start, end = when.split("/", 1)
            props[P_TIME] = {"date": {"start": start.strip(), "end": end.strip()}}
        else:
            props[P_TIME] = {"date": {"start": when.strip()}}
    if place:
        props[P_PLACE] = _rt(place)
    if people:
        props[P_PEOPLE] = _rt(people)

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
        raise SystemExit("사용법: python notion_personal_schedule.py <입력.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    items = data if isinstance(data, list) else [data]
    for item in items:
        page = add_schedule(
            name=item["name"],
            when=item.get("when"),
            place=item.get("place"),
            people=item.get("people"),
        )
        print(f"OK  {item['name']}  -> {page.get('url')}")


if __name__ == "__main__":
    main()
