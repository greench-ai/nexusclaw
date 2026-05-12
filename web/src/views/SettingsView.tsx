import { useState, useEffect } from "react";
import { Settings, Plus, Trash2, Check, AlertCircle, X, ChevronDown } from "lucide-react";

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

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

function maskKey(key: string): string {
  if (!key || key.length < 8) return "••••••••";
  return key.slice(0, 4) + "••••••••" + key.slice(-4);
}

export default function SettingsView() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<{ type: "idle" | "ok" | "error"; msg: string }>({ type: "idle", msg: "" });

  // Add provider form
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({
    name: "",
    base_url: "",
    api_key: "",
    api_mode: "openai-chat",
    models: "",
  });
  const [detecting, setDetecting] = useState(false);

  // Switch default provider
  const [switchDropdown, setSwitchDropdown] = useState(false);
  const switchDropRef = { current: null as HTMLDivElement | null };

  useEffect(() => {
    loadConfig();
  }, []);

  function loadConfig() {
    setLoading(true);
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then((d) => {
        setConfig(d);
        setLoading(false);
      })
      .catch(() => {
        setStatus({ type: "error", msg: "Failed to load config" });
        setLoading(false);
      });
  }

  async function saveAddProvider() {
    if (!addForm.name || !addForm.base_url) return;
    setStatus({ type: "idle", msg: "" });
    try {
      const models = addForm.models
        ? addForm.models.split(",").map((m) => m.trim()).filter(Boolean)
        : [];
      const res = await fetch("/api/v1/config/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: addForm.name,
          base_url: addForm.base_url,
          api_key: addForm.api_key || undefined,
          api_mode: addForm.api_mode,
          models,
          enabled: true,
        }),
      });
      if (res.ok) {
        setStatus({ type: "ok", msg: `Provider "${addForm.name}" added.` });
        setShowAddForm(false);
        setAddForm({ name: "", base_url: "", api_key: "", api_mode: "openai-chat", models: "" });
        loadConfig();
      } else {
        const err = await res.text();
        setStatus({ type: "error", msg: err || "Failed to add provider" });
      }
    } catch {
      setStatus({ type: "error", msg: "Network error" });
    }
  }

  async function deleteProvider(name: string) {
    if (!confirm(`Delete provider "${name}"?`)) return;
    try {
      const res = await fetch(`/api/v1/config/provider/${name}`, { method: "DELETE" });
      if (res.ok) {
        setStatus({ type: "ok", msg: `Provider "${name}" deleted.` });
        loadConfig();
      } else {
        setStatus({ type: "error", msg: "Failed to delete provider" });
      }
    } catch {
      setStatus({ type: "error", msg: "Network error" });
    }
  }

  async function setDefaultProvider(providerName: string) {
    try {
      // Update by patching the provider config with an empty models update to keep it active
      const res = await fetch("/api/v1/config/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: providerName,
          enabled: true,
        }),
      });
      if (res.ok) {
        setStatus({ type: "ok", msg: `Default provider set to "${providerName}".` });
        loadConfig();
      }
    } catch {
      setStatus({ type: "error", msg: "Failed to update default provider" });
    }
    setSwitchDropdown(false);
  }

  async function setDefaultModel(modelId: string) {
    if (!config) return;
    try {
      // Extract model name from "provider/model" or just use raw modelId
      const modelName = modelId.includes("/") ? modelId.split("/").pop()! : modelId;
      const res = await fetch("/api/v1/config/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: config.default_provider,
          models: [modelName],
        }),
      });
      if (res.ok) {
        setStatus({ type: "ok", msg: `Default model set to "${modelName}".` });
        loadConfig();
      }
    } catch {
      setStatus({ type: "error", msg: "Failed to update default model" });
    }
  }

  if (loading) {
    return (
      <div style={s.wrap}>
        <div style={s.center}>
          <span style={{ color: TEXT2, fontFamily: "'IBM Plex Mono', monospace", fontSize: 13 }}>Loading config…</span>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div style={s.wrap}>
        <div style={s.center}>
          <span style={{ color: ORANGE, fontFamily: "'IBM Plex Mono', monospace", fontSize: 13 }}>No config found.</span>
        </div>
      </div>
    );
  }

  const currentProvider = config.providers[config.default_provider];

  return (
    <div style={s.wrap}>
      {/* Header */}
      <div style={s.header}>
        <Settings size={20} style={{ color: ACCENT }} />
        <h1 style={s.title}>Settings</h1>
        {status.type !== "idle" && (
          <div style={{
            ...s.statusBadge,
            ...(status.type === "ok" ? s.statusOk : s.statusErr),
          }}>
            {status.type === "ok" ? <Check size={12} /> : <AlertCircle size={12} />}
            {status.msg}
          </div>
        )}
      </div>

      {/* Default provider / model */}
      <div style={s.section}>
        <div style={s.sectionLabel}>ACTIVE CONFIG</div>
        <div style={s.card}>
          <div style={s.infoRow}>
            <span style={s.label}>Default Provider</span>
            <div style={s.right}>
              <span style={s.value}>{config.default_provider}</span>
              {/* Switch dropdown */}
              <div style={{ position: "relative" as const }}>
                <button style={s.btnSmall} onClick={() => setSwitchDropdown((v) => !v)}>
                  Switch <ChevronDown size={11} />
                </button>
                {switchDropdown && (
                  <div style={s.dropdown}>
                    {Object.entries(config.providers)
                      .filter(([name]) => name !== config.default_provider)
                      .map(([name]) => (
                        <button
                          key={name}
                          style={s.dropdownItem}
                          onClick={() => setDefaultProvider(name)}
                        >
                          {name}
                        </button>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div style={s.infoRow}>
            <span style={s.label}>Default Model</span>
            <span style={{ ...s.value, fontFamily: "'IBM Plex Mono', monospace", color: ACCENT }}>
              {config.default_model?.split("/").pop() || "—"}
            </span>
          </div>
          <div style={s.infoRow}>
            <span style={s.label}>Base URL</span>
            <span style={{ ...s.valueMono }}>{currentProvider?.base_url || "—"}</span>
          </div>
          <div style={{ ...s.infoRow, borderBottom: "none" }}>
            <span style={s.label}>Models ({currentProvider?.models?.length || 0})</span>
            <div style={s.modelList}>
              {currentProvider?.models?.map((m) => (
                <button
                  key={m}
                  style={{
                    ...s.modelChip,
                    ...(m === config.default_model?.split("/").pop() ? s.modelChipActive : {}),
                  }}
                  onClick={() => setDefaultModel(m)}
                >
                  {m}
                </button>
              )) || <span style={s.hint}>No models</span>}
            </div>
          </div>
        </div>
      </div>

      {/* All providers */}
      <div style={s.section}>
        <div style={s.sectionLabel}>ALL PROVIDERS</div>
        {Object.entries(config.providers).map(([name, prov]) => {
          const isDefault = name === config.default_provider;
          return (
            <div key={name} style={{ ...s.card, marginBottom: 10 }}>
              <div style={s.providerHead}>
                <div style={s.providerNameRow}>
                  <span style={s.providerName}>{name}</span>
                  {isDefault && <span style={s.badge}>default</span>}
                  {prov.enabled ? (
                    <span style={{ ...s.badge, background: "rgba(0,255,136,0.08)", color: ACCENT }}>enabled</span>
                  ) : (
                    <span style={{ ...s.badge, background: "rgba(255,107,53,0.1)", color: ORANGE }}>disabled</span>
                  )}
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                  {!isDefault && (
                    <button
                      style={s.btnSmall}
                      onClick={() => setDefaultProvider(name)}
                      title="Set as default"
                    >
                      Set default
                    </button>
                  )}
                  <button
                    style={{ ...s.btnSmall, ...s.btnDanger }}
                    onClick={() => deleteProvider(name)}
                    title="Delete provider"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
              <div style={s.providerDetail}>
                <span style={s.label}>Base URL</span>
                <span style={s.valueMono}>{prov.base_url}</span>
              </div>
              <div style={s.providerDetail}>
                <span style={s.label}>API Mode</span>
                <span style={s.value}>{prov.api_mode === "anthropic-chat" ? "Anthropic" : prov.api_mode === "openai-chat" ? "OpenAI-compatible" : (prov.api_mode || "openai")}</span>
              </div>
              <div style={s.providerDetail}>
                <span style={s.label}>API Key</span>
                <span style={s.valueMono}>{maskKey(prov.api_key || "")}</span>
              </div>
              <div style={{ ...s.providerDetail, borderBottom: "none" }}>
                <span style={s.label}>Models ({prov.models?.length || 0})</span>
                <span style={s.valueMono}>{prov.models?.slice(0, 10).join(", ")}{prov.models?.length > 10 ? ` +${prov.models.length - 10} more` : ""}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add provider */}
      <div style={s.section}>
        <div style={s.sectionLabel}>ADD PROVIDER</div>
        {showAddForm ? (
          <div style={s.addForm}>
            <div style={s.formRow}>
              <label style={s.formLabel}>Provider Name *</label>
              <input
                style={s.input}
                placeholder="e.g. openrouter"
                value={addForm.name}
                onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div style={s.formRow}>
              <label style={s.formLabel}>Base URL *</label>
              <input
                style={s.input}
                placeholder="https://api.example.com/v1"
                value={addForm.base_url}
                onChange={(e) => setAddForm((f) => ({ ...f, base_url: e.target.value }))}
              />
            </div>
            <div style={s.formRow}>
              <label style={s.formLabel}>API Key</label>
              <input
                style={s.input}
                placeholder="sk-..."
                type="password"
                value={addForm.api_key}
                onChange={(e) => setAddForm((f) => ({ ...f, api_key: e.target.value }))}
              />
            </div>
            <div style={s.formRow}>
              <label style={s.formLabel}>API Mode</label>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <select
                  style={{ ...s.select, flex: 1 }}
                  value={addForm.api_mode}
                  onChange={(e) => setAddForm((f) => ({ ...f, api_mode: e.target.value }))}
                >
                  <option value="openai-chat">OpenAI-compatible</option>
                  <option value="anthropic-chat">Anthropic</option>
                </select>
                <button
                  type="button"
                  onClick={async () => {
                    if (!addForm.base_url) return;
                    setDetecting(true);
                    try {
                      const res = await fetch("/api/v1/config/provider/detect", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ base_url: addForm.base_url, api_key: addForm.api_key || undefined }),
                      });
                      if (res.ok) {
                        const data = await res.json();
                        setAddForm((f) => ({ ...f, api_mode: data.api_mode }));
                      }
                    } catch { /* ignore */ }
                    setDetecting(false);
                  }}
                  disabled={detecting || !addForm.base_url}
                  style={{ padding: "7px 12px", background: SURFACE, color: detecting ? TEXT2 : ACCENT, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, cursor: detecting ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", whiteSpace: "nowrap" as const }}
                >
                  {detecting ? "Detecting…" : "Auto-detect"}
                </button>
              </div>
            </div>
            <div style={s.formRow}>
              <label style={s.formLabel}>Models (comma-separated)</label>
              <input
                style={s.input}
                placeholder="model-1, model-2"
                value={addForm.models}
                onChange={(e) => setAddForm((f) => ({ ...f, models: e.target.value }))}
              />
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button style={s.btnPrimary} onClick={saveAddProvider}>
                <Plus size={14} /> Add Provider
              </button>
              <button
                style={s.btnSecondary}
                onClick={() => {
                  setShowAddForm(false);
                  setAddForm({ name: "", base_url: "", api_key: "", api_mode: "openai-chat", models: "" });
                }}
              >
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <button style={s.btnOutline} onClick={() => setShowAddForm(true)}>
            <Plus size={14} /> Add Provider
          </button>
        )}
      </div>

      <div style={{ height: 40 }} />
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  wrap: {
    maxWidth: 760,
    margin: "0 auto",
    padding: "2rem 1.5rem",
    color: TEXT,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
  },
  center: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "60vh",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginBottom: 24,
  },
  title: {
    fontSize: "1.25rem",
    fontWeight: 600,
    color: TEXT,
    margin: 0,
  },
  statusBadge: {
    marginLeft: "auto",
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "4px 10px",
    borderRadius: 4,
    fontSize: 12,
    fontFamily: "'IBM Plex Mono', monospace",
  },
  statusOk: {
    background: "rgba(0,255,136,0.1)",
    color: ACCENT,
    border: "1px solid rgba(0,255,136,0.2)",
  },
  statusErr: {
    background: "rgba(255,107,53,0.1)",
    color: ORANGE,
    border: "1px solid rgba(255,107,53,0.2)",
  },
  section: {
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 10,
    fontFamily: "'IBM Plex Mono', monospace",
    color: TEXT2,
    textTransform: "uppercase" as const,
    letterSpacing: "0.1em",
    marginBottom: 10,
  },
  card: {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    overflow: "hidden",
  },
  infoRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: 16,
    padding: "10px 14px",
    borderBottom: `1px solid ${BORDER}`,
  },
  label: {
    color: TEXT2,
    fontSize: 13,
    minWidth: 120,
    flexShrink: 0,
    paddingTop: 1,
  },
  right: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    marginLeft: "auto",
    flexWrap: "wrap" as const,
    justifyContent: "flex-end",
  },
  value: {
    color: TEXT,
    fontSize: 13,
    fontWeight: 500,
  },
  valueMono: {
    color: ACCENT,
    fontSize: 12,
    fontFamily: "'IBM Plex Mono', monospace",
    wordBreak: "break-all" as const,
  },
  modelList: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: 6,
    marginLeft: "auto",
  },
  hint: {
    color: TEXT2,
    fontSize: 12,
    fontStyle: "italic" as const,
  },
  modelChip: {
    padding: "3px 8px",
    borderRadius: 4,
    border: `1px solid ${BORDER}`,
    background: BG,
    color: TEXT2,
    fontSize: 11,
    fontFamily: "'IBM Plex Mono', monospace",
    cursor: "pointer",
  },
  modelChipActive: {
    border: `1px solid ${ACCENT}`,
    color: ACCENT,
    background: "rgba(0,255,136,0.08)",
  },
  providerHead: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 14px",
    borderBottom: `1px solid ${BORDER}`,
    background: BG,
  },
  providerNameRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  providerName: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontWeight: 600,
    fontSize: 13,
    color: TEXT,
  },
  badge: {
    padding: "2px 7px",
    borderRadius: 3,
    background: "rgba(0,255,136,0.15)",
    color: ACCENT,
    fontSize: 10,
    fontWeight: 600,
    letterSpacing: "0.03em",
  },
  providerDetail: {
    display: "flex",
    alignItems: "flex-start",
    gap: 16,
    padding: "8px 14px",
    borderBottom: `1px solid ${BORDER}`,
  },
  btnSmall: {
    display: "flex",
    alignItems: "center",
    gap: 4,
    padding: "4px 9px",
    borderRadius: 4,
    border: `1px solid ${BORDER}`,
    background: BG,
    color: TEXT2,
    fontSize: 11,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    cursor: "pointer",
  },
  btnDanger: {
    border: "1px solid rgba(255,107,53,0.3)",
    color: ORANGE,
    background: "rgba(255,107,53,0.05)",
  },
  dropdown: {
    position: "absolute" as const,
    top: "calc(100% + 4px)",
    right: 0,
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 6,
    minWidth: 160,
    zIndex: 100,
    boxShadow: "0 4px 16px rgba(0,0,0,0.5)",
  },
  dropdownItem: {
    display: "block",
    width: "100%",
    padding: "7px 12px",
    background: "transparent",
    border: "none",
    color: TEXT,
    fontSize: 13,
    fontFamily: "'IBM Plex Mono', monospace",
    cursor: "pointer",
    textAlign: "left" as const,
  },
  addForm: {
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    padding: 16,
    display: "flex",
    flexDirection: "column" as const,
    gap: 12,
  },
  formRow: {
    display: "flex",
    flexDirection: "column" as const,
    gap: 5,
  },
  formLabel: {
    color: TEXT2,
    fontSize: 12,
    fontWeight: 500,
  },
  input: {
    padding: "8px 10px",
    borderRadius: 6,
    border: `1px solid ${BORDER}`,
    background: BG,
    color: TEXT,
    fontSize: 13,
    fontFamily: "'IBM Plex Mono', monospace",
    outline: "none",
    width: "100%",
    boxSizing: "border-box" as const,
  },
  select: {
    padding: "8px 10px",
    borderRadius: 6,
    border: `1px solid ${BORDER}`,
    background: BG,
    color: TEXT,
    fontSize: 13,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    outline: "none",
    cursor: "pointer",
  },
  btnPrimary: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "8px 14px",
    borderRadius: 6,
    border: "none",
    background: ACCENT,
    color: "#000",
    fontSize: 13,
    fontWeight: 600,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    cursor: "pointer",
  },
  btnSecondary: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "8px 14px",
    borderRadius: 6,
    border: `1px solid ${BORDER}`,
    background: BG,
    color: TEXT2,
    fontSize: 13,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    cursor: "pointer",
  },
  btnOutline: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    padding: "8px 14px",
    borderRadius: 6,
    border: `1px solid ${BORDER}`,
    background: "transparent",
    color: TEXT2,
    fontSize: 13,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    cursor: "pointer",
  },
};
