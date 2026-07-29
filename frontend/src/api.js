// 백엔드(FastAPI) 주소. 백엔드는 http://localhost:8000 에서 실행된다고 가정.
export const API_BASE = "http://localhost:8000";

// GET 요청 (JSON 받기)
export async function getJson(path) {
  const res = await fetch(API_BASE + path);
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}

// POST 요청 (JSON 보내고 받기)
export async function postJson(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}

// 실시간 알림용 WebSocket 연결. 새 승인 요청이 오면 onMessage 가 호출된다.
export function openApprovalsSocket(onMessage) {
  const ws = new WebSocket("ws://localhost:8000/ws/approvals");
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

// PATCH 요청 (일부 수정)
export async function patchJson(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}