"""4개 DB에 가상 데이터 3행씩 추가한다."""
import scripts.notion.create_databases as m


def rt(v):
    return {"rich_text": [{"type": "text", "text": {"content": v}}]}


def title(v):
    return {"title": [{"type": "text", "text": {"content": v}}]}


def date(v):
    return {"date": {"start": v}}


def url(v):
    return {"url": v}


ROWS = {
    "3ca24c48-3f29-8144-bc14-cb974b431278": [  # 개인 일정
        {"이름": title("치과 정기검진"), "장소": rt("서울 강남 미소치과"), "시간": date("2026-09-03T10:30:00"), "함께하는 사람": rt("혼자")},
        {"이름": title("대학 동기 모임"), "장소": rt("홍대 소셜포차"), "시간": date("2026-09-06T19:00:00"), "함께하는 사람": rt("김지훈, 박서연, 이도윤")},
        {"이름": title("부모님 결혼기념일 저녁"), "장소": rt("잠실 한정식 예담"), "시간": date("2026-09-12T18:00:00"), "함께하는 사람": rt("아버지, 어머니, 동생")},
    ],
    "3ca24c48-3f29-81ac-bfef-d5842e3ead82": [  # 업무
        {"이름": title("3분기 실적 보고서 작성"), "등록일": date("2026-08-25"), "잔여기한": date("2026-09-05"), "제출처": rt("경영지원팀 이과장")},
        {"이름": title("신규 협력사 계약서 검토"), "등록일": date("2026-08-27"), "잔여기한": date("2026-09-02"), "제출처": rt("법무팀")},
        {"이름": title("사내 워크숍 기획안 제출"), "등록일": date("2026-08-28"), "잔여기한": date("2026-09-15"), "제출처": rt("인사팀 채널")},
    ],
    "3ca24c48-3f29-81af-9b52-d7b5ccde708a": [  # 학습
        {"이름": title("생성형 AI 에이전트 아키텍처 학습"), "보고서제목": rt("AI 에이전트 설계 패턴 정리"), "출처": rt("Anthropic 공식 문서")},
        {"이름": title("데이터 파이프라인 기초"), "보고서제목": rt("ETL vs ELT 비교 노트"), "출처": rt("오라일리 - Fundamentals of Data Engineering")},
        {"이름": title("노션 API 연동 실습"), "보고서제목": rt("Notion REST API 연동 리포트"), "출처": rt("developers.notion.com")},
    ],
    "3ca24c48-3f29-81b8-afe3-c406689e03c9": [  # 완료작업
        {"이름": title("카드뉴스 6프레임 제작"), "담당자": rt("포포"), "소요기간": rt("3일"), "자료 위치": url("https://github.com/hsb050315/AI_AG_2607/tree/main/output")},
        {"이름": title("회사소개 페이지 웹디자인 기획안"), "담당자": rt("웹 기획자"), "소요기간": rt("2일"), "자료 위치": url("https://github.com/hsb050315/AI_AG_2607/tree/main/output/reports")},
        {"이름": title("노션 DB 5개 생성 및 연동"), "담당자": rt("포포"), "소요기간": rt("1일"), "자료 위치": url("https://www.notion.so/3c924c483f2980aaaab1cdfdf4c156a4")},
    ],
}


def main():
    m.load_env()
    for db_id, rows in ROWS.items():
        for props in rows:
            s, b = m.call("/pages", method="POST", payload={"parent": {"database_id": db_id}, "properties": props})
            tag = props["이름"]["title"][0]["text"]["content"]
            print(f"{'OK ' if s == 200 else 'ERR'} [{db_id[:8]}] {tag}" + ("" if s == 200 else f"  {b.get('message')}"))


if __name__ == "__main__":
    main()
