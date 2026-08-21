import { useEffect, useState } from "react";
import { getJson, patchJson } from "../api.js";

// masking.py의 FIELD_POLICY와 동일한 9개 직군
const ALL_ROLES = [
  "doctor", "nurse", "pharmacist", "admin_staff", "insurance_reviewer",
  "security_officer", "system_admin", "intern", "hospital_admin",
];

// 도구 관리: /tools 목록을 표로 보여주고, 토글로 on/off, 직군 칩으로 권한을 바꾼다.
export default function Tools() {
  const [tools, setTools] = useState([]);
  const [error, setError] = useState("");     // 목록 자체를 못 불러온 경우 (전체 화면 대체)
  const [actionError, setActionError] = useState(""); // 토글 하나 실패한 경우 (토스트로만 표시)

  const load = () => getJson("/tools").then(setTools).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const showActionError = (message) => {
    setActionError(message);
    setTimeout(() => setActionError(""), 4000);
  };

  const toggleEnabled = async (t) => {
    try {
      await patchJson("/tools/" + t.name, { enabled: !t.enabled });
      load();
    } catch (e) { showActionError(e.message); }
  };

  const toggleRole = async (t, role) => {
    const roles = t.allowed_roles.includes(role)
      ? t.allowed_roles.filter((r) => r !== role)
      : [...t.allowed_roles, role];
    try {
      await patchJson("/tools/" + t.name, { allowed_roles: roles });
      load();
    } catch (e) { showActionError(e.message); }
  };

  if (error) return <div className="error-box">연결 실패: {error}</div>;

  return (
    <div>
      <h1 className="page-title">도구 관리</h1>
      {actionError && <div className="toast" style={{ borderLeftColor: "var(--brand)" }}>⚠ {actionError}</div>}
      <div className="card card-flush">
        <table className="tools-table">
          <thead>
            <tr>
              <th>도구</th><th>역할</th><th>위험도</th><th>활성화</th><th>허용 직군</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((t) => (
              <tr key={t.name}>
                <td className="mono">{t.name}</td>
                <td>{t.role}</td>
                <td><span className={"risk-tag risk-" + t.base_risk}>{riskLabel(t.base_risk)}</span></td>
                <td>
                  <button
                    className={"toggle" + (t.enabled ? " on" : "")}
                    onClick={() => toggleEnabled(t)}
                    aria-label="활성화 토글"
                  >
                    <span className="toggle-knob" />
                  </button>
                </td>
                <td>
                  <div className="role-chips" style={{ flexWrap: "wrap" }}>
                    {ALL_ROLES.map((role) => (
                      <button
                        key={role}
                        className={"role-chip" + (t.allowed_roles.includes(role) ? " on" : "")}
                        onClick={() => toggleRole(t, role)}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="empty" style={{ fontSize: 12 }}>
        도구를 끄거나 직군을 바꾸면 시연 콘솔·게이트웨이 판정에 바로 반영됩니다.
      </div>
    </div>
  );
}

function riskLabel(r) {
  return { low: "낮음", medium: "중간", high: "높음" }[r] || r;
}

