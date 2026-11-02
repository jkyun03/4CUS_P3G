// 감사 로그 화면: 이벤트 목록과 상세 탐지 사유.
import { useEffect, useState } from "react";
import { getJson } from "../api.js";
import RiskBadge from "../components/RiskBadge.jsx";

// 감사 로그: 왼쪽 목록(/events)에서 고르면 오른쪽에 상세(/events/{id})를 보여준다.
export default function Logs() {
  const [events, setEvents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getJson("/events?limit=50")
      .then((list) => {
        setEvents(list);
        if (list.length) select(list[0].event_id); // 첫 항목 자동 선택
      })
      .catch((e) => setError(e.message));
  }, []);

  const select = (id) =>
    getJson("/events/" + id).then(setSelected).catch((e) => setError(e.message));

  if (error) return <div className="error-box">연결 실패: {error}</div>;

  return (
    <div>
      <h1 className="page-title">감사 로그</h1>
      <div className="logs-split">
        <div className="card card-flush logs-list">
          {events.length === 0 && (
            <div className="empty" style={{ padding: 16 }}>이벤트가 없습니다.</div>
          )}
          {events.map((e) => (
            <div
              key={e.event_id}
              className={"log-row" + (selected && selected.event_id === e.event_id ? " active" : "")}
              onClick={() => select(e.event_id)}
            >
              <div className="log-row-top">
                <span className="mono">LOG-{e.event_id}</span>
                <RiskBadge decision={e.decision} />
              </div>
              <div className="log-row-sub">{e.session_id} · {e.tool_name} · {e.risk_score}점</div>
            </div>
          ))}
        </div>

        <div className="card">
          {!selected ? (
            <div className="empty">왼쪽에서 이벤트를 선택하세요.</div>
          ) : (
            <div>
              <div className="detail-head">
                <span className="mono" style={{ fontWeight: 600 }}>LOG-{selected.event_id}</span>
                <RiskBadge decision={selected.decision} />
              </div>
              <div className="detail-label">요청 원문</div>
              <div className="detail-quote">"{selected.user_request || "(없음)"}"</div>

              <div className="detail-label">호출 흐름</div>
              <div className="flow-inline">
                {selected.flow.map((t, i) => (
                  <span key={i}>
                    <span className="flow-pill mono">{t}</span>
                    {i < selected.flow.length - 1 && <span className="flow-arrow">→</span>}
                  </span>
                ))}
              </div>

              <div className="detail-label">위험 점수</div>
              <div className="detail-score">{selected.risk_score} / 100</div>

              <div className="detail-label">탐지 사유</div>
              <div className="detail-reasons">
                {selected.reasons.length === 0 && <div>위험 신호 없음</div>}
                {selected.reasons.map((r, i) => (
                  <div key={i}>• {r}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
