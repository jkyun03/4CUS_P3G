import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

// 진입 화면(로그인). 아직 로그인 API가 없으므로 버튼을 누르면 대시보드로 이동한다.
export default function Login() {
  const navigate = useNavigate();
  const handleLogin = () => navigate("/dashboard");

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-head">
          <ShieldCheck size={32} color="#ff4628" />
          <div className="login-title">IDEA Gateway</div>
          <div className="login-sub">관리자 콘솔 로그인</div>
        </div>

        <label className="field-label">아이디</label>
        <input className="field" placeholder="admin@hospital.org" />

        <label className="field-label">비밀번호</label>
        <input className="field" type="password" placeholder="********" />

        <button className="btn-primary btn-full" onClick={handleLogin}>로그인</button>
        <div className="login-note">권한이 없는 사용자는 접근할 수 없습니다</div>
      </div>
    </div>
  );
}
