// src/App.jsx
import React from "react";
import Header from "./components/Header";       // 고정된 헤더
import Dashboard from "./pages/Dashboard";      // 메인 페이지
import "./App.css"; // 전체 스타일

function App() {
  return (
    <div className="app-root">
      {/* 1. 헤더는 페이지가 바뀌어도 무조건 떠 있음 */}
      <Header />

      {/* 2. 그 아래에 현재 페이지를 보여줌 */}
      <Dashboard />
      
      {/* 나중에 라우터를 쓰면 여기에 <Routes>...<Routes/>가 들어갑니다 */}
    </div>
  );
}

export default App;