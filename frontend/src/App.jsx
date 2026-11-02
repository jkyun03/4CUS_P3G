// 화면 라우팅: 로그인 화면과, 사이드바 레이아웃 안의 관리자 콘솔 화면들.
import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Approvals from "./pages/Approvals.jsx";
import Console from "./pages/Console.jsx";
import Logs from "./pages/Logs.jsx";
import Analytics from "./pages/Analytics.jsx";
import Tools from "./pages/Tools.jsx";
import Policy from "./pages/Policy.jsx";

export default function App() {
  return (
    <Routes>
      {/* 로그인은 사이드바 없이 단독으로 보여준다 */}
      <Route path="/" element={<Login />} />

      {/* 나머지 화면은 Layout(사이드바 + 본문) 안에서 보여준다 */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/console" element={<Console />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/tools" element={<Tools />} />
        <Route path="/policy" element={<Policy />} />
      </Route>
    </Routes>
  );
}
