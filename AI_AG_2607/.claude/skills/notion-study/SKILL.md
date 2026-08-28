---
name: notion-study
description: 사용자가 공부하거나 학습·조사한 내용(강의 수강, 문서 정독, 책 챕터, 기술 리서치 등)을 Notion "학습" 데이터베이스에 학습 기록으로 저장해주는 스킬입니다. Notion API 를 직접 호출해 사용자의 진짜 노션 워크스페이스에 행을 추가합니다. 사용자가 "이거 학습 DB에 저장해줘", "노션 학습에 기록해줘", "공부한 거 노션에 정리해줘", "학습 로그 남겨줘", "이 자료 학습 노트로 노션에 넣어줘" 처럼 요청하면 사용하세요. 방금 조사·정리한 내용을 "학습 기록으로 노션에 남겨줘"라고 하거나, 대화 맥락상 노션 학습 DB 를 의미하면 적극적으로 트리거하세요. 단, 마감 있는 업무는 notion-work 를, 개인 약속은 notion-personal 을, 단순 요약만 원하면 이 스킬을 쓰지 않습니다.
---

# notion-study: Notion "학습" DB 저장

사용자가 학습·조사한 내용을 파싱해서 Notion "학습" 데이터베이스에 학습 기록 한 줄로 저장하는 스킬이다. 번들된 `scripts/notion_study_log.py` 의 함수를 그대로 쓴다 — Notion 저수준 요청 JSON 을 매번 직접 조립하지 않는다.

이번 버전은 **새 학습 기록 저장만** 다룬다. 기존 기록 조회·수정·삭제는 범위 밖이며, 사용자가 그런 요청을 하면 이 스킬이 저장만 지원한다는 걸 알리고 어떻게 도울지 되묻는다.

## 사전 조건

- 프로젝트 루트 `.env` 에 `NOTION_API_KEY` 가 있어야 한다 (통합 토큰, `ntn_` 또는 `secret_` 로 시작). 없으면 사용자에게 알리고 `output/guides/notion-db-api-setup.md` 를 참고하라고 안내한다.
- "학습" DB ID 는 스크립트에 기본값으로 박혀 있다. 다른 DB 를 쓰려면 `.env` 에 `NOTION_STUDY_DB_ID=` 를 넣으면 그 값이 우선한다.

## "학습" DB 스키마 (2026-08 기준)

| 속성 | 타입 | 설명 |
|------|------|------|
| `이름` | title | 학습 주제 (필수) |
| `보고서제목` | rich_text | 정리한 보고서·노트의 제목 |
| `출처` | rich_text | 학습 출처 — 문서명, 책, URL, 강의명 등 |

작업 시작 시 `get_schema()` 로 실제 스키마를 한 번 확인한다. 속성 이름/타입이 위 표와 다르면 사용자에게 알리고, 바뀐 이름에 맞춰 값을 넣는다 (스크립트의 `P_NAME` 등 상수를 그 자리에서 맞게 조정).

## 전체 흐름

1. **학습 정보 파악** — 사용자 요청(또는 방금 진행한 조사/정리 결과)에서 학습 주제, 보고서 제목, 출처를 뽑는다.
   - 주제(`이름`)가 없으면 저장 전에 되물어본다. 다만 대화에서 방금 조사·정리한 내용이 있으면 그 핵심을 한 줄 주제로 요약해 제안하고 확인받는다.
   - `보고서제목`: 방금 만든 문서(구글 독스, docx, 노트 등)가 있으면 그 제목을 쓴다. 없으면 학습 내용을 대표하는 짧은 제목을 제안해 확인받거나, 비워둔다.
   - `출처`: 실제로 참고한 자료(URL, 문서명, 책, 강의)가 확인되면 넣는다. 모르면 지어내지 말고 비워두거나 사용자에게 물어본다.

2. **저장 실행** — `scripts/notion_study_log.py` 의 `add_log(...)` 를 호출한다 (아래 "스크립트 사용법").

3. **결과 보고** — 성공하면 반환된 페이지의 `url` 을 사용자에게 전달하고, 실제로 저장된 주제/보고서제목/출처를 요약해 알린다. 1번에서 제안·가정한 부분이 있으면 명시한다.

## 스크립트 사용법

한글이 인자·리터럴로 들어가므로, **셸 명령줄에 한글을 직접 넘기지 않는다.** 대신:

1. Write 도구로 입력값을 담은 JSON 파일을 스크래치패드에 만든다 (경로는 ASCII).
2. 그 JSON 경로만 인자로 넘겨 스크립트를 실행한다.

```json
// C:\...\scratchpad\notion_study_input.json
{
  "name": "생성형 AI 에이전트 아키텍처 학습",
  "report_title": "AI 에이전트 설계 패턴 정리",
  "source": "Anthropic 공식 문서 (docs.anthropic.com)"
}
```

여러 건이면 위 객체들의 배열로 만든다.

```bash
python .claude/skills/notion-study/scripts/notion_study_log.py C:/.../scratchpad/notion_study_input.json
```

또는 Write 로 작은 파이썬 실행 파일을 만들어 함수를 직접 호출해도 된다:

```python
import sys
sys.path.insert(0, r"<이 스킬 폴더>/scripts")
from notion_study_log import load_env, get_schema, add_log

load_env()
# print(get_schema())  # 스키마 확인
page = add_log(
    name="데이터 파이프라인 기초",
    report_title="ETL vs ELT 비교 노트",
    source="오라일리 - Fundamentals of Data Engineering",
)
print(page["url"])
```

- `report_title`, `source` 는 선택 인자다. 언급이 없으면 넘기지 않는다.
- 실행 셸은 Bash / PowerShell 어느 쪽이어도 되지만, 인자로 넘기는 파일 경로는 ASCII 여야 한다.

## 오류 대응

- `NOTION_API_KEY 가 .env 에 없습니다` → 사용자에게 `.env` 에 토큰을 넣어달라고 안내.
- `저장 실패 404` → 통합이 이 DB 에 연결(공유)되지 않음. 노션에서 DB 페이지 우상단 `•••` → "연결" → 통합 추가 필요.
- `저장 실패 400` + `is not a property that exists` → DB 속성 이름이 바뀜. `get_schema()` 결과를 사용자에게 보여주고 매핑을 맞춘다.
- `저장 실패 429` → 잠시 후 재시도 (Notion 레이트리밋, 평균 3req/s).

## 하지 말아야 할 것

- 학습 주제가 불분명한데 임의로 지어내 저장하지 않는다 — 방금 조사한 내용이 있으면 요약해 확인받고, 없으면 되묻는다.
- 출처를 추측해서 지어내지 않는다 — 확인 안 되면 비워둔다.
- Notion API 요청 JSON 을 직접 조립하지 않는다 — `notion_study_log.py` 함수를 쓴다.
- 조회·수정·삭제 요청을 저장으로 오인하지 않는다 — 이 스킬은 새 학습 기록 저장만 한다.
- 마감 있는 업무는 `notion-work`, 개인 약속은 `notion-personal` 로 넘긴다.
