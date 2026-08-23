---
name: gws-forms
description: 사용자가 입력한 제약 조건과 자료를 바탕으로 실제 Google Forms(설문지/폼)를 만들어주는 스킬입니다. gws CLI로 Google Forms API를 직접 호출해서 사용자의 진짜 Google Drive/계정에 폼을 생성합니다. 사용자가 "구글 폼 만들어줘", "설문지 만들어줘", "Forms로 설문 만들어줘", "구글 설문 하나 만들어줘", "폼 제작해줘" 처럼 요청하면 사용하세요.
---

# gws-forms: Google Forms 제작 (Forms API 직접 호출 방식)

사용자가 말한 제약 조건과 자료를 바탕으로 (1) 폼 문항 구성 확정 → (2) Google Forms API 요청 조립 → (3) 실제 Google Form 생성까지 끝내는 스킬이다. `gws` CLI의 `forms` 리소스(`gws forms forms create` / `batchUpdate` / `get`)로 Forms API v1을 직접 호출한다. 매번 저수준 API 호출을 직접 짜지 말고, 번들된 `scripts/gws_forms_builder.py`의 함수를 그대로 가져다 쓴다.

## 전체 흐름

1. **폼 요구사항 파악** — 사용자가 준 제약 조건/자료에서 폼 제목, 설명, 문항 목록(문항별 유형·필수 여부·선택지 등)을 뽑는다.
   - 제목과 문항이 하나도 없으면 진행 전에 반드시 사용자에게 물어본다.
   - 문항 유형이 명시되지 않았으면 내용상 자연스러운 유형(단답형/서술형/객관식/체크박스/척도)으로 합리적으로 가정하되, 가정한 부분은 결과 보고 시 알린다.
   - 객관식/체크박스인데 선택지가 빠져 있으면 억지로 지어내지 말고 되물어본다.

2. **문항 스펙 구성** — 아래 "지원하는 문항 유형"에 맞춰 `items` 리스트(딕셔너리 리스트)를 만든다.

3. **폼 생성** — `scripts/gws_forms_builder.py`의 `create_form(form_title, form_description, items)`로 한 번에 처리한다 (아래 "스크립트 사용법" 참고).

4. **결과 보고** — 반환된 `publishedUrl`(응답자용 링크)과 `editUrl`(편집용 링크)을 사용자에게 전달하고, 실제로 만들어진 문항 구성과 1번 단계에서 가정한 부분이 있다면 그것도 요약해서 알린다.

## 지원하는 문항 유형

`items`는 딕셔너리 리스트이며, 각 항목은 `"type"`에 따라 나머지 키가 달라진다.

- `{"type": "TEXT", "title": str, "required": bool}` — 단답형
- `{"type": "PARAGRAPH_TEXT", "title": str, "required": bool}` — 장문형
- `{"type": "MULTIPLE_CHOICE", "title": str, "choices": [str, ...], "required": bool}` — 객관식(단일 선택)
- `{"type": "CHECKBOX", "title": str, "choices": [str, ...], "required": bool}` — 체크박스(복수 선택)
- `{"type": "SCALE", "title": str, "lower": int, "upper": int, "lower_label": str, "upper_label": str, "required": bool}` — 선형 배율(척도)

이 다섯 가지 외의 유형(파일 업로드, 섹션 나누기, 날짜/시간, 그리드 등)은 이번 버전 범위 밖이다 — 사용자가 요청하면 현재는 지원하지 않는다고 알린다.

## 스크립트 사용법

`scripts/gws_forms_builder.py`에 있는 함수를 그대로 사용한다. `gws` 저수준 명령을 매번 직접 짜지 않는다.

```python
import sys
sys.path.insert(0, "<이 스킬 폴더>/scripts")
from gws_forms_builder import create_form

result = create_form(
    form_title="행사 참가 신청서",
    form_description="아래 항목을 작성해주세요.",
    items=[
        {"type": "TEXT", "title": "이름", "required": True},
        {"type": "MULTIPLE_CHOICE", "title": "참가 여부", "choices": ["참가", "불참"], "required": True},
        {"type": "SCALE", "title": "만족도", "lower": 1, "upper": 5,
         "lower_label": "낮음", "upper_label": "높음", "required": False},
    ],
)

print(result["publishedUrl"])  # 응답자에게 공유할 링크
print(result["editUrl"])       # 폼 편집 링크
```

- `create_form`은 내부적으로 `gws forms forms create`(제목만 생성) → `gws forms forms batchUpdate`(설명·문항 추가) → `gws forms forms get`(응답 링크 조회)까지 한 번에 처리한다. 단계별로 직접 호출해야 하는 특수한 경우가 아니면 `create_form`만 쓰면 된다.
- Forms API로 생성한 폼은 기본적으로 게시되어 응답을 즉시 수집한다(`isPublished`/`isAcceptingResponses` 모두 true) — 별도 게시 작업이 필요 없다.

### 한글(비-ASCII) 텍스트를 다룰 때 주의할 점

폼 제목/문항/선택지 대부분이 한글이므로, 이 함수들을 호출하는 파이썬 코드를 실행할 셸 도구 선택이 중요하다.

- **Bash 도구(Git Bash/MSYS)로 한글이 포함된 명령을 실행하면, 파이썬 프로세스가 시작되기도 전에 인자 문자열 자체가 깨진다.** 이는 `gws`나 이 스크립트의 버그가 아니라 Bash 도구가 명령줄을 자식 프로세스에 전달하는 방식 자체의 문제라, 스크립트 쪽에서 고칠 수 없다.
- 한글(또는 다른 비-ASCII 문자)이 포함된 문자열을 인라인 `python -c "..."` 형태로 실행해야 한다면, **Bash 도구 대신 PowerShell 도구를 사용한다.**
- 가장 안전한 방법은 한글 문자열을 명령줄 인자로 아예 넘기지 않는 것이다 — Write 도구로 파이썬 스크립트 파일(.py)을 작성해서 그 안에 한글 리터럴(제목, 문항, 선택지 등)을 넣고, 그 파일 경로(ASCII)만 셸 명령의 인자로 넘겨 실행한다.
- 콘솔에 결과를 바로 출력하면 PowerShell 콘솔 인코딩 때문에 한글이 깨져 보일 수 있다 — 실제 데이터는 정상이니, 확인이 필요하면 UTF-8로 파일에 써서 확인한다.

## 하지 말아야 할 것

- 제목이나 문항처럼 핵심 정보가 빠졌는데 임의로 채워서 만들지 않는다.
- 객관식/체크박스 선택지가 빠졌는데 지어내서 채우지 않는다.
- `gws` 저수준 명령이나 Forms API 요청을 직접 짜지 않는다 — `gws_forms_builder.py`의 함수를 사용한다.
