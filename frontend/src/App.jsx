import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Approvals from "./pages/Approvals.jsx";
import Console from "./pages/Console.jsx";
import Logs from "./pages/Logs.jsx";  
import Analytics from "./pages/Analytics.jsx";
import Placeholder from "./pages/Placeholder.jsx";

// 화면 이동(라우팅) 규칙
export default function App() {
  return (
    <Routes>
      {/* 로그인은 사이드바 없이 단독으로 보여준다 */}
      <Route path="/" element={<Login />} />

      {/* 나머지 화면은 Layout(사이드바 + 본문) 안에서 보여준다 */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/approvals" element={<Approvals />} />
        {/* 아래는 아직 준비 중(플레이스홀더). 와이어프레임 기준으로 이어서 구현 */}
        <Route path="/console" element={<Console />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/tools" element={<Placeholder title="도구 관리" />} />
        <Route path="/policy" element={<Placeholder title="정책 설정" />} />
      </Route>
    </Routes>
  );
}
