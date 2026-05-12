import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import ChatView from "./views/ChatView";
import SettingsView from "./views/SettingsView";
import SetupView from "./views/SetupView";
import "./styles.css";

function NavBar() {
  const location = useLocation();
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => {});
  }, []);

  const navStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "center",
    padding: "0.75rem 1.5rem",
    background: "#0a0a0a",
    borderBottom: "1px solid #1e1e28",
    gap: "0.25rem",
    position: "sticky",
    top: 0,
    zIndex: 100,
  };

  const linkStyle = (active: boolean): React.CSSProperties => ({
    padding: "0.5rem 1rem",
    borderRadius: "6px",
    textDecoration: "none",
    fontSize: "0.875rem",
    fontWeight: 500,
    color: active ? "#00ff88" : "#6b6b7b",
    background: active ? "rgba(0,255,136,0.08)" : "transparent",
    border: active ? "1px solid rgba(0,255,136,0.2)" : "1px solid transparent",
    transition: "all 0.15s ease",
  });

  const logoStyle: React.CSSProperties = {
    fontFamily: "'IBM Plex Mono', monospace",
    fontWeight: 700,
    fontSize: "0.95rem",
    color: "#00ff88",
    marginRight: "1.5rem",
    textDecoration: "none",
    letterSpacing: "-0.02em",
  };

  const modelBadge: React.CSSProperties = {
    marginLeft: "auto",
    fontSize: "0.75rem",
    color: "#6b6b7b",
    fontFamily: "'IBM Plex Mono', monospace",
    padding: "0.25rem 0.6rem",
    background: "#111118",
    borderRadius: "4px",
    border: "1px solid #1e1e28",
  };

  return (
    <nav style={navStyle}>
      <Link to="/" style={logoStyle}>⚡ NexusClaw</Link>
      <Link to="/chat" style={linkStyle(location.pathname === "/chat")}>Chat</Link>
      <Link to="/settings" style={linkStyle(location.pathname === "/settings")}>Settings</Link>
      {config?.default_model && (
        <span style={modelBadge}>{config.default_model.split("/").pop()}</span>
      )}
    </nav>
  );
}

function App() {
  const [hasConfig, setHasConfig] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.ok)
      .then((ok) => setHasConfig(ok))
      .catch(() => setHasConfig(false));
  }, []);

  if (hasConfig === null) {
    return (
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center",
        height: "100vh", background: "#0a0a0a", color: "#6b6b7b",
        fontFamily: "'IBM Plex Mono', monospace", fontSize: "0.875rem"
      }}>
        Loading...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div style={{ minHeight: "100vh", background: "#0a0a0a" }}>
        <NavBar />
        <Routes>
          <Route
            path="/"
            element={hasConfig ? <Navigate to="/chat" replace /> : <Navigate to="/setup" replace />}
          />
          <Route path="/setup" element={<SetupView />} />
          <Route path="/chat" element={<ChatView />} />
          <Route path="/settings" element={<SettingsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
