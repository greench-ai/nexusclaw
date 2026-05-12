import { useEffect, useState } from "react";

// ── Provider definitions ───────────────────────────────────────────────────────
const PROVIDERS = [
  {
    id: "ollama",
    label: "Ollama",
    desc: "Free local models — no API key needed",
    icon: "●",
    type: "local" as const,
    base_url: "http://localhost:11434/v1",
    default_model: "llama3",
    models: ["llama3", "llama3.2", "mistral", "codellama", "qwen2.5"],
    hint: "Install from ollama.com first",
  },
  {
    id: "openrouter",
    label: "OpenRouter",
    desc: "100+ models — DeepSeek, Qwen, Gemma, Claude...",
    icon: "◎",
    type: "cloud" as const,
    base_url: "https://openrouter.ai/api/v1",
    key_placeholder: "sk-or-v1-...",
    key_url: "openrouter.ai/keys",
    default_model: "deepseek/deepseek-chat-v3.1",
    models: [
      "deepseek/deepseek-chat-v3.1",
      "qwen/qwen3-8b",
      "qwen/qwen3-32b",
      "google/gemma-3-27b-it",
      "anthropic/claude-3-haiku",
      "nvidia/nemotron-3-super-120b-a12b:free",
    ],
    hint: "Best value: DeepSeek V3.1 — cheapest and most capable",
  },
  {
    id: "deepseek",
    label: "DeepSeek",
    desc: "Fast, cheap, excellent reasoning",
    icon: "◆",
    type: "cloud" as const,
    base_url: "https://api.deepseek.com/v1",
    key_placeholder: "sk-...",
    key_url: "platform.deepseek.com/api_keys",
    default_model: "deepseek-chat",
    models: ["deepseek-chat", "deepseek-coder"],
    hint: "deepseek-chat is the main all-purpose model",
  },
  {
    id: "groq",
    label: "Groq",
    desc: "Blazingly fast — free tier available",
    icon: "▲",
    type: "cloud" as const,
    base_url: "https://api.groq.com/openai/v1",
    key_placeholder: "gsk_...",
    key_url: "console.groq.com/keys",
    default_model: "llama-3.1-70b-versatile",
    models: ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    hint: "Free tier — 14k tokens/min. Llama 3.1 70B is best quality",
  },
  {
    id: "dashscope",
    label: "DashScope",
    desc: "Alibaba Qwen series — powerful Chinese models",
    icon: "◈",
    type: "cloud" as const,
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    key_placeholder: "your Alibaba Access Key",
    key_url: "modelstudio.console.alibabacloud.com → Access Key",
    default_model: "qwen-plus",
    models: ["qwen-plus", "qwen-turbo", "qwen-max"],
    hint: "qwen-plus is the best all-round from DashScope",
  },
];

