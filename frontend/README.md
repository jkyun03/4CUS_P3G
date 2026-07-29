# IDEA Gateway — Frontend (React + Vite)

관리자 콘솔 화면. 백엔드(FastAPI)를 호출해 데이터를 보여준다.

## 준비물
- Node.js 18 이상 (`node --version` 으로 확인)

## 실행 순서
1. **백엔드를 먼저 켠다** — `backend` 폴더에서: `uvicorn app.main:app --reload`
2. 이 `frontend` 폴더에서:
   ```bash
   npm install      # 처음 한 번만
   npm run dev
   ```
3. 브라우저에서 **http://localhost:5173**

## 지금 되는 화면
- **로그인** — 진입 화면 (버튼 누르면 대시보드로 이동. 로그인 API는 아직 없음)
- **대시보드** — KPI · 판정 분포 · 도구 Top · 실시간 이벤트 (`/analytics/summary`, `/events` 연동)
- **승인 큐** — 대기 목록 + 실시간 알림 + 승인/거부 (`/approvals`, `/ws/approvals` 연동)
- 나머지(시연 콘솔 · 감사 로그 · 분석·리포트 · 도구 관리 · 정책 설정)는 **준비 중**(플레이스홀더)

## 폴더 구조
```
src/
├── api.js          백엔드 호출 함수 (여기서 백엔드 주소를 설정)
├── theme.css       색상·레이아웃 (와이어프레임 디자인)
├── App.jsx         화면 이동(라우팅) 규칙
├── components/     Sidebar · Layout · RiskBadge (공통)
└── pages/          Login · Dashboard · Approvals · Placeholder
```

## 자주 만나는 문제
- **대시보드에 "백엔드 연결 실패"** → 백엔드(uvicorn)가 안 켜졌거나, 백엔드에 CORS 설정이 없음.
- **표가 비어 있음** → 백엔드에 `GET /events` 엔드포인트가 있어야 함. 그리고 이벤트가 있어야 보이니, 스웨거나 시연 콘솔로 요청을 몇 번 보내 데이터를 쌓아둘 것.
- **백엔드 주소가 다름** → `src/api.js` 의 `API_BASE` 수정.
