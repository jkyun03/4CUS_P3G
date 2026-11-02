// 정책 설정 화면: 경고/승인/차단 임계값 조정.
import { useEffect, useState } from "react";
import { getJson, patchJson } from "../api.js";

// 정책 설정: 위험 점수 판정 임계값(경고/승인/차단 경계)을 조정한다.
export default function Policy() {
  const [rules, setRules] = useState(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getJson("/rules").then(setRules).catch((e) => setError(e.message));
  }, []);

  const setField = (key, value) => {
    setRules({ ...rules, [key]: Number(value) });
    setSaved(false);
  };

  const save = async () => {
    setError("");
    setSaved(false);
    try {
      const updated = await patchJson("/rules", rules);
      setRules(updated);
      setSaved(true);
    } catch (e) {
      setError("저장 실패: 경고 < 승인 < 차단 순서와 0~100 범위를 확인하세요.");
    }
  };

  if (error && !rules) return <div className="error-box">연결 실패: {error}</div>;
  if (!rules) return <div className="loading">불러오는 중…</div>;

  return (
    <div>
      <h1 className="page-title">정책 설정</h1>

      <div className="card">
        <div className="card-title">위험 점수 판정 기준</div>
        <p className="policy-desc">
          각 구간의 경계 점수를 조정하면 게이트웨이 판정에 바로 반영됩니다.
        </p>

        <div className="range-bar">
          <span className="seg seg-allow" style={{ width: rules.warn + "%" }}>허용</span>
          <span className="seg seg-warn" style={{ width: (rules.approve - rules.warn) + "%" }}>경고</span>
          <span className="seg seg-approve" style={{ width: (rules.block - rules.approve) + "%" }}>승인</span>
          <span className="seg seg-block" style={{ width: (100 - rules.block) + "%" }}>차단</span>
        </div>

        <div className="policy-fields">
          <Field label="경고 시작 점수" value={rules.warn} onChange={(v) => setField("warn", v)} />
          <Field label="승인 필요 시작 점수" value={rules.approve} onChange={(v) => setField("approve", v)} />
          <Field label="차단 시작 점수" value={rules.block} onChange={(v) => setField("block", v)} />
        </div>

        {error && <div className="policy-error">{error}</div>}
        {saved && <div className="policy-saved">저장되었습니다.</div>}
        <button className="btn-primary" onClick={save} style={{ marginTop: 14 }}>저장</button>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div className="policy-field">
      <label>{label}</label>
      <input type="number" min="0" max="100" value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}
