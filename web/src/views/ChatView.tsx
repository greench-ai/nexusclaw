import { useEffect, useRef, useState } from "react";
import { ChevronDown, Send, Bot, User, AlertCircle, Settings } from "lucide-react";
import { Link } from "react-router-dom";

interface Provider {
  name: string;
  base_url: string;
  models: string[];
  enabled: boolean;
  api_mode?: string;
  api_key?: string;
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
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";

export default function ChatView() {
  const [config, setConfig] = useState<Config | null>(null);
  const [currentModel, setCurrentModel] = useState(""); // full "provider/model" string
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setCurrentModel(data.default_model || "");
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setModelDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function buildAllModels(cfg: Config) {
    const result: Array<{ label: string; value: string; provider: string }> = [];
    for (const [providerName, prov] of Object.entries(cfg.providers)) {
      if (!prov.enabled) continue;
      for (const model of prov.models) {
        result.push({
          label: model,
          value: `${providerName}/${model}`,
          provider: providerName,
        });
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
      ws.send(JSON.stringify({ message, model: currentModel }));
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

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: BG, fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
      {/* Top bar */}
      <div style={{ flexShrink: 0, height: 52, borderBottom: `1px solid ${BORDER}`, background: BG, display: "flex", alignItems: "center", padding: "0 1.25rem", gap: 12 }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontWeight: 700, fontSize: "0.875rem", color: ACCENT, letterSpacing: "-0.02em" }}>⚡ NexusClaw</span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          {/* Model selector */}
          <div style={{ position: "relative" }} ref={dropdownRef}>
            <button
              style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 10px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", cursor: "pointer", maxWidth: 300 }}
              onClick={() => setModelDropdownOpen((v) => !v)}
            >
              <Bot size={13} style={{ color: ACCENT, flexShrink: 0 }} />
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", maxWidth: 220, textAlign: "left", whiteSpace: "nowrap" }}>{currentModelShort || "Select model"}</span>
              <ChevronDown size={13} style={{ color: TEXT2, flexShrink: 0, transform: modelDropdownOpen ? "rotate(180deg)" : "none", transition: "transform 150ms" }} />
            </button>

            {modelDropdownOpen && (
              <div style={{ position: "absolute", top: "calc(100% + 6px)", right: 0, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, minWidth: 300, maxWidth: 420, maxHeight: 420, overflowY: "auto", zIndex: 200, boxShadow: "0 8px 32px rgba(0,0,0,0.6)" }}>
                {Object.entries(config.providers).map(([providerName, prov]) => {
                  if (!prov.enabled) return null;
                  return (
                    <div key={providerName} style={{ padding: "6px 0", borderBottom: `1px solid ${BORDER}` }}>
                      <div style={{ padding: "4px 12px 2px", fontSize: 10, fontFamily: "'IBM Plex Mono', monospace", color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.08em" }}>{providerName}</div>
                      {prov.models.map((model) => {
                        const fullValue = `${providerName}/${model}`;
                        const isActive = currentModel === fullValue;
                        return (
                          <button
                            key={model}
                            style={{ display: "flex", alignItems: "center", width: "100%", padding: "7px 12px", background: isActive ? "rgba(0,255,136,0.08)" : "transparent", border: "none", color: isActive ? ACCENT : TEXT, fontSize: 13, fontFamily: "'IBM Plex Mono', monospace", cursor: "pointer", textAlign: "left" as const }}
                            onClick={() => { setCurrentModel(fullValue); setModelDropdownOpen(false); }}
                          >
                            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 260 }}>{model}</span>
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

          <Link to="/settings" style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 10px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT2, fontSize: 13, textDecoration: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
            <Settings size={13} /> Settings
          </Link>
        </div>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto" as const, padding: "24px 20px", display: "flex", flexDirection: "column", gap: 16 }}>
        {messages.length === 0 && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", marginTop: 80, textAlign: "center" as const }}>
            <Bot size={32} style={{ color: BORDER, marginBottom: 12 }} />
            <p style={{ color: TEXT, fontSize: 18, fontWeight: 600, marginBottom: 6 }}>NexusClaw</p>
            <p style={{ color: TEXT2, fontSize: 14 }}>Select a model above and send a message.</p>
            <p style={{ color: TEXT2, fontSize: 13, marginTop: 4 }}>{allModels.length} models across {Object.keys(config.providers).length} providers ready.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 8, maxWidth: "72%", padding: "10px 14px", borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px", background: msg.role === "user" ? ACCENT : SURFACE, border: msg.role === "user" ? "none" : `1px solid ${BORDER}`, color: msg.role === "user" ? "#000" : TEXT, fontSize: 14, lineHeight: 1.5, wordBreak: "break-word" as const }}>
              {msg.role === "user" ? <User size={14} style={{ flexShrink: 0, marginTop: 2 }} /> : <Bot size={14} style={{ color: ACCENT, flexShrink: 0, marginTop: 2 }} />}
              <span style={{ whiteSpace: "pre-wrap" as const }}>{msg.content || (msg.role === "assistant" ? "…" : "")}</span>
            </div>
          </div>
        ))}

        {isStreaming && messages[messages.length - 1]?.role !== "assistant" && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 8, padding: "10px 14px", borderRadius: "14px 14px 14px 2px", background: SURFACE, border: `1px solid ${BORDER}`, color: TEXT2, fontSize: 14 }}>
              <Bot size={14} style={{ color: ACCENT, flexShrink: 0, marginTop: 2 }} />
              <span>thinking…</span>
            </div>
          </div>
        )}

        {error && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(255,107,53,0.1)", border: "1px solid rgba(255,107,53,0.25)", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#ff6b35" }}>
            <AlertCircle size={14} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ flexShrink: 0, borderTop: `1px solid ${BORDER}`, padding: "16px 20px", display: "flex", gap: 10, alignItems: "flex-end", background: BG }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={currentModel ? "Type a message…" : "Select a model first…"}
          rows={1}
          disabled={!currentModel || isStreaming}
          style={{ flex: 1, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "10px 14px", color: TEXT, fontSize: 14, resize: "none", outline: "none", maxHeight: 120, overflowY: "auto", lineHeight: 1.5, fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: !currentModel || isStreaming ? 0.5 : 1, cursor: !currentModel || isStreaming ? "not-allowed" : "text" }}
          onInput={(e) => { const t = e.target as HTMLTextAreaElement; t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 120) + "px"; }}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || isStreaming || !currentModel}
          style={{ flexShrink: 0, width: 42, height: 42, border: "none", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", background: input.trim() && !isStreaming && currentModel ? ACCENT : SURFACE, color: input.trim() && !isStreaming && currentModel ? "#000" : TEXT2, cursor: input.trim() && !isStreaming && currentModel ? "pointer" : "not-allowed", transition: "all 0.15s" }}
        >
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
