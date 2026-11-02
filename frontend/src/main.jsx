// React 앱 진입점.
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { loadAuth } from "./api.js";
import "./theme.css";

// 새로고침해도 로그인 상태가 유지되도록, 렌더링 전에 세션스토리지에서 토큰을 복구한다.
loadAuth();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
