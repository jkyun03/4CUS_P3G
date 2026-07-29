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
