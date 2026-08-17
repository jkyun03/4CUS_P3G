import { useEffect, useState } from "react";
import { getJson } from "../api.js";
import RiskBadge from "../components/RiskBadge.jsx";
 
// 대시보드: 백엔드의 /analytics/summary(집계)와 /events(최근 이벤트)를 불러와 보여준다.
export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState("");
 
  useEffect(() => {
    // 화면이 뜰 때 백엔드에서 데이터를 가져온다
    Promise.all([getJson("/analytics/summary"), getJson("/events?limit=10")])
      .then(([s, e]) => {
        setSummary(s);
        setEvents(e);
      })
      .catch((err) => setError(err.message));
  }, []);
 
  if (error) {
    return (
      <div className="error-box">
        백엔드 연결 실패: {error}
        <br />
        백엔드 서버(uvicorn)가 켜져 있는지, CORS 설정을 했는지 확인하세요.
      </div>
    );
  }
  if (!summary) return <div className="loading">불러오는 중…</div>;
 
  return (
    <div>
      <h1 className="page-title">대시보드</h1>
 
      {/* 상단 KPI 카드 */}
      <div className="kpi-row">
        <Kpi label="오늘 탐지" value={summary.total_events} />
        <Kpi label="차단" value={summary.blocked} danger />
        <Kpi label="승인 대기" value={summary.pending_approvals} danger />
        <Kpi label="마스킹 적용" value={summary.masked} />
      </div>
 
      <div className="two-col">
        {/* 판정 분포 */}
        <div className="card">
          <div className="card-title">판정 분포</div>
          {Object.entries(summary.by_decision).map(([k, v]) => (
            <DistRow key={k} label={k} count={v} total={summary.total_events} />
          ))}
        </div>
 
        {/* 많이 쓰인 도구 Top */}
        <div className="card">
          <div className="card-title">도구 호출 Top</div>
          {summary.top_tools.map((t) => (
            <DistRow key={t.tool} label={t.tool} count={t.count} total={summary.total_events} mono />
          ))}
        </div>
      </div>
 
      {/* 최근 이벤트 표 */}
      <div className="card card-flush">
        <div className="card-title card-title-pad">실시간 이벤트</div>
        <table className="events-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>세션</th>
              <th>도구</th>
              <th>시간</th>
              <th>점수</th>
              <th>판정</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.event_id}>
                <td>{e.event_id}</td>
                <td>{e.session_id}</td>
                <td className="mono">{e.tool_name}</td>
                <td className="mono" title={e.created_at}>{formatTime(e.created_at)}</td>
                <td className={e.risk_score >= 80 ? "score-high" : ""}>{e.risk_score}</td>
                <td><RiskBadge decision={e.decision} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
 
function Kpi({ label, value, danger }) {
  return (
    <div className="kpi">
      <div className="kpi-label">{label}</div>
      <div className={"kpi-value" + (danger ? " danger" : "")}>{value}</div>
    </div>
  );
}
 
function DistRow({ label, count, total, mono }) {
  const pct = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="dist-row">
      <span className={"dist-label" + (mono ? " mono" : "")}>{label}</span>
      <span className="dist-bar"><span style={{ width: pct + "%" }} /></span>
      <span className="dist-count">{count}</span>
    </div>
  );
}
 
// 백엔드가 보내는 created_at 문자열엔 시간대 표시(Z, +09:00 등)가
// 없을 수 있다 (SQLite가 저장/조회 과정에서 시간대 정보를 날리는 문제).
// 표시가 없으면 "UTC였다"고 명시적으로 알려줘서, 브라우저가
// 로컬(한국) 시간으로 잘못 알고 변환을 건너뛰는 걸 막는다.
function toDate(isoString) {
  const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(isoString);
  return new Date(hasTimezone ? isoString : isoString + "Z");
}
 
// created_at(ISO 문자열)을 "N초 전" / "N분 전" / "HH:MM" / "MM/DD HH:MM" 형태로 바꿔준다.
// 오늘 발생한 이벤트는 시간만, 오늘이 아니면 날짜까지 같이 보여줘서
// "이게 오늘 건지 어제 건지" 헷갈리지 않게 한다.
function formatTime(isoString) {
  if (!isoString) return "-";
  const date = toDate(isoString);
  const now = new Date();
  const diffSec = Math.floor((now - date) / 1000);
 
  if (diffSec < 60) return `${diffSec}초 전`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}분 전`;
 
  const timeStr = date.toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Seoul",
  });
  const isToday = date.toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" })
    === now.toLocaleDateString("ko-KR", { timeZone: "Asia/Seoul" });
  if (isToday) return timeStr;
 
  const dateStr = date.toLocaleDateString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Seoul",
  });
  return `${dateStr} ${timeStr}`;
}
