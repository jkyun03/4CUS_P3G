// 승인 큐 화면: 승인 대기 요청 목록, 실시간 알림, 승인/거부 처리.
import { useEffect, useState } from "react";
import { getJson, postJson, openApprovalsSocket } from "../api.js";

// 승인 큐: 대기 중인 승인 요청을 보여주고, 실시간 알림(WebSocket)을 받고,
// 승인/거부 버튼으로 백엔드에 결정을 보낸다.
export default function Approvals() {
  const [pending, setPending] = useState([]);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  // 대기 목록을 다시 불러오는 함수
  const load = () =>
    getJson("/approvals?status=pending")
      .then(setPending)
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
    // 새 승인 요청이 오면 토스트를 띄우고 목록을 갱신한다
    const ws = openApprovalsSocket((msg) => {
      if (msg.type === "new_approval") {
        setToast("새 승인 요청: " + msg.tool + " (" + msg.risk_score + "점)");
        load();
        setTimeout(() => setToast(""), 4000);
      }
    });
    // 화면을 떠날 때 WebSocket 연결을 닫는다
    return () => ws.close();
  }, []);

  // 승인 또는 거부 결정을 백엔드에 보낸다
  const decide = async (id, decision) => {
    try {
      await postJson("/approvals/" + id + "/decide", { decision, admin_id: "admin" });
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div>
      <h1 className="page-title">승인 큐</h1>

      {toast && <div className="toast">{toast}</div>}
      {error && <div className="error-box">연결 실패: {error}</div>}
      {pending.length === 0 && !error && (
        <div className="empty">대기 중인 승인 요청이 없습니다.</div>
      )}

      {pending.map((ap) => (
        <div className="card approval-card" key={ap.id}>
          <div className="approval-head">
            <span className="approval-title">
              요청 #{ap.id} · <span className="mono">{ap.tool_name}</span>
            </span>
            <span className="score-pill">{ap.risk_score}점</span>
          </div>
          <div className="approval-reasons">
            {ap.reasons.map((r, i) => (
              <div key={i}>• {r}</div>
            ))}
          </div>
          <div className="approval-actions">
            <button className="btn-secondary" onClick={() => decide(ap.id, "reject")}>거부</button>
            <button className="btn-primary" onClick={() => decide(ap.id, "approve")}>승인하고 실행</button>
          </div>
        </div>
      ))}
    </div>
  );
}
