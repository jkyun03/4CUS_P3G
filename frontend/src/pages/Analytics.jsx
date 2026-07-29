import { useEffect, useState } from "react";
import { getJson } from "../api.js";

// 분석·리포트: /analytics/summary 를 불러와 통계를 보여준다.
export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getJson("/analytics/summary").then(setSummary).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error-box">연결 실패: {error}</div>;
  if (!summary) return <div className="loading">불러오는 중…</div>;

  return (
    <div>
      <h1 className="page-title">분석 · 리포트</h1>

      <div className="kpi-row">
        <Kpi label="총 이벤트" value={summary.total_events} />
        <Kpi label="차단" value={summary.blocked} danger />
        <Kpi label="마스킹" value={summary.masked} />
        <Kpi label="승인 대기" value={summary.pending_approvals} danger />
      </div>

      <div className="two-col">
        <div className="card">
          <div className="card-title">판정 분포</div>
          {Object.entries(summary.by_decision).map(([k, v]) => (
            <Dist key={k} label={k} count={v} total={summary.total_events} />
          ))}
        </div>
        <div className="card">
          <div className="card-title">도구 호출 Top</div>
          {summary.top_tools.map((t) => (
            <Dist key={t.tool} label={t.tool} count={t.count} total={summary.total_events} mono />
          ))}
        </div>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <div className="card-title">리포트 내보내기</div>
        <div className="empty" style={{ padding: "4px 0" }}>
          CSV · PDF · 컴플라이언스 리포트는 리포트 2단계에서 추가 예정입니다.
        </div>
        <button className="btn-secondary" disabled>리포트 생성 (준비 중)</button>
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
function Dist({ label, count, total, mono }) {
  const pct = total ? Math.round((count / total) * 100) : 0;
  return (
    <div className="dist-row">
      <span className={"dist-label" + (mono ? " mono" : "")}>{label}</span>
      <span className="dist-bar"><span style={{ width: pct + "%" }} /></span>
      <span className="dist-count">{count}</span>
    </div>
  );
}