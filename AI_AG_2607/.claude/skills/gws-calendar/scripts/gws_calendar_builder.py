"""
gws CLI를 감싸서 Google Calendar에 일정을 등록하는 헬퍼 함수 모음.

시간은 전부 RFC3339(ISO 8601) 형식의 문자열로 gws에 그대로 넘긴다. 사용자의
캘린더 기본 시간대(get_default_timezone)를 기준으로 오프셋을 붙여 넘기면 되고,
사용자가 이미 타임존이 포함된 시각을 말했다면 그걸 그대로 쓰면 된다.

직접 저수준 JSON을 조립하지 말고, 이 파일의 함수를 그대로 가져다 쓴다.
"""

import json
import os
import shutil
import subprocess

# npm 전역 설치본은 Windows에서 gws.cmd 래퍼로 깔리는 경우가 많다. subprocess가 shell 없이
# .cmd 파일을 실행하더라도 Windows는 내부적으로 cmd.exe를 거쳐 명령줄을 재해석하는데, 이
# 과정에서 인자에 포함된 "&", "|" 같은 문자가 명령 구분자로 오인되어 인자가 깨지는 문제가
# 있다. 그래서 gws.cmd를 직접 실행하는 대신, 그 안에서 감싸고 있는 진짜 실행 파일인
# node.exe + run.js를 찾아 바로 호출해서 cmd.exe 재해석 단계를 아예 건너뛴다.
def _resolve_gws_argv_prefix():
    gws_cmd = shutil.which("gws")
    if gws_cmd and gws_cmd.lower().endswith(".cmd"):
        dp0 = os.path.dirname(gws_cmd)
        run_js = os.path.join(dp0, "node_modules", "@googleworkspace", "cli", "run.js")
        if os.path.exists(run_js):
            node_bin = shutil.which("node") or "node"
            return [node_bin, run_js]
        return [gws_cmd]
    return [gws_cmd or "gws"]


_GWS_ARGV_PREFIX = _resolve_gws_argv_prefix()


def _run_gws(args):
    """gws CLI를 실행하고 stdout을 JSON으로 파싱해 반환한다. 실패 시 예외를 던진다."""
    result = subprocess.run(
        _GWS_ARGV_PREFIX + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gws {' '.join(args)} failed (exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    stdout = result.stdout.strip()
    if not stdout:
        return {}
    return json.loads(stdout)


def _gws_call(service_path, params=None, json_body=None):
    """service_path 예: ["calendar", "calendarList", "list"]"""
    args = list(service_path)
    if params is not None:
        args += ["--params", json.dumps(params, ensure_ascii=False)]
    if json_body is not None:
        args += ["--json", json.dumps(json_body, ensure_ascii=False)]
    return _run_gws(args)


# ---------------------------------------------------------------------------
# 캘린더 조회 / 시간대
# ---------------------------------------------------------------------------

def get_default_timezone():
    """사용자 캘린더의 기본 시간대(IANA 이름, 예: 'Asia/Seoul')를 반환한다.
    사용자가 시각을 말할 때 별도 시간대를 언급하지 않았다면 이 시간대로 해석한다."""
    result = _gws_call(["calendar", "settings", "get"], params={"setting": "timezone"})
    return result.get("value", "UTC")


def find_calendars(name_query=None):
    """사용자의 calendarList를 반환한다. name_query가 있으면 summary에 해당 문자열이
    포함된 캘린더만 걸러서 반환한다 (대소문자 무시). name_query가 없으면(=기본 캘린더로
    등록하기로 확인된 경우) 호출할 필요 없다 — calendar_id="primary"를 그대로 쓰면 된다."""
    result = _gws_call(["calendar", "calendarList", "list"])
    items = result.get("items", [])
    if not name_query:
        return items
    q = name_query.lower()
    return [c for c in items if q in c.get("summary", "").lower()]


# ---------------------------------------------------------------------------
# 일정 등록
# ---------------------------------------------------------------------------

def insert_event(summary, start, end, calendar_id="primary", location=None, description=None):
    """일정을 등록한다.

    summary: 일정 제목
    start, end: RFC3339 형식 문자열 (예: "2026-08-24T14:00:00+09:00"). 종일 일정이 아니라
      특정 시각이 있는 일정만 다룬다 — 날짜/시각을 이 형식으로 조합해서 넘긴다.
    calendar_id: 기본은 "primary"(주 캘린더). 특정 캘린더에 등록하기로 확인됐다면
      find_calendars로 찾은 항목의 "id" 값을 넘긴다.
    location, description: 선택 사항. 사용자가 언급하지 않았으면 넘기지 않는다.

    반환값은 생성된 이벤트 리소스(JSON) 그대로다. 결과 보고에는 반환값의
    "htmlLink"(사용자가 클릭해서 캘린더에서 바로 볼 수 있는 링크)를 사용한다.
    """
    args = [
        "calendar", "+insert",
        "--summary", summary,
        "--start", start,
        "--end", end,
        "--calendar", calendar_id,
    ]
    if location:
        args += ["--location", location]
    if description:
        args += ["--description", description]
    return _run_gws(args)
