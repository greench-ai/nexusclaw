import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import ChatView from "./views/ChatView";
import SettingsView from "./views/SettingsView";
import SetupView from "./views/SetupView";
import BrainView from "./views/BrainView";
import SkillsView from "./views/SkillsView";
import ManagerView from "./views/ManagerView";
import CollectionsView from "./views/CollectionsView";
import GroupChatView from "./views/GroupChatView";
import BrowserView from "./views/BrowserView";
import RAGView from "./views/RAGView";
import PromptsView from "./views/PromptsView";
import "./styles.css";

const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";

function NavBar() {
  const location = useLocation();
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then(setConfig)
      .catch(() => {});
  }, []);

  const isActive = (path: string) => location.pathname === path;

  const linkStyle = (active: boolean): React.CSSProperties => ({
    padding: "0.4rem 0.75rem",
    borderRadius: "6px",
    textDecoration: "none",
    fontSize: "0.78rem",
    fontWeight: 500,
    color: active ? ACCENT : TEXT2,
    background: active ? "rgba(0,255,136,0.08)" : "transparent",
    border: active ? "1px solid rgba(0,255,136,0.15)" : "1px solid transparent",
    transition: "all 150ms",
    whiteSpace: "nowrap" as const,
  });

  return (
    <nav style={{
      display: "flex",
      alignItems: "center",
      padding: "0.55rem 1.25rem",
      background: BG,
      borderBottom: `1px solid ${BORDER}`,
      gap: "0.2rem",
      position: "sticky",
      top: 0,
      zIndex: 100,
      overflowX: "auto",
    }}>
      <Link to="/" style={{
        fontFamily: "'IBM Plex Mono', monospace",
        fontWeight: 700,
        fontSize: "0.78rem",
        color: ACCENT,
        textDecoration: "none",
        marginRight: "1rem",
        letterSpacing: "-0.02em",
        flexShrink: 0,
      }}>
        ⚡ NexusClaw
      </Link>

      {[
        { path: "/chat", label: "Chat" },
        { path: "/brain", label: "Brain" },
        { path: "/skills", label: "Skills" },
        { path: "/manager", label: "Agents" },
        { path: "/collections", label: "Collections" },
        { path: "/group-chat", label: "Group Chat" },
        { path: "/browser", label: "Browser" },
        { path: "/rag", label: "RAG" },
        { path: "/prompts", label: "Prompts" },
      ].map(({ path, label }) => (
        <Link key={path} to={path} style={linkStyle(isActive(path))}>
          {label}
        </Link>
      ))}

      <div style={{ marginLeft: "auto", flexShrink: 0 }}>
        <Link to="/settings" style={linkStyle(isActive("/settings"))}>
          Settings
        </Link>
      </div>
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

  // Call useLocation unconditionally — hooks must fire before any early returns
  const location = useLocation();
  const isChat = location.pathname === "/chat";

  if (hasConfig === null) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        background: BG,
        color: TEXT2,
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: "0.875rem",
      }}>
        Loading…
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div style={{ minHeight: "100vh", background: BG }}>
        {!isChat && <NavBar />}
        <Routes>
          <Route path="/setup" element={<SetupView />} />

          {/* Full-height views (own layout) */}
          <Route path="/chat" element={<ChatView />} />

          {/* Standard views (nav bar + content) */}
          <Route path="/brain" element={<BrainView />} />
          <Route path="/skills" element={<SkillsView />} />
          <Route path="/manager" element={<ManagerView />} />
          <Route path="/collections" element={<CollectionsView />} />
          <Route path="/group-chat" element={<GroupChatView />} />
          <Route path="/browser" element={<BrowserView />} />
          <Route path="/rag" element={<RAGView />} />
          <Route path="/prompts" element={<PromptsView />} />
          <Route path="/settings" element={<SettingsView />} />

          {/* Root */}
          <Route
            path="/"
            element={hasConfig ? <Navigate to="/chat" replace /> : <Navigate to="/setup" replace />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
