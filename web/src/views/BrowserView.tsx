import { useState, useEffect, useRef } from "react";
import { Globe, Play, Square, RefreshCw, Trash2, Camera, ChevronDown, ExternalLink } from "lucide-react";

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

interface BrowserSession {
  id: string;
  url: string;
  title?: string;
}

export default function BrowserView() {
  const [url, setUrl] = useState("https://example.com");
  const [sessions, setSessions] = useState<BrowserSession[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>("idle");
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => { loadSessions(); }, []);

  async function loadSessions() {
    try {
      const res = await fetch("/api/v1/browser/sessions");
      if (res.ok) setSessions(await res.json());
    } catch { /* ignore */ }
  }

  async function startSession() {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/v1/browser/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      if (res.ok) {
        const s = await res.json();
        setActiveSession(s.id);
        setUrl(s.url || url);
        loadSessions();
        await takeScreenshot(s.id);
      }
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function takeScreenshot(sessionId?: string) {
    const sid = sessionId || activeSession;
    if (!sid) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/browser/sessions/${sid}/screenshot`);
      if (res.ok) {
        const data = await res.json();
        setScreenshot(data.screenshot || null);
      }
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function closeSession(sid: string) {
    try {
      await fetch(`/api/v1/browser/sessions/${sid}`, { method: "DELETE" });
      if (activeSession === sid) setActiveSession(null);
      loadSessions();
    } catch { /* ignore */ }
  }

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <Globe size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Browser</h1>
        <span style={{ marginLeft: 8, fontSize: 11, color: TEXT2, background: SURFACE, padding: "2px 8px", borderRadius: 10, border: `1px solid ${BORDER}`, fontFamily: "'IBM Plex Mono', monospace" }}>
          Playwright
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 240px", gap: 16 }}>
        {/* Main panel */}
        <div>
          {/* URL bar */}
          <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
            <input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && startSession()}
              placeholder="https://…"
              style={{ flex: 1, padding: "9px 13px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 7, color: TEXT, fontSize: 13, outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
            />
            <button
              onClick={startSession}
              disabled={loading}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 16px", background: ACCENT, color: "#000", border: "none", borderRadius: 7, fontSize: 13, cursor: loading ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: loading ? 0.6 : 1 }}
            >
              <Globe size={13} /> {loading ? "Loading…" : "Navigate"}
            </button>
            <button
              onClick={() => takeScreenshot()}
              disabled={!activeSession || loading}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 12px", background: SURFACE, color: activeSession ? TEXT2 : "transparent", border: `1px solid ${BORDER}`, borderRadius: 7, fontSize: 13, cursor: activeSession ? "pointer" : "not-allowed", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
            >
              <Camera size={13} />
            </button>
          </div>

          {/* Browser preview */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, overflow: "hidden", minHeight: 500 }}>
            {screenshot ? (
              <img
                src={`data:image/png;base64,${screenshot}`}
                alt="Browser screenshot"
                style={{ width: "100%", display: "block", borderRadius: 10 }}
              />
            ) : activeSession ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 500, flexDirection: "column", gap: 10 }}>
                <Globe size={32} style={{ color: BORDER }} />
                <p style={{ color: TEXT2, fontSize: 13, margin: 0 }}>Session active. Taking screenshot…</p>
              </div>
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 500, flexDirection: "column", gap: 10 }}>
                <Globe size={40} style={{ color: BORDER }} />
                <p style={{ color: TEXT2, fontSize: 14, margin: 0 }}>Enter a URL and click Navigate to open a browser session.</p>
                <p style={{ color: TEXT2, fontSize: 12, margin: 0 }}>Screenshots are captured via Playwright.</p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar — sessions */}
        <div>
          <h3 style={{ margin: "0 0 10px", fontSize: 12, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Sessions</h3>
          {sessions.length === 0 ? (
            <p style={{ color: TEXT2, fontSize: 12 }}>No active sessions.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => { setActiveSession(s.id); takeScreenshot(s.id); }}
                  style={{
                    background: s.id === activeSession ? "rgba(0,255,136,0.06)" : SURFACE,
                    border: `1px solid ${s.id === activeSession ? ACCENT : BORDER}`,
                    borderRadius: 7,
                    padding: "9px 11px",
                    cursor: "pointer",
                    transition: "all 150ms",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                    <Globe size={11} style={{ color: s.id === activeSession ? ACCENT : TEXT2 }} />
                    <span style={{ fontSize: 11, color: TEXT, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1, fontFamily: "'IBM Plex Mono', monospace" }}>
                      {s.url}
                    </span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontSize: 10, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>{s.id.slice(0, 8)}…</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); closeSession(s.id); }}
                      style={{ marginLeft: "auto", background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 2, display: "flex", alignItems: "center" }}
                    >
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Info */}
          <div style={{ marginTop: 20, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: 12 }}>
            <h4 style={{ margin: "0 0 8px", fontSize: 11, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Browser Control</h4>
            <p style={{ margin: 0, fontSize: 12, color: TEXT2, lineHeight: 1.5 }}>
              Playwright-based browser automation. Start a session, navigate to any URL, and capture screenshots. Sessions persist until manually closed.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
