import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { login } from "../api.js";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("doctor_kim");
  const [password, setPassword] = useState("pass1234");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setError("");
    try {
      await login(username, password);
      navigate("/dashboard");
    } catch (e) {
      setError("아이디 또는 비밀번호가 올바르지 않습니다.");
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-head">
          <ShieldCheck size={32} color="#ff4628" />
          <div className="login-title">IDEA Gateway</div>
          <div className="login-sub">관리자 콘솔 로그인</div>
        </div>

        <label className="field-label">아이디</label>
        <input className="field" value={username} onChange={(e) => setUsername(e.target.value)} />

        <label className="field-label">비밀번호</label>
        <input className="field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

        <button className="btn-primary btn-full" onClick={handleLogin}>로그인</button>
        <div className="login-note">
          데모 계정: doctor_kim / nurse_lee / pharm01 / sysadmin01 등 (비밀번호 pass1234)
        </div>
      </div>
    </div>
  );
}

