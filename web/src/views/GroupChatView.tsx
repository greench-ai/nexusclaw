import { useEffect, useState, useRef } from "react";
import { Users, Play, Trash2, Plus, Send, User } from "lucide-react";

interface Agent { id: string; name: string; description: string; color: string }
interface ChatMessage { agent: string; content: string; timestamp: string }

const AGENTS: Agent[] = [
  { id: "researcher", name: "Researcher", description: "Deep research and information synthesis", color: "#00ff88" },
  { id: "coder", name: "Coder", description: "Write, review, and debug code", color: "#3b82f6" },
  { id: "writer", name: "Writer", description: "Clear, engaging content creation", color: "#a855f7" },
  { id: "critic", name: "Critic", description: "Challenge assumptions, find flaws", color: "#ff6b35" },
  { id: "analyst", name: "Analyst", description: "Data analysis and pattern detection", color: "#ffc800" },
];

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";

export default function GroupChatView() {
  const [selectedAgents, setSelectedAgents] = useState<string[]>(["researcher", "coder"]);
  const [teamType, setTeamType] = useState<"round_robin" | "selector">("round_robin");
  const [task, setTask] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [running, setRunning] = useState(false);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadSessions(); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSessions() {
    setLoadingSessions(true);
    try {
      const res = await fetch("/api/v1/group-chat/sessions");
      if (res.ok) setSessions(await res.json());
    } catch { setSessions([]); }
    setLoadingSessions(false);
  }

  async function runGroupChat() {
    if (!task.trim() || selectedAgents.length === 0) return;
    setRunning(true);
    setMessages([]);
    const prompt = `You are part of a group chat with these agents: ${selectedAgents.join(", ")}.\nYour task: ${task}\n\nRespond as your role.`;
    try {
      const res = await fetch("/api/v1/group-chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_ids: selectedAgents, team_type: teamType, message: prompt }),
      });
      if (res.ok) {
        const session = await res.json();
        // Poll for results
        for (let i = 0; i < 20; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const hist = await fetch(`/api/v1/group-chat/sessions/${session.id}`);
          if (hist.ok) {
            const h = await hist.json();
            if (h.messages) {
              setMessages(h.messages.map((m: any) => ({ agent: m.agent, content: m.content, timestamp: m.timestamp })));
            }
            if (h.status === "complete" || h.status === "error") break;
          }
        }
      }
    } catch { /* ignore */ }
    setRunning(false);
    loadSessions();
  }

  function toggleAgent(id: string) {
    setSelectedAgents((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  }

  const agentColor = (id: string) => AGENTS.find((a) => a.id === id)?.color || TEXT2;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <Users size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Group Chat</h1>
      </div>

      {/* Agent picker */}
      <div style={{ marginBottom: 20, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16 }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 12, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Select Agents</h3>
        <div style={{ display: "flex", flexWrap: "wrap" as const, gap: 8, marginBottom: 14 }}>
          {AGENTS.map((agent) => {
            const active = selectedAgents.includes(agent.id);
            return (
              <button
                key={agent.id}
                onClick={() => toggleAgent(agent.id)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: `1px solid ${active ? agent.color : BORDER}`,
                  background: active ? `${agent.color}18` : "transparent",
                  color: active ? agent.color : TEXT2,
                  fontSize: 12,
                  cursor: "pointer",
                  fontFamily: "'Space Grotesk', system-ui, sans-serif",
                  transition: "all 150ms",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: agent.color, display: "inline-block" }} />
                {agent.name}
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select
            value={teamType}
            onChange={(e) => setTeamType(e.target.value as any)}
            style={{ padding: "7px 10px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 12, fontFamily: "'Space Grotesk', system-ui, sans-serif", outline: "none" }}
          >
            <option value="round_robin">Round Robin (fixed turns)</option>
            <option value="selector">Selector (best agent next)</option>
          </select>
          <div style={{ flex: 1 }}>
            <input
              value={task}
              onChange={(e) => setTask(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runGroupChat()}
              placeholder="Describe the task for the group…"
              style={{ width: "100%", padding: "7px 12px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 13, outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif", boxSizing: "border-box" }}
            />
          </div>
          <button
            onClick={runGroupChat}
            disabled={running || !task.trim() || selectedAgents.length === 0}
            style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 16px", background: running ? SURFACE : ACCENT, color: running ? TEXT2 : "#000", border: "none", borderRadius: 6, fontSize: 13, cursor: running ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: running ? 0.6 : 1, flexShrink: 0 }}
          >
            <Play size={13} /> {running ? "Running…" : "Run"}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 12, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Messages</h3>
        {messages.length === 0 && (
          <div style={{ textAlign: "center" as const, padding: "24px 0", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8 }}>
            <Users size={24} style={{ color: BORDER, marginBottom: 8 }} />
            <p style={{ color: TEXT2, fontSize: 13, margin: 0 }}>No messages yet. Run a group chat to see results here.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", gap: 10, marginBottom: 10, alignItems: "flex-start" }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: agentColor(msg.agent), display: "inline-block", flexShrink: 0, marginTop: 4 }} />
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: 11, color: agentColor(msg.agent), fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600 }}>{msg.agent}</span>
              <p style={{ margin: "2px 0 0", fontSize: 13, color: TEXT, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "8px 12px", lineHeight: 1.5 }}>{msg.content}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Sessions list */}
      <div>
        <h3 style={{ margin: "0 0 12px", fontSize: 12, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Past Sessions</h3>
        {loadingSessions ? (
          <p style={{ color: TEXT2, fontSize: 13 }}>Loading…</p>
        ) : sessions.length === 0 ? (
          <p style={{ color: TEXT2, fontSize: 13 }}>No past sessions.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {sessions.map((s) => (
              <div key={s.id} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "10px 12px", display: "flex", alignItems: "center", gap: 10 }}>
                <Users size={12} style={{ color: TEXT2 }} />
                <span style={{ flex: 1, fontSize: 13, color: TEXT }}>{s.id}</span>
                <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>{s.status}</span>
                <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>{new Date(s.created_at).toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
