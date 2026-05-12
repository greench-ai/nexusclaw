import { useEffect, useRef, useState } from "react";
import { ChevronDown, Send, Bot, User, AlertCircle, Settings, Plus, Trash2, MessageSquare, X, PanelLeftClose, PanelLeft } from "lucide-react";
import { Link } from "react-router-dom";

interface Provider {
  name: string;
  base_url: string;
  models: string[];
  enabled: boolean;
}

interface Config {
  version: string;
  default_provider: string;
  default_model: string;
  providers: Record<string, Provider>;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  model?: string;
  created_at?: string;
}

interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

export default function ChatView() {
  const [config, setConfig] = useState<Config | null>(null);
  const [currentModel, setCurrentModel] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [focusMode, setFocusMode] = useState("copilot");
  const [focusDropdownOpen, setFocusDropdownOpen] = useState(false);

  // Conversation state
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Load config
  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setCurrentModel(data.default_model || "");
      })
      .catch(() => {});
    loadConversations();
  }, []);

  // Load conversation messages when activeConvId changes
  useEffect(() => {
    if (activeConvId) {
      fetchMessages(activeConvId);
    } else {
      setMessages([]);
    }
  }, [activeConvId]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function loadConversations() {
    fetch("/api/v1/conversations")
      .then((r) => r.json())
      .then((data) => {
        setConversations(data);
        // Auto-select most recent if none selected
        if (!activeConvId && data.length > 0) {
          setActiveConvId(data[0].id);
        }
      })
      .catch(() => {});
  }

  function fetchMessages(convId: string) {
    fetch(`/api/v1/conversations/${convId}/messages`)
      .then((r) => r.json())
      .then((data) => {
        setMessages(data.map((m: any) => ({ role: m.role, content: m.content, model: m.model })));
      })
      .catch(() => {});
  }

  async function newConversation() {
    try {
      const res = await fetch("/api/v1/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: "New conversation" }) });
      const conv = await res.json();
      setActiveConvId(conv.id);
      setMessages([]);
      loadConversations();
    } catch { /* ignore */ }
  }

  async function deleteConversation(convId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Delete this conversation?")) return;
    try {
      await fetch(`/api/v1/conversations/${convId}`, { method: "DELETE" });
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([]);
        loadConversations();
      } else {
        loadConversations();
      }
    } catch { /* ignore */ }
  }

  function buildAllModels(cfg: Config) {
    const result: Array<{ label: string; value: string; provider: string }> = [];
    for (const [providerName, prov] of Object.entries(cfg.providers)) {
      if (!prov.enabled) continue;
      for (const model of prov.models) {
        result.push({ label: model, value: `${providerName}/${model}`, provider: providerName });
      }
    }
    return result;
  }

  function connectWS(message: string) {
    if (wsRef.current) wsRef.current.close();
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/api/v1/stream/default`);
    wsRef.current = ws;

    setMessages((msgs) => [...msgs, { role: "assistant", content: "" }]);

    ws.onopen = () => {
      ws.send(JSON.stringify({ message, model: currentModel, conversation_id: activeConvId, focus_mode: focusMode }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "token") {
          setMessages((msgs) => {
            const last = msgs[msgs.length - 1];
            if (last?.role === "assistant") {
              return [...msgs.slice(0, -1), { role: "assistant", content: last.content + data.content }];
            }
            return [...msgs, { role: "assistant", content: data.content }];
          });
        } else if (data.type === "error") {
          setError(data.error || "Unknown error");
          setIsStreaming(false);
          setMessages((msgs) => {
            const last = msgs[msgs.length - 1];
            if (last?.role === "assistant" && last.content === "") return msgs.slice(0, -1);
            return msgs;
          });
        } else if (data.type === "done") {
          setIsStreaming(false);
          // Update active conv_id if newly created
          if (data.conversation_id && data.conversation_id !== activeConvId) {
            setActiveConvId(data.conversation_id);
          }
          loadConversations();
        }
      } catch { /* ignore */ }
    };

    ws.onerror = () => {
      setError("Connection error — is NexusClaw running?");
      setIsStreaming(false);
    };

    ws.onclose = () => {
      setIsStreaming(false);
      wsRef.current = null;
    };
  }

  function sendMessage() {
    if (!input.trim() || isStreaming || !currentModel) return;
    const text = input.trim();
    setInput("");
    setError(null);
    setMessages((msgs) => [...msgs, { role: "user", content: text }]);
    setIsStreaming(true);
    connectWS(text);
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  if (!config) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: BG, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace", fontSize: 13 }}>
        Loading...
      </div>
    );
  }

  const allModels = buildAllModels(config);
  const currentModelShort = currentModel.split("/").pop() || currentModel;
  const activeConv = conversations.find((c) => c.id === activeConvId);
  const totalModels = allModels.length;

  return (
    <div style={{ height: "100vh", display: "flex", background: BG, fontFamily: "'Space Grotesk', system-ui, sans-serif", overflow: "hidden" }}>
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <div ref={sidebarRef} style={{
        width: sidebarOpen ? 260 : 0,
        flexShrink: 0,
        borderRight: sidebarOpen ? `1px solid ${BORDER}` : "none",
        background: SURFACE,
        display: "flex",
        flexDirection: "column",
        transition: "width 200ms",
        overflow: "hidden",
      }}>
        <div style={{ padding: "14px 14px 10px", borderBottom: `1px solid ${BORDER}`, display: "flex", alignItems: "center", gap: 8 }}>
          <MessageSquare size={15} style={{ color: ACCENT, flexShrink: 0 }} />
          <span style={{ color: TEXT, fontSize: 13, fontWeight: 600, flex: 1 }}>Chats</span>
          <button
            onClick={newConversation}
            title="New conversation"
            style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: "3px", borderRadius: 4, display: "flex", alignItems: "center" }}
          >
            <Plus size={15} />
          </button>
          <button
            onClick={() => setSidebarOpen(false)}
            title="Close sidebar"
            style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: "3px", borderRadius: 4, display: "flex", alignItems: "center" }}
          >
            <X size={14} />
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto" as const }}>
          {conversations.length === 0 && (
            <div style={{ padding: "24px 16px", textAlign: "center" as const }}>
              <p style={{ color: TEXT2, fontSize: 13, marginBottom: 12 }}>No conversations yet</p>
              <button onClick={newConversation} style={{ background: ACCENT, color: "#000", border: "none", borderRadius: 6, padding: "7px 14px", fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
                New chat
              </button>
            </div>
          )}
          {conversations.map((conv) => {
            const isActive = conv.id === activeConvId;
            const label = conv.title && conv.title !== "New conversation" ? conv.title : conv.id;
            return (
              <div
                key={conv.id}
                onClick={() => { setActiveConvId(conv.id); }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "10px 14px",
                  cursor: "pointer",
                  background: isActive ? "rgba(0,255,136,0.08)" : "transparent",
                  borderLeft: isActive ? `2px solid ${ACCENT}` : "2px solid transparent",
                  transition: "all 150ms",
                }}
              >
                <MessageSquare size={13} style={{ color: isActive ? ACCENT : TEXT2, flexShrink: 0 }} />
                <span style={{ flex: 1, color: isActive ? ACCENT : TEXT, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {label}
                </span>
                <button
                  onClick={(e) => deleteConversation(conv.id, e)}
                  title="Delete"
                  style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: "2px", borderRadius: 3, display: "flex", alignItems: "center", opacity: 0.6 }}
                  onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
                  onMouseLeave={(e) => (e.currentTarget.style.opacity = "0.6")}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            );
          })}
        </div>

        {/* Sidebar footer */}
        <div style={{ padding: "12px 14px", borderTop: `1px solid ${BORDER}` }}>
          <Link to="/settings" style={{ display: "flex", alignItems: "center", gap: 8, color: TEXT2, fontSize: 13, textDecoration: "none", padding: "6px 0" }}>
            <Settings size={13} /> Settings
          </Link>
        </div>
      </div>

      {/* ── Main chat ───────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top bar */}
        <div style={{ flexShrink: 0, height: 52, borderBottom: `1px solid ${BORDER}`, background: BG, display: "flex", alignItems: "center", padding: "0 1rem", gap: 10 }}>
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: "4px", borderRadius: 4, display: "flex", alignItems: "center" }}
            >
              <PanelLeft size={16} />
            </button>
          )}
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontWeight: 700, fontSize: "0.8rem", color: ACCENT }}>⚡ NexusClaw</span>

          {activeConv && (
            <span style={{ color: TEXT2, fontSize: 12, marginLeft: 8, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 200 }}>
              {activeConv.title !== "New conversation" ? activeConv.title : `Chat ${activeConv.id}`}
            </span>
          )}

          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            {/* Model selector */}
            <div style={{ position: "relative" }} ref={dropdownRef}>
              <button
                style={{ display: "flex", alignItems: "center", gap: 7, padding: "5px 10px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 12, fontFamily: "'IBM Plex Mono', monospace", cursor: "pointer", maxWidth: 260 }}
                onClick={() => setModelDropdownOpen((v) => !v)}
              >
                <Bot size={12} style={{ color: ACCENT, flexShrink: 0 }} />
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", maxWidth: 200, whiteSpace: "nowrap" as const, textAlign: "left" as const }}>{currentModelShort || "Select model"}</span>
                <ChevronDown size={11} style={{ color: TEXT2, flexShrink: 0, transform: modelDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 150ms" }} />
              </button>

              {modelDropdownOpen && (
                <div style={{ position: "absolute", top: "calc(100% + 6px)", right: 0, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, minWidth: 280, maxWidth: 380, maxHeight: 420, overflowY: "auto" as const, zIndex: 200, boxShadow: "0 8px 32px rgba(0,0,0,0.6)" }}>
                  {Object.entries(config.providers).map(([providerName, prov]) => {
                    if (!prov.enabled) return null;
                    return (
                      <div key={providerName} style={{ padding: "5px 0", borderBottom: `1px solid ${BORDER}` }}>
                        <div style={{ padding: "3px 12px 2px", fontSize: 10, fontFamily: "'IBM Plex Mono', monospace", color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>{providerName}</div>
                        {prov.models.map((model) => {
                          const fullValue = `${providerName}/${model}`;
                          const isActive = currentModel === fullValue;
                          return (
                            <button
                              key={model}
                              style={{ display: "flex", alignItems: "center", width: "100%", padding: "6px 12px", background: isActive ? "rgba(0,255,136,0.08)" : "transparent", border: "none", color: isActive ? ACCENT : TEXT, fontSize: 12, fontFamily: "'IBM Plex Mono', monospace", cursor: "pointer", textAlign: "left" as const }}
                              onClick={() => { setCurrentModel(fullValue); setModelDropdownOpen(false); }}
                            >
                              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, maxWidth: 240 }}>{model}</span>
                              {isActive && <span style={{ marginLeft: "auto", color: ACCENT, fontSize: 10, flexShrink: 0 }}>✓</span>}
                            </button>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Focus mode picker */}
            <div style={{ position: "relative" }}>
              <button
                style={{ display: "flex", alignItems: "center", gap: 6, padding: "5px 10px", background: focusMode !== "copilot" ? "rgba(0,255,136,0.08)" : SURFACE, border: `1px solid ${focusMode !== "copilot" ? ACCENT : BORDER}`, borderRadius: 6, color: focusMode !== "copilot" ? ACCENT : TEXT, fontSize: 12, fontFamily: "'Space Grotesk', system-ui, sans-serif", cursor: "pointer" }}
                onClick={() => setFocusDropdownOpen((v) => !v)}
              >
                <span style={{ fontSize: 11 }}>⚡</span>
                <span style={{ fontSize: 12 }}>{focusMode === "copilot" ? "Copilot" : focusMode === "academic" ? "Academic" : focusMode === "writing" ? "Writing" : "Custom"}</span>
                <ChevronDown size={10} style={{ color: TEXT2, transform: focusDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 150ms" }} />
              </button>
              {focusDropdownOpen && (
                <div style={{ position: "absolute", top: "calc(100% + 6px)", right: 0, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, minWidth: 160, zIndex: 200, boxShadow: "0 8px 32px rgba(0,0,0,0.6)", padding: "4px 0" }}>
                  {[
                    { key: "copilot", label: "Copilot", desc: "Balanced, k=3" },
                    { key: "academic", label: "Academic", desc: "+30% arxiv boost" },
                    { key: "writing", label: "Writing", desc: "+15% prose boost" },
                    { key: "custom", label: "Custom", desc: "Your prompts" },
                  ].map(({ key, label, desc }) => (
                    <button
                      key={key}
                      style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", width: "100%", padding: "7px 12px", background: focusMode === key ? "rgba(0,255,136,0.08)" : "transparent", border: "none", color: focusMode === key ? ACCENT : TEXT, fontSize: 12, cursor: "pointer", textAlign: "left" as const, gap: 1 }}
                      onClick={() => { setFocusMode(key); setFocusDropdownOpen(false); }}
                    >
                      <span style={{ fontWeight: 600 }}>{label}</span>
                      <span style={{ fontSize: 10, color: TEXT2 }}>{desc}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Link to="/settings" style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 8px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT2, fontSize: 12, textDecoration: "none" }}>
              <Settings size={12} /> Settings
            </Link>
          </div>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto" as const, padding: "20px 16px", display: "flex", flexDirection: "column", gap: 14 }}>
          {messages.length === 0 && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", marginTop: 60, textAlign: "center" as const }}>
              <Bot size={28} style={{ color: BORDER, marginBottom: 10 }} />
              <p style={{ color: TEXT, fontSize: 16, fontWeight: 600, marginBottom: 4 }}>NexusClaw</p>
              <p style={{ color: TEXT2, fontSize: 13 }}>{totalModels} models across {Object.keys(config.providers).length} providers ready.</p>
              <p style={{ color: TEXT2, fontSize: 12, marginTop: 2 }}>{conversations.length} conversation{conversations.length !== 1 ? "s" : ""} saved.</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8, maxWidth: "74%", padding: "9px 13px", borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px", background: msg.role === "user" ? ACCENT : SURFACE, border: msg.role === "user" ? "none" : `1px solid ${BORDER}`, color: msg.role === "user" ? "#000" : TEXT, fontSize: 14, lineHeight: 1.5, wordBreak: "break-word" as const }}>
                {msg.role === "user" ? <User size={13} style={{ flexShrink: 0, marginTop: 2 }} /> : <Bot size={13} style={{ color: ACCENT, flexShrink: 0, marginTop: 2 }} />}
                <span style={{ whiteSpace: "pre-wrap" as const }}>{msg.content || (msg.role === "assistant" ? "…" : "")}</span>
              </div>
            </div>
          ))}

          {isStreaming && messages[messages.length - 1]?.role !== "assistant" && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 13px", borderRadius: "14px 14px 14px 2px", background: SURFACE, border: `1px solid ${BORDER}`, color: TEXT2, fontSize: 14 }}>
                <Bot size={13} style={{ color: ACCENT }} />
                <span>thinking…</span>
              </div>
            </div>
          )}

          {error && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(255,107,53,0.1)", border: "1px solid rgba(255,107,53,0.25)", borderRadius: 8, padding: "9px 13px", fontSize: 13, color: ORANGE }}>
              <AlertCircle size={13} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ flexShrink: 0, borderTop: `1px solid ${BORDER}`, padding: "14px 16px", display: "flex", gap: 10, alignItems: "flex-end", background: BG }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={currentModel ? "Type a message…" : "Select a model first…"}
            rows={1}
            disabled={!currentModel || isStreaming}
            style={{ flex: 1, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "9px 13px", color: TEXT, fontSize: 14, resize: "none", outline: "none", maxHeight: 120, overflowY: "auto" as const, lineHeight: 1.5, fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: !currentModel || isStreaming ? 0.5 : 1, cursor: !currentModel || isStreaming ? "not-allowed" : "text" }}
            onInput={(e) => { const t = e.target as HTMLTextAreaElement; t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 120) + "px"; }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isStreaming || !currentModel}
            style={{ flexShrink: 0, width: 40, height: 40, border: "none", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", background: input.trim() && !isStreaming && currentModel ? ACCENT : SURFACE, color: input.trim() && !isStreaming && currentModel ? "#000" : TEXT2, cursor: input.trim() && !isStreaming && currentModel ? "pointer" : "not-allowed", transition: "all 150ms" }}
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
