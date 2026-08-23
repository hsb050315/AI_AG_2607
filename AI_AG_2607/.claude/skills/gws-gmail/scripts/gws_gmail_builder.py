"""
gws CLI를 감싸서 Gmail API로 이메일 초안을 만들고, 사용자 승인 후에만 그 초안을
전송하는 헬퍼 함수 모음.

이 스킬의 핵심 안전장치는 "초안 생성"과 "전송"을 서로 다른 두 API 호출로
분리해 두었다는 것이다:

1. create_draft(...) -> gws gmail +send --draft ...
   실제로 아무것도 보내지 않는다. Gmail 계정의 임시보관함(DRAFT)에 메시지를
   저장만 하고, 그 초안의 id를 반환한다.
2. send_draft(draft_id) -> gws gmail users drafts send ...
   1번에서 만든 초안을 실제로 발송한다. 이 함수는 사용자가 채팅에서 명시적으로
   전송을 승인한 뒤에만 호출해야 한다 (SKILL.md 흐름 참고).

직접 저수준 명령을 조립하지 말고, 이 파일의 함수를 그대로 가져다 쓴다.
"""

import json
import os
import shutil
import subprocess
import sys


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
    # `gws`가 "Using keyring backend: ..." 같은 안내 줄을 stdout 맨 앞에 섞어
    # 출력하는 경우가 있어, 실제 JSON이 시작하는 첫 '{' 위치부터 파싱한다.
    brace_index = stdout.find("{")
    if brace_index == -1:
        return {}
    return json.loads(stdout[brace_index:])


# ---------------------------------------------------------------------------
# 1단계: 초안 생성 (아무것도 발송하지 않음)
# ---------------------------------------------------------------------------

def create_draft(to, subject, body, cc=None, bcc=None, attachments=None, html=False):
    """Gmail 임시보관함에 초안을 저장한다. 실제 발송은 하지 않는다.

    Args:
        to: 받는사람 이메일 주소(쉼표로 여러 명 가능한 문자열 하나, 또는 리스트).
        subject: 제목.
        body: 본문. html=True면 HTML 조각으로 취급된다.
        cc, bcc: 선택. to와 동일한 형식.
        attachments: 선택. 첨부할 파일 경로 리스트.
        html: 본문을 HTML로 취급할지 여부 (기본 False = 일반 텍스트).

    Returns:
        {"draftId": ..., "messageId": ..., "threadId": ...}
    """
    def _join(value):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return ",".join(value)
        return value

    args = ["gmail", "+send", "--to", _join(to), "--subject", subject, "--body", body, "--draft"]

    cc = _join(cc)
    if cc:
        args += ["--cc", cc]
    bcc = _join(bcc)
    if bcc:
        args += ["--bcc", bcc]
    if html:
        args.append("--html")
    for path in attachments or []:
        args += ["-a", path]

    resp = _run_gws(args)
    message = resp.get("message", {})
    return {
        "draftId": resp.get("id"),
        "messageId": message.get("id"),
        "threadId": message.get("threadId"),
    }


# ---------------------------------------------------------------------------
# 2단계: 승인된 초안만 실제 전송
# ---------------------------------------------------------------------------

def send_draft(draft_id):
    """create_draft로 만든 초안을 실제로 전송한다.

    사용자가 채팅에서 "보내줘" 등으로 명시적으로 승인한 뒤에만 호출한다.
    이 함수 호출 자체가 실제 이메일 발송이라는 점을 항상 인지하고 사용한다.

    Returns:
        {"messageId": ..., "threadId": ..., "labelIds": [...]}
    """
    resp = _run_gws(
        [
            "gmail",
            "users",
            "drafts",
            "send",
            "--params",
            json.dumps({"userId": "me"}, ensure_ascii=False),
            "--json",
            json.dumps({"id": draft_id}, ensure_ascii=False),
        ]
    )
    return {
        "messageId": resp.get("id"),
        "threadId": resp.get("threadId"),
        "labelIds": resp.get("labelIds", []),
    }


def delete_draft(draft_id):
    """초안을 영구 삭제한다 (전송 취소 시 사용). 휴지통 이동이 아니라 즉시 완전 삭제된다."""
    return _run_gws(
        [
            "gmail",
            "users",
            "drafts",
            "delete",
            "--params",
            json.dumps({"userId": "me", "id": draft_id}, ensure_ascii=False),
        ]
    )


if __name__ == "__main__":
    print(
        "이 파일은 직접 실행하는 CLI가 아니라, SKILL.md 안내에 따라 import해서 쓰는 "
        "헬퍼 모듈입니다.",
        file=sys.stderr,
    )
