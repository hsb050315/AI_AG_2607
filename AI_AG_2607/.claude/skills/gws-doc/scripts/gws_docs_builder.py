"""
gws CLI를 감싸서 Google Docs 문서를 조립하는 헬퍼 함수 모음.

이 문서의 배경: Google Docs API는 모든 삽입 위치를 문자 인덱스(UTF-16 code unit)로
지정해야 한다. 특히 표의 각 셀에 텍스트를 채울 때는 인덱스가 앞쪽 셀 삽입으로 인해
뒤쪽 셀의 인덱스가 밀리기 때문에, 반드시 "뒤쪽 셀 -> 앞쪽 셀" 역순으로 삽입해야
한 번의 batchUpdate로 안전하게 채울 수 있다. 이 파일은 그 인덱스 계산을 대신 해준다.

직접 저수준 JSON을 조립하지 말고, 이 파일의 함수를 그대로 가져다 쓴다.
"""

import json
import os
import shutil
import subprocess
import sys

# npm 전역 설치본은 Windows에서 gws.cmd 래퍼로 깔리는 경우가 많다. subprocess가 shell 없이
# .cmd 파일을 실행하더라도 Windows는 내부적으로 cmd.exe를 거쳐 명령줄을 재해석하는데, 이
# 과정에서 인자에 포함된 "&", "|" 같은 문자가 명령 구분자로 오인되어 인자가 깨지는 문제가
# 있다(예: --json 안의 텍스트에 "&"가 들어가면 JSON이 잘려 파싱 에러가 난다). 그래서
# gws.cmd를 직접 실행하는 대신, 그 안에서 감싸고 있는 진짜 실행 파일인 node.exe + run.js를
# 찾아 바로 호출해서 cmd.exe 재해석 단계를 아예 건너뛴다.
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
    """service_path 예: ["docs", "documents", "get"]"""
    args = list(service_path)
    if params is not None:
        args += ["--params", json.dumps(params, ensure_ascii=False)]
    if json_body is not None:
        args += ["--json", json.dumps(json_body, ensure_ascii=False)]
    return _run_gws(args)


# ---------------------------------------------------------------------------
# Drive 폴더 검색 / 문서 생성
# ---------------------------------------------------------------------------

def find_folders(name_query):
    """이름에 name_query가 들어간, trash되지 않은 폴더 목록을 반환한다.
    (본인 소유가 아니어도 목록엔 나오지만, 쓰기 권한이 없으면 create_document가 실패할 수 있다 —
    실패 시 다른 폴더를 선택하거나 최상위(My Drive)에 만들도록 사용자에게 안내한다.)"""
    escaped = name_query.replace("'", "\\'")
    q = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name contains '{escaped}' and trashed=false"
    )
    resp = _gws_call(
        ["drive", "files", "list"],
        params={"q": q, "pageSize": 20, "fields": "files(id,name,parents)"},
    )
    return resp.get("files", [])


def create_folder(name, parent_id=None):
    """Google Drive에 폴더를 생성한다. parent_id를 주면 그 폴더 안에 생성된다.
    반환값: 생성된 폴더의 id (str)"""
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    resp = _gws_call(
        ["drive", "files", "create"],
        params={"fields": "id,name,parents"},
        json_body=body,
    )
    return resp["id"]


def set_anyone_reader_permission(document_id):
    """문서를 '링크가 있는 모든 사용자 - 뷰어'로 공개 설정한다."""
    return _gws_call(
        ["drive", "permissions", "create"],
        params={"fileId": document_id, "fields": "id"},
        json_body={"role": "reader", "type": "anyone"},
    )


def create_document(title, folder_id=None):
    """Google Docs 문서를 생성한다. folder_id를 주면 그 폴더 안에 바로 생성된다
    (생성 후 이동시키는 방식은 공유 드라이브/권한 문제로 실패하는 경우가 많아 사용하지 않는다).
    반환값: documentId (str)"""
    body = {"name": title, "mimeType": "application/vnd.google-apps.document"}
    if folder_id:
        body["parents"] = [folder_id]
    resp = _gws_call(
        ["drive", "files", "create"],
        params={"fields": "id,name,parents"},
        json_body=body,
    )
    return resp["id"]


def get_share_link(document_id):
    return f"https://docs.google.com/document/d/{document_id}/edit"


# ---------------------------------------------------------------------------
# 문서 내부 상태 조회 (인덱스 계산용)
# ---------------------------------------------------------------------------

def get_document(document_id):
    return _gws_call(
        ["docs", "documents", "get"],
        params={"documentId": document_id},
    )


def _end_of_body_index(doc):
    """본문 맨 끝(마지막 암묵적 개행 직전) 삽입 지점의 인덱스를 반환한다."""
    content = doc["body"]["content"]
    return content[-1]["endIndex"] - 1


def batch_update(document_id, requests):
    if not requests:
        return {}
    return _gws_call(
        ["docs", "documents", "batchUpdate"],
        params={"documentId": document_id},
        json_body={"requests": requests},
    )


# ---------------------------------------------------------------------------
# 콘텐츠 추가 함수 (SKILL.md에서 이것만 호출하면 된다)
# ---------------------------------------------------------------------------

