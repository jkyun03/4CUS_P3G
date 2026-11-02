// 사이드바 + 본문 공통 레이아웃.
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar.jsx";

// 사이드바 + 본문(현재 화면)을 나란히 배치하는 공통 레이아웃
export default function Layout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
