export const API_BASE = "http://localhost:8000";

let authToken = null;
let currentIdentity = null;

export function setAuth(token, identity) {
  authToken = token;
  currentIdentity = identity;
  sessionStorage.setItem("idea_token", token);
  sessionStorage.setItem("idea_identity", JSON.stringify(identity));
}

export function loadAuth() {
  authToken = sessionStorage.getItem("idea_token");
  const raw = sessionStorage.getItem("idea_identity");
  currentIdentity = raw ? JSON.parse(raw) : null;
  return currentIdentity;
}

export function getIdentity() {
  return currentIdentity;
}

export function logout() {
  authToken = null;
  currentIdentity = null;
  sessionStorage.removeItem("idea_token");
  sessionStorage.removeItem("idea_identity");
}

function authHeaders() {
  return authToken ? { Authorization: "Bearer " + authToken } : {};
}

export async function login(username, password) {
  let res;
  try {
    res = await fetch(API_BASE + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
  } catch (e) {
    // fetch 자체가 실패 = 백엔드 서버에 아예 연결이 안 된 것 (꺼져있음 / 포트 다름 / 네트워크 문제)
    throw new Error("서버에 연결할 수 없습니다. 백엔드(uvicorn)가 http://localhost:8000 에서 켜져 있는지 확인하세요.");
  }
  if (res.status === 401) throw new Error("아이디 또는 비밀번호가 올바르지 않습니다.");
  if (!res.ok) throw new Error(`로그인 실패 (서버 오류: ${res.status}). 백엔드 콘솔에 에러가 없는지 확인하세요.`);
  const data = await res.json();
  setAuth(data.access_token, { role: data.role, user_id: data.user_id, display_name: data.display_name });
  return data;
}

export async function getJson(path) {
  const res = await fetch(API_BASE + path, { headers: authHeaders() });
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}

export async function postJson(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}

export async function patchJson(path, body) {
  const res = await fetch(API_BASE + path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("요청 실패: " + res.status);
  return res.json();
}

export function openApprovalsSocket(onMessage) {
  const ws = new WebSocket("ws://localhost:8000/ws/approvals");
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

