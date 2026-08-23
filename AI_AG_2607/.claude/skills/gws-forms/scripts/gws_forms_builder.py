"""
gws CLI를 감싸서 Google Forms API를 직접 호출해 실제 Google Form을 만드는 헬퍼 함수 모음.

Apps Script(FormApp) 경유 방식은 두 가지 실행 경로(Execution API, Web App)가 모두
플랫폼 차원의 제약(표준 GCP 프로젝트 바인딩 필요 / Google 봇 탐지 챌린지)에 막혀서
포기했고, 대신 gws의 forms 리소스(`gws forms forms ...`)로 Forms API v1을
직접 호출하는 방식으로 전환했다 (사용자 승인됨).

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
    """service_path 예: ["forms", "forms", "create"]"""
    args = list(service_path)
    if params is not None:
        args += ["--params", json.dumps(params, ensure_ascii=False)]
    if json_body is not None:
        args += ["--json", json.dumps(json_body, ensure_ascii=False)]
    return _run_gws(args)


# ---------------------------------------------------------------------------
# 폼 명세(items) -> Forms API v1 createItem 요청 변환
# ---------------------------------------------------------------------------

def _item_to_create_item_request(item, index):
    """items 리스트의 항목 하나를 batchUpdate용 createItem 요청으로 변환한다.

    지원 타입: TEXT, PARAGRAPH_TEXT, MULTIPLE_CHOICE, CHECKBOX, SCALE
    """
    item_type = item["type"]
    title = item["title"]
    required = bool(item.get("required", False))

    if item_type == "TEXT":
        question = {"required": required, "textQuestion": {"paragraph": False}}
    elif item_type == "PARAGRAPH_TEXT":
        question = {"required": required, "textQuestion": {"paragraph": True}}
    elif item_type == "MULTIPLE_CHOICE":
        question = {
            "required": required,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [{"value": c} for c in item["choices"]],
            },
        }
    elif item_type == "CHECKBOX":
        question = {
            "required": required,
            "choiceQuestion": {
                "type": "CHECKBOX",
                "options": [{"value": c} for c in item["choices"]],
            },
        }
    elif item_type == "SCALE":
        question = {
            "required": required,
            "scaleQuestion": {
                "low": int(item.get("lower", 1)),
                "high": int(item.get("upper", 5)),
                "lowLabel": item.get("lower_label", ""),
                "highLabel": item.get("upper_label", ""),
            },
        }
    else:
        raise ValueError(f"지원하지 않는 문항 타입: {item_type}")

    return {
        "createItem": {
            "item": {
                "title": title,
                "questionItem": {"question": question},
            },
            "location": {"index": index},
        }
    }


def build_batch_update_requests(form_description, items):
    """batchUpdate에 넘길 requests 배열을 만든다. (설명 설정 + 문항 추가들)"""
    requests = []
    if form_description:
        requests.append(
            {
                "updateFormInfo": {
                    "info": {"description": form_description},
                    "updateMask": "description",
                }
            }
        )
    for index, item in enumerate(items):
        requests.append(_item_to_create_item_request(item, index))
    return requests


# ---------------------------------------------------------------------------
# Forms API 직접 호출
# ---------------------------------------------------------------------------

def create_form(form_title, form_description, items):
    """Forms API로 폼을 생성하고 문항까지 채운 뒤 링크를 반환한다.

    반환값: {"editUrl": ..., "publishedUrl": ..., "formId": ...}
    """
    create_resp = _gws_call(
        ["forms", "forms", "create"],
        json_body={"info": {"title": form_title}},
    )
    form_id = create_resp["formId"]

    requests = build_batch_update_requests(form_description, items)
    if requests:
        _gws_call(
            ["forms", "forms", "batchUpdate"],
            params={"formId": form_id},
            json_body={"requests": requests},
        )

    get_resp = _gws_call(["forms", "forms", "get"], params={"formId": form_id})

    return {
        "editUrl": f"https://docs.google.com/forms/d/{form_id}/edit",
        "publishedUrl": get_resp.get("responderUri", ""),
        "formId": form_id,
    }


if __name__ == "__main__":
    print(
        "이 파일은 직접 실행하는 CLI가 아니라, SKILL.md 안내에 따라 import해서 쓰는 "
        "헬퍼 모듈입니다.",
        file=sys.stderr,
    )
