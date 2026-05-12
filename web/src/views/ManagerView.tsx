import { useEffect, useState } from "react";
import { Cpu, Zap, Clock, Trash2, RefreshCw, PlayCircle, PauseCircle } from "lucide-react";

interface AgentSession {
  id: string;
  name: string;
  status: "running" | "idle" | "complete" | "error";
  created_at: string;
  updated_at: string;
  model?: string;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

export default function ManagerView() {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadSessions(); }, []);

  async function loadSessions() {
    setLoading(true);
    try {
      // Try the agents endpoint
      const res = await fetch("/api/v1/agents");
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      } else {
        setSessions([]);
      }
    } catch {
      setSessions([]);
    }
    setLoading(false);
  }

  async function deleteSession(id: string) {
    if (!confirm("Delete this agent session?")) return;
    try {
      await fetch(`/api/v1/agents/sessions/${id}`, { method: "DELETE" });
      loadSessions();
    } catch { /* ignore */ }
  }

  const statusColor = (status: string) => {
    if (status === "running") return ACCENT;
    if (status === "error") return ORANGE;
    if (status === "complete") return "#6b6b7b";
    return TEXT2;
  };

  const StatusIcon = ({ status }: { status: string }) => {
    if (status === "running") return <PlayCircle size={13} style={{ color: ACCENT }} />;
    if (status === "error") return <PauseCircle size={13} style={{ color: ORANGE }} />;
    return <Zap size={13} style={{ color: TEXT2 }} />;
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <Cpu size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Agent Sessions</h1>
        <button
          onClick={loadSessions}
          style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", background: SURFACE, color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {loading ? (
        <p style={{ color: TEXT2, fontSize: 13 }}>Loading sessions…</p>
      ) : sessions.length === 0 ? (
        <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
          <Cpu size={32} style={{ color: BORDER, marginBottom: 12 }} />
          <p style={{ color: TEXT2, fontSize: 14, marginBottom: 4 }}>No active agent sessions.</p>
          <p style={{ color: TEXT2, fontSize: 13 }}>Agent sessions are created when you run multi-step tasks.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {sessions.map((s) => (
            <div key={s.id} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <StatusIcon status={s.status} />
                <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{s.name || s.id}</span>
                <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: statusColor(s.status), fontFamily: "'IBM Plex Mono', monospace" }}>
                  <span style={{ width: 6, height: 6, borderRadius: "50%", background: statusColor(s.status), display: "inline-block" }} />
                  {s.status}
                </span>
                {s.model && <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>{s.model.split("/").pop()}</span>}
                <button onClick={() => deleteSession(s.id)} style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 4, borderRadius: 4, display: "flex", alignItems: "center" }}>
                  <Trash2 size={13} />
                </button>
              </div>
              <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                <span>ID: {s.id}</span>
                <span style={{ display: "flex", alignItems: "center", gap: 4 }}><Clock size={10} /> {new Date(s.updated_at).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info box */}
      <div style={{ marginTop: 24, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: 14 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Agent Sessions</h3>
        <p style={{ margin: 0, fontSize: 13, color: TEXT2, lineHeight: 1.5 }}>
          Agent sessions track multi-step AI tasks. Sessions are created when you run workflows that involve tool calls, browser automation, or multi-agent collaboration. Each session maintains context across multiple turns.
        </p>
      </div>
    </div>
  );
}
