# IDEA Gateway — Frontend (React + Vite)

게이트웨이 관리자 콘솔 화면. 백엔드(FastAPI)를 호출해 판정 결과·감사 로그·승인 대기열을 보여준다.
프로젝트 전체 설명은 [루트 README](../README.md)를 참고.

## 준비물
- Node.js 18 이상 (`node --version` 으로 확인)

## 실행 순서
1. **백엔드를 먼저 켠다** — `backend` 폴더에서: `uvicorn app.main:app --reload`
2. 이 `frontend` 폴더에서:
   ```bash
   npm install      # 처음 한 번만
   npm run dev
   ```
3. 브라우저에서 **http://localhost:5173** 접속 후 데모 계정으로 로그인 (예: `doctor_kim` / `pass1234`)

## 화면
| 경로 | 화면 | 사용하는 API |
|---|---|---|
| `/` | 로그인 | `POST /auth/login` |
| `/dashboard` | 대시보드 | `/analytics/summary`, `/events` |
| `/console` | 시연 콘솔 | `POST /v1/tool_call`, `/tools` |
| `/approvals` | 승인 큐 | `/approvals`, `/approvals/{id}/decide`, `ws /ws/approvals` |
| `/logs` | 감사 로그 | `/events`, `/events/{id}` |
| `/analytics` | 분석·리포트 | `/analytics/summary`, `/reports/events.csv`, `/reports/events.pdf` |
| `/tools` | 도구 관리 | `/tools`, `PATCH /tools/{name}` |
| `/policy` | 정책 설정 | `/rules`, `PATCH /rules` |

## 폴더 구조
```
src/
├── api.js          백엔드 호출 함수 · 로그인 토큰 관리 (여기서 백엔드 주소 API_BASE 설정)
├── theme.css       색상·레이아웃
├── App.jsx         화면 라우팅
├── components/     Layout · Sidebar · RiskBadge (공통)
└── pages/          Login · Dashboard · Console · Approvals · Logs · Analytics · Tools · Policy
```

## 자주 만나는 문제
- **"서버에 연결할 수 없습니다"** → 백엔드(uvicorn)가 `http://localhost:8000` 에서 켜져 있는지 확인.
- **표가 비어 있음** → 이벤트가 쌓여야 보인다. 시연 콘솔에서 시나리오를 몇 번 실행해 데이터를 만든다.
- **도구·정책 변경 시 403** → 관리자 계정(`sysadmin01`, `hospadmin01`)으로 로그인해야 한다.
- **백엔드 주소가 다름** → `src/api.js` 의 `API_BASE` 수정.
