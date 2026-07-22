# IDEA Gateway — Backend (Phase 1)

행동 기반 MCP 보안 게이트웨이의 백엔드. 이 Phase 1은 **핵심 흐름이 실제로 작동하는 최소 버전**이다.
여기에 팀원들이 기능을 하나씩 얹어 나간다.

지금 되는 것: 도구 호출 가로채기 → 세션 흐름 분석 → 위험 점수 → **허용 / 마스킹 / 경고 / 승인 / 차단** 결정 → 도구 실행(또는 차단) → 감사 로그 저장. 여기에 **툴 별 권한 관리**의 기초(도구 on/off, 역할별 허용)가 들어 있다.

---

## 1. 준비물

- **Python 3.10 이상** (`python --version` 으로 확인)
- 터미널(명령 프롬프트 / PowerShell / 터미널)

## 2. 설치 (처음 한 번만)

`backend` 폴더에서:

```bash
# 1) 가상환경 만들기 (이 프로젝트 전용 파이썬 공간)
python -m venv .venv

# 2) 가상환경 켜기
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 3) 라이브러리 설치
pip install -r requirements.txt
```

> 가상환경이 켜지면 터미널 앞에 `(.venv)` 가 붙는다. 작업할 때마다 켜면 된다.

## 3. 실행

```bash
uvicorn app.main:app --reload
```

- `--reload` : 코드를 고치면 서버가 자동으로 재시작(개발용).
- 브라우저에서 **http://127.0.0.1:8000/docs** 접속 → API를 눌러가며 직접 테스트할 수 있다(Swagger 문서).

`POST /v1/tool_call` 을 열고 `Try it out` → 아래 예시를 넣고 `Execute`:

```json
{
  "session_id": "S1",
  "user_request": "김민수 환자 예약 알려줘",
  "tool": "get_medical_record",
  "arguments": { "patient_id": "P1001" },
  "user_role": "doctor"
}
```

→ 진료기록이 **마스킹되어** 반환되는 걸 볼 수 있다.

## 4. 빠른 자동 테스트

서버를 안 띄우고도 6가지 시나리오를 한 번에 확인:

```bash
python test_smoke.py
```

기대 출력:

```text
[정상] search_patient  -> allow (0점)
[정상] get_appointment -> allow (0점) result={...}
[마스킹] get_medical_record -> mask (masked=True)
         결과: {'patient_id': 'P1001', 'diagnosis': '[비식별]', 'content': '[비식별]'}
[차단] send_email(외부) -> block (95점)
[권한] export_csv -> block  사유: ['비활성화된 도구: export_csv']
[권한] nurse 진료기록 -> block  사유: ["권한 없음: 'nurse' ..."]
```

---

## 5. 폴더 구조

```text
backend/
├── requirements.txt          설치할 라이브러리 목록
├── test_smoke.py             빠른 시나리오 테스트
└── app/
    ├── main.py               FastAPI 앱 시작점 (서버 실행 대상)
    ├── database.py           SQLite 연결 · 테이블 생성
    ├── models.py             DB 테이블 정의 (세션/호출/이벤트/도구)
    ├── seed.py               초기 도구 목록 삽입 (권한 설정)
    ├── mcp_tools/
    │   └── registry.py       가짜 도구 + 가짜 환자 데이터
    ├── core/                 ★ 보안 엔진 (프레임워크 무관, 테스트 쉬움)
    │   ├── analyzers.py      위험 행동 탐지 (흐름 기반)
    │   ├── scorer.py         위험 점수 합산
    │   ├── policy.py         점수 -> 허용/마스킹/승인/차단
    │   └── masking.py        민감정보 가리기
    └── api/
        └── tool_call.py      ★ POST /v1/tool_call (핵심 진입점)
```

`core/` 는 FastAPI/DB에 의존하지 않는 순수 파이썬이다. 그래서 판정 로직을 서버 없이 테스트할 수 있다(이게 "단단한 구현"의 핵심).

## 6. 요청 처리 순서 (`app/api/tool_call.py`)

1. 세션 확인/생성
2. 호출 기록 (`tool_calls`)
3. 세션 맥락(이전 호출들) 로드 — *세션 기반 기억의 기초*
4. **툴 별 권한 검사** — 도구가 꺼져 있거나 역할 권한이 없으면 즉시 차단
5. 분석(`analyzers`) → 점수(`scorer`) → 정책(`policy`)
6. 허용/경고/마스킹이면 도구 실행, 마스킹이면 결과를 가림
7. 이벤트(감사 로그) 저장 후 응답

---

## 7. 기능 로드맵 (팀 분담)

Phase 1에 이미 **기초가 들어간** 것: 툴 별 권한 관리, 세션 기반 기억, 마스킹(블랙리스트).
각자 아래 파일을 중심으로 확장한다.

| 우선순위 | 기능 | 담당 | 주로 손댈 곳 |
|---|---|---|---|
| 1 | 툴 별 권한 관리 | (팀) | `models.Tool`, `seed.py`, `tool_call.py` 권한 검사 + 도구 관리 API 신설 |
| 2 | 마스킹 (화이트리스트) | 서희 | `core/masking.py` (블랙리스트 → 화이트리스트로 확장) |
| 3 | 관리자 승인 (실시간) | 서이 | `core/policy.py`의 `approve` + 승인 대기(asyncio.Event) + WebSocket |
| 4 | 리포트 | 자경 | `reports/` 신설: `events` 집계 → CSV/PDF |
| - | 세션 기반 기억 | 유진 | `tool_call.py` 맥락 로드 확장(시간창/최근 N건) + `analyzers` |
| - | 과거 공격 대응(확장) | (팀) | 공격 시그니처 축적 → `analyzers`에 반영 |

### 새 기능 붙이는 법 (예: 새 탐지 규칙)

1. `core/analyzers.py`의 `analyze()`에 `signals.append(RiskSignal(...))` 한 줄 추가
2. `test_smoke.py`에 시나리오 추가해서 점수가 기대대로 나오는지 확인
3. 끝. (점수·정책은 자동으로 반영됨)

이렇게 "규칙 하나 = 코드 몇 줄"이라 초보자도 안전하게 확장할 수 있다.
