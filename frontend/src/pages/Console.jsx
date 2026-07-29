import { useState } from "react";
import { postJson } from "../api.js";
import RiskBadge from "../components/RiskBadge.jsx";

const ROLES = [
  "doctor", "nurse", "pharmacist", "admin_staff", "insurance_reviewer",
  "security_officer", "system_admin", "intern", "hospital_admin",
];

const SCENARIOS = {
  "정상": {
    request: "김민수 환자의 다음 예약 시간을 알려줘",
    steps: [
      { tool: "search_patient", arguments: { name: "김민수" } },
      { tool: "get_appointment", arguments: { patient_id: "P1001" } },
    ],
  },
  "위험 1 · 외부전송": {
    request: "김민수 환자의 다음 예약 시간을 알려줘",
    steps: [
      { tool: "search_patient", arguments: { name: "김민수" } },
      { tool: "get_medical_record", arguments: { patient_id: "P1001" } },
      { tool: "send_email", arguments: { to: "external@gmail.com", body: "..." } },
    ],
  },
  "위험 2 · 대량조회": {
    request: "오늘 예약자 명단 확인해줘",
    steps: [
      { tool: "get_medical_record", arguments: { patient_id: "P1001" } },
      { tool: "get_medical_record", arguments: { patient_id: "P1002" } },
      { tool: "get_medical_record", arguments: { patient_id: "P1001" } },
      { tool: "export_csv", arguments: {} },
    ],
  },
  "담당 환자 vs 비담당": {
    request: "진료기록 확인",
    steps: [
      { tool: "get_medical_record", arguments: { patient_id: "P1001" } },
      { tool: "get_medical_record", arguments: { patient_id: "P1002" } },
    ],
  },
};

export default function Console() {
  const [selected, setSelected] = useState("위험 1 · 외부전송");
  const [role, setRole] = useState("doctor");
  const [userId, setUserId] = useState("doctor_kim");
  const [steps, setSteps] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setError("");
    setSteps([]);
    setRunning(true);
    const scenario = SCENARIOS[selected];
    const sessionId = "CONSOLE-" + Date.now();
    const results = [];
    try {
      for (const step of scenario.steps) {
        const r = await postJson("/v1/tool_call", {
          session_id: sessionId,
          user_request: scenario.request,
          tool: step.tool,
          arguments: step.arguments,
          user_role: role,
          user_id: userId,
        });
        results.push({ tool: step.tool, ...r });
        setSteps([...results]);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  const maxScore = steps.reduce((m, s) => Math.max(m, s.risk_score), 0);
  const finalDecision = steps.length ? steps[steps.length - 1].decision : null;

  return (
    <div>
      <h1 className="page-title">시연 콘솔</h1>

      <div className="chip-row">
        {Object.keys(SCENARIOS).map((name) => (
          <button
            key={name}
            className={"chip" + (selected === name ? " active" : "")}
            onClick={() => setSelected(name)}
          >
            {name}
          </button>
        ))}
      </div>

      <div className="console-run">
        <div className="console-request">"{SCENARIOS[selected].request}"</div>

        <select className="role-select" value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>

        <input
          className="console-request"
          style={{ flex: "none", width: 140 }}
          placeholder="user_id"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />

        <button className="btn-primary" onClick={run} disabled={running}>
          {running ? "실행 중…" : "실행"}
        </button>
      </div>

      {error && <div className="error-box">연결 실패: {error} (백엔드가 켜져 있는지 확인)</div>}

      {steps.length > 0 && (
        <div className="two-col">
          <div className="card">
            <div className="card-title">행동 흐름</div>
            {steps.map((s, i) => (
              <div className="flow-step" key={i}>
                <div className={"flow-dot " + dotClass(s.decision)} />
                <div className="flow-body">
                  <span className="mono">{s.tool}()</span>
                  <div className="flow-meta">
                    <RiskBadge decision={s.decision} />
                    <span className="flow-reason">{topReason(s)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="card judge-card">
            <div className="card-title">판정</div>
            <div className={"judge-score" + (maxScore >= 80 ? " danger" : "")}>{maxScore}</div>
            <div className="judge-reasons">
              {lastReasons(steps).map((r, i) => (
                <div key={i}>• {r}</div>
              ))}
            </div>
            <div className="judge-final">
              최종 판정 <RiskBadge decision={finalDecision} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function dotClass(decision) {
  if (decision === "block") return "dot-block";
  if (["approve", "warn", "mask"].includes(decision)) return "dot-warn";
  return "dot-ok";
}
function topReason(s) {
  return s.reasons && s.reasons.length ? s.reasons[s.reasons.length - 1] : "정상";
}
function lastReasons(steps) {
  const last = steps[steps.length - 1];
  return last.reasons && last.reasons.length ? last.reasons : ["위험 신호 없음"];
}
