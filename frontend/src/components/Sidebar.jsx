import { NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, PlayCircle, ListChecks, Clock,
  BarChart3, Wrench, SlidersHorizontal, ShieldCheck, LogOut,
} from "lucide-react";
import { getIdentity, logout } from "../api.js";

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
  const navigate = useNavigate();
  const identity = getIdentity();
  const displayName = identity?.display_name || identity?.user_id || "로그인 필요";

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <ShieldCheck size={20} color="#ff4628" />
        <span>P3G</span>
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
        <span className="avatar">{displayName[0]}</span>
        <span>{displayName}</span>
        <button className="logout-btn" onClick={handleLogout} title="로그아웃" aria-label="로그아웃">
          <LogOut size={15} />
        </button>
      </div>
    </aside>
  );
}
