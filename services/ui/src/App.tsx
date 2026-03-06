import React from "react";
import { Link, Route, Routes, Navigate } from "react-router-dom";
import Nurse from "./pages/Nurse";
import Supervisor from "./pages/Supervisor";

export default function App() {
  return (
    <div className="container">
      <div className="row" style={{ alignItems: "center", justifyContent: "space-between" }}>
        <div className="h1">Agent Platform MVP UI</div>
        <div style={{ display: "flex", gap: 12 }}>
          <Link to="/nurse">Nurse</Link>
          <Link to="/supervisor">Supervisor</Link>
        </div>
      </div>

      <Routes>
        <Route path="/" element={<Navigate to="/nurse" replace />} />
        <Route path="/nurse" element={<Nurse />} />
        <Route path="/supervisor" element={<Supervisor />} />
      </Routes>

      <div className="small" style={{ marginTop: 14 }}>
        Uses Vite proxy: UI → <code>/api</code> → agent-runtime container (<code>http://agent-runtime:8080</code>)
      </div>
    </div>
  );
}