// ── Component ────────────────────────────────────────────────────────────────
export default function SetupView() {
  const [selected, setSelected] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "done" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const provider = PROVIDERS.find((p) => p.id === selected);

  // Auto-select first provider
  useEffect(() => {
    if (!selected && PROVIDERS.length > 0) {
      setSelected(PROVIDERS[0].id);
      setModel(PROVIDERS[0].default_model);
    }
  }, [selected]);

  function pickProvider(id: string) {
    const p = PROVIDERS.find((pr) => pr.id === id)!;
    setSelected(id);
    setModel(p.default_model);
    setApiKey("");
    setStatus("idle");
    setErrorMsg("");
  }

  async function handleSave() {
    if (!provider || !model.trim()) return;
    setStatus("saving");
    setErrorMsg("");

    try {
      const r = await fetch("/api/v1/config/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: provider.id,
          api_key: provider.type === "cloud" ? apiKey.trim() : null,
          base_url: provider.base_url,
          models: [model.trim()],
          enabled: true,
        }),
      });

      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `Error ${r.status}`);
      }

      setStatus("done");
      setTimeout(() => { window.location.href = "/chat"; }, 1200);
    } catch (e: any) {
      setStatus("error");
      setErrorMsg(e.message || "Something went wrong");
    }
  }

  const canSave = provider && model.trim() && (provider.type === "local" || apiKey.trim());

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <div style={{ width: "100%", maxWidth: 600 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <div style={{ fontSize: 34, fontWeight: 700, color: "var(--green)", marginBottom: 6, fontFamily: "var(--font-mono)" }}>
            ⚡ NexusClaw
          </div>
          <div style={{ color: "var(--text-2)", fontSize: 15 }}>
            Your AI chat platform. Self-hosted. Private.
          </div>
        </div>

        {/* Step 1: Pick provider */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-3)", marginBottom: 12 }}>
            Step 1 — Choose your provider
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => pickProvider(p.id)}
                style={{
                  background: selected === p.id ? "rgba(0,255,136,0.06)" : "var(--surface-1)",
                  border: `1px solid ${selected === p.id ? "var(--green)" : "var(--border)"}`,
                  borderRadius: "var(--radius)",
                  padding: "14px 16px",
                  textAlign: "left",
                  color: "var(--text)",
                  cursor: "pointer",
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-start",
                  transition: "all 0.15s",
                }}
              >
                <span style={{ fontSize: 18, lineHeight: 1, marginTop: 1, flexShrink: 0, color: selected === p.id ? "var(--green)" : "var(--text-3)" }}>{p.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{p.label}</div>
                  <div style={{ fontSize: 12, color: "var(--text-2)", marginTop: 2 }}>{p.desc}</div>
                </div>
                {selected === p.id && (
                  <span style={{ color: "var(--green)", fontSize: 18, lineHeight: 1, flexShrink: 0 }}>✓</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: API Key */}
        {provider && provider.type === "cloud" && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-3)", marginBottom: 12 }}>
              Step 2 — Add your API key
            </div>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={provider.key_placeholder}
              style={{
                width: "100%",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "12px 14px",
                color: "var(--text)",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
                outline: "none",
              }}
            />
            <div style={{ fontSize: 11, color: "var(--text-3)", marginTop: 5 }}>
              Get your key at{" "}
              <span style={{ color: "var(--green)" }}>{provider.key_url}</span>
            </div>
          </div>
        )}

        {/* Step 2b: Pick model */}
        {provider && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-3)", marginBottom: 12 }}>
              {provider.type === "local" ? "Step 2" : "Step 3"} — Pick a model
            </div>

            {/* Model chips */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
              {provider.models.map((m) => (
                <button
                  key={m}
                  onClick={() => setModel(m)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 6,
                    border: `1px solid ${model === m ? "var(--green)" : "var(--border)"}`,
                    background: model === m ? "var(--green-dim)" : "transparent",
                    color: model === m ? "var(--green)" : "var(--text-2)",
                    fontSize: 12,
                    fontFamily: "var(--font-mono)",
                    cursor: "pointer",
                  }}
                >
                  {m}
                </button>
              ))}
            </div>

            {/* Model input */}
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder={provider.default_model}
              style={{
                width: "100%",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "12px 14px",
                color: "var(--text)",
                fontSize: 13,
                fontFamily: "var(--font-mono)",
                outline: "none",
              }}
            />
            {provider.hint && (
              <div style={{ fontSize: 11, color: "var(--text-3)", marginTop: 5 }}>{provider.hint}</div>
            )}
          </div>
        )}

        {/* Error */}
        {status === "error" && (
          <div style={{ background: "rgba(255,68,68,0.1)", border: "1px solid rgba(255,68,68,0.25)", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: 13, color: "#ff6666" }}>
            ✗ {errorMsg}
          </div>
        )}

        {status === "done" && (
          <div style={{ background: "var(--green-dim)", border: "1px solid rgba(0,255,136,0.2)", borderRadius: 8, padding: "10px 14px", marginBottom: 12, fontSize: 13, color: "var(--green)" }}>
            ✓ Saved! Starting chat...
          </div>
        )}

        {/* Save */}
        <button
          onClick={handleSave}
          disabled={!canSave || status === "saving" || status === "done"}
          style={{
            width: "100%",
            background: canSave && status !== "saving" ? "var(--green)" : "var(--surface-2)",
            color: canSave && status !== "saving" ? "#000" : "var(--text-3)",
            border: "none",
            borderRadius: 8,
            padding: "15px",
            fontWeight: 700,
            fontSize: 15,
            cursor: canSave && status !== "saving" ? "pointer" : "not-allowed",
            transition: "all 0.15s",
          }}
        >
          {status === "saving" ? "Saving..." : status === "done" ? "✓ Saved!" : "Save & Start Chatting →"}
        </button>

        {/* Privacy note */}
        <div style={{ fontSize: 11, color: "var(--text-3)", textAlign: "center", marginTop: 12 }}>
          Your key is stored locally in{" "}
          <code style={{ fontFamily: "var(--font-mono)" }}>~/.nexusclaw/config.yaml</code>
        </div>
      </div>
    </div>
  );
}
