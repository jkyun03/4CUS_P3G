// 판정(decision) 값을 색깔 배지로 보여준다
const MAP = {
  allow:   { label: "허용", cls: "badge-allow" },
  mask:    { label: "마스킹", cls: "badge-mask" },
  warn:    { label: "경고", cls: "badge-warn" },
  approve: { label: "승인 필요", cls: "badge-approve" },
  block:   { label: "차단", cls: "badge-block" },
};

export default function RiskBadge({ decision }) {
  const d = MAP[decision] || { label: decision, cls: "badge-allow" };
  return <span className={"badge " + d.cls}>{d.label}</span>;
}
