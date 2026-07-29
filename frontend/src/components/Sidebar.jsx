import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, PlayCircle, ListChecks, Clock,
  BarChart3, Wrench, SlidersHorizontal, ShieldCheck,
} from "lucide-react";

const items = [
  { to: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { to: "/console", label: "시연 콘솔", icon: PlayCircle },
  { to: "/logs", label: "감사 로그", icon: ListChecks },
  { to: "/approvals", label: "승인 큐", icon: Clock },
  { to: "/analytics", label: "분석·리포트", icon: BarChart3 },
  { to: "/tools", label: "도구 관리", icon: Wrench },
  { to: "/policy", label: "정책 설정", icon: SlidersHorizontal },
];

// 왼쪽 다크 내비게이션 바
export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <ShieldCheck size={20} color="#ff4628" />
        <span>IDEA Gateway</span>
      </div>
      <nav className="sidebar-nav">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
          >
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-user">
        <span className="avatar">관</span>
        <span>보안관리자</span>
      </div>
    </aside>
  );
}
