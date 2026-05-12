import { useEffect, useRef, useState } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Config {
  default_model: string;
  providers: Record<string, { name: string; models: string[]; enabled: boolean }>;
}

export default function ChatView() {
  const [config, setConfig] = useState<Config | null>(null);
  const [currentModel, setCurrentModel] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load config
  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setCurrentModel(data.default_model || "");
      });
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function connectWS(message: string) {
    if (wsRef.current) wsRef.current.close();

    const ws = new WebSocket(`ws://${window.location.host}/api/v1/stream/default`);
    wsRef.current = ws;

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
          setError(data.error);
          setIsStreaming(false);
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
    if (!input.trim() || isStreaming) return;
    const text = input.trim();
    setInput("");
    setError(null);
    setMessages((msgs) => [...msgs, { role: "user", content: text }]);
    setIsStreaming(true);
    connectWS(text);
  }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  // Collect all models from config
  const allModels: string[] = config
    ? Object.values(config.providers).flatMap((p) => p.models)
    : [];

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: "var(--bg)" }}>
      {/* Header */}
      <div style={{
        flexShrink: 0,
        borderBottom: "1px solid var(--border)",
        background: "var(--surface-1)",
        padding: "12px 20px",
        display: "flex",
        alignItems: "center",
        gap: 16,
      }}>
        <span style={{ fontWeight: 700, color: "var(--green)", fontSize: 16, fontFamily: "var(--font-mono)" }}>
          ⚡ NexusClaw
        </span>
        <div style={{ flex: 1 }} />
        {/* Model selector */}
        <select
          value={currentModel}
          onChange={(e) => setCurrentModel(e.target.value)}
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            padding: "6px 10px",
            color: "var(--text)",
            fontSize: 13,
            fontFamily: "var(--font-mono)",
            cursor: "pointer",
          }}
        >
          {allModels.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "var(--text-3)", marginTop: 80, fontSize: 15 }}>
            Send a message to start chatting.
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} style={{
            marginBottom: 16,
            display: "flex",
            flexDirection: "column",
            alignItems: msg.role === "user" ? "flex-end" : "flex-start",
          }}>
            <div style={{
              maxWidth: "72%",
              padding: "10px 14px",
              borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
              background: msg.role === "user" ? "var(--green)" : "var(--surface-1)",
              color: msg.role === "user" ? "#000" : "var(--text)",
              fontSize: 14,
              lineHeight: 1.5,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {isStreaming && messages[messages.length - 1]?.role === "assistant" && (
          <div style={{ marginBottom: 16, display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
            <div style={{
              maxWidth: "72%",
              padding: "10px 14px",
              borderRadius: "14px 14px 14px 2px",
              background: "var(--surface-1)",
              color: "var(--text-3)",
              fontSize: 14,
            }}>
              typing...
            </div>
          </div>
        )}

        {error && (
          <div style={{
            background: "rgba(255,68,68,0.1)",
            border: "1px solid rgba(255,68,68,0.25)",
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 13,
            color: "#ff6666",
            marginBottom: 12,
          }}>
            ✗ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        flexShrink: 0,
        borderTop: "1px solid var(--border)",
        padding: "16px 20px",
        display: "flex",
        gap: 10,
        alignItems: "flex-end",
      }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Type a message..."
          rows={1}
          style={{
            flex: 1,
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: 10,
            padding: "10px 14px",
            color: "var(--text)",
            fontSize: 14,
            resize: "none",
            outline: "none",
            maxHeight: 120,
            overflowY: "auto",
          }}
          onInput={(e) => {
            const t = e.target as HTMLTextAreaElement;
            t.style.height = "auto";
            t.style.height = Math.min(t.scrollHeight, 120) + "px";
          }}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || isStreaming}
          style={{
            flexShrink: 0,
            width: 42,
            height: 42,
            background: input.trim() && !isStreaming ? "var(--green)" : "var(--surface-2)",
            color: input.trim() && !isStreaming ? "#000" : "var(--text-3)",
            border: "none",
            borderRadius: 10,
            cursor: input.trim() && !isStreaming ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            transition: "all 0.15s",
          }}
        >
          ↑
        </button>
      </div>
    </div>
  );
}