def add_title(document_id, text):
    _append_styled_line(document_id, text, "TITLE")


def add_subtitle(document_id, text):
    _append_styled_line(document_id, text, "SUBTITLE")


def add_heading(document_id, text, level=1):
    assert 1 <= level <= 6
    _append_styled_line(document_id, text, f"HEADING_{level}")


def _append_styled_line(document_id, text, named_style_type):
    """텍스트 한 줄을 문서 끝에 추가하고 지정한 문단 스타일을 적용한다."""
    doc = get_document(document_id)
    start_index = _end_of_body_index(doc)
    line = text + "\n"
    batch_update(
        document_id,
        [{"insertText": {"endOfSegmentLocation": {}, "text": line}}],
    )
    end_index = start_index + len(line)
    batch_update(
        document_id,
        [
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "paragraphStyle": {"namedStyleType": named_style_type},
                    "fields": "namedStyleType",
                }
            }
        ],
    )


def add_paragraph(document_id, text):
    """일반 본문 문단을 문서 끝에 추가한다 (기본 스타일 NORMAL_TEXT라 스타일 적용 불필요)."""
    batch_update(
        document_id,
        [{"insertText": {"endOfSegmentLocation": {}, "text": text + "\n"}}],
    )


def add_emphasized_paragraph(document_id, text, bold=True, red=True):
    """본문 문단을 추가하고, 필요 시 굵게+빨간색 텍스트 스타일을 적용한다.
    가장 중요한 부분을 강조 표시할 때 add_paragraph 대신 사용한다."""
    doc = get_document(document_id)
    start_index = _end_of_body_index(doc)
    line = text + "\n"
    batch_update(
        document_id,
        [{"insertText": {"endOfSegmentLocation": {}, "text": line}}],
    )
    if not (bold or red):
        return
    end_index = start_index + len(text)
    text_style = {}
    fields = []
    if bold:
        text_style["bold"] = True
        fields.append("bold")
    if red:
        text_style["foregroundColor"] = {
            "color": {"rgbColor": {"red": 0.8, "green": 0.0, "blue": 0.0}}
        }
        fields.append("foregroundColor")
    batch_update(
        document_id,
        [
            {
                "updateTextStyle": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "textStyle": text_style,
                    "fields": ",".join(fields),
                }
            }
        ],
    )


def add_bullet_list(document_id, items):
    """items(문자열 리스트)를 글머리 기호 목록으로 문서 끝에 추가한다."""
    if not items:
        return
    doc = get_document(document_id)
    start_index = _end_of_body_index(doc)
    block = "".join(item + "\n" for item in items)
    batch_update(
        document_id,
        [{"insertText": {"endOfSegmentLocation": {}, "text": block}}],
    )
    end_index = start_index + len(block)
    batch_update(
        document_id,
        [
            {
                "createParagraphBullets": {
                    "range": {"startIndex": start_index, "endIndex": end_index},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            }
        ],
    )


def add_table(document_id, headers, rows):
    """headers(문자열 리스트) + rows(문자열 리스트의 리스트)로 표를 문서 끝에 추가한다.
    모든 행의 길이는 headers와 같아야 한다."""
    num_cols = len(headers)
    for row in rows:
        assert len(row) == num_cols, "모든 행의 칸 수는 headers와 같아야 합니다."

    doc = get_document(document_id)
    insert_index = _end_of_body_index(doc)
    num_rows = len(rows) + 1

    batch_update(
        document_id,
        [
            {
                "insertTable": {
                    "rows": num_rows,
                    "columns": num_cols,
                    "location": {"index": insert_index},
                }
            }
        ],
    )

    # 표가 삽입된 뒤 실제 구조를 다시 읽어 각 셀의 시작 인덱스를 알아낸다.
    doc = get_document(document_id)
    table_element = _find_table_at_or_after(doc, insert_index)
    cell_start_indices = []
    for table_row in table_element["table"]["tableRows"]:
        for cell in table_row["tableCells"]:
            cell_start_indices.append(cell["content"][0]["startIndex"])

    all_rows = [headers] + [list(r) for r in rows]
    flat_texts = [cell for row in all_rows for cell in row]
    assert len(flat_texts) == len(cell_start_indices)

    # 뒤(마지막 셀)에서부터 앞으로 삽입해야 앞쪽 삽입이 뒤쪽 인덱스를 밀지 않는다.
    requests = []
    for idx, text in reversed(list(zip(cell_start_indices, flat_texts))):
        if text:
            requests.append({"insertText": {"location": {"index": idx}, "text": text}})
    batch_update(document_id, requests)


def _find_table_at_or_after(doc, index):
    for element in doc["body"]["content"]:
        if "table" in element and element["startIndex"] >= index:
            return element
    raise RuntimeError("삽입한 표를 문서에서 찾지 못했습니다.")


if __name__ == "__main__":
    print(
        "이 파일은 직접 실행하는 CLI가 아니라, SKILL.md 안내에 따라 import해서 쓰는 "
        "헬퍼 모듈입니다.",
        file=sys.stderr,
    )
