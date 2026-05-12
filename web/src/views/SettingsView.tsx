import { useState, useEffect } from "react";
import { Settings, Key, Check, AlertCircle } from "lucide-react";

interface Provider {
  name: string;
  base_url: string;
  models: string[];
  enabled: boolean;
  has_key?: boolean;
}

interface Config {
  version: string;
  default_provider: string;
  default_model: string;
  providers: Record<string, Provider>;
}

export default function SettingsView() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [defaultModel, setDefaultModel] = useState("");

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.json())
      .then((d) => {
        setConfig(d);
        setDefaultModel(d.default_model || "");
        setLoading(false);
      })
      .catch(() => {
        setError("Failed to load config");
        setLoading(false);
      });
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaveStatus("saving");
    try {
      // Update default model by patching providers
      const providerName = config.default_provider;
      const model = defaultModel.split("/").pop() || defaultModel;
      const res = await fetch("/api/v1/config/provider", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: providerName,
          models: [model],
        }),
      });
      if (res.ok) {
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus("idle"), 2000);
        // Reload config
        const r = await fetch("/api/v1/config").then((r) => r.json());
        setConfig(r);
      } else {
        setSaveStatus("error");
        setTimeout(() => setSaveStatus("idle"), 3000);
      }
    } catch {
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <p style={styles.loading}>Loading config...</p>
      </div>
    );
  }

  if (error || !config) {
    return (
      <div style={styles.container}>
        <p style={styles.error}>{error || "No config"}</p>
      </div>
    );
  }

  const currentProvider = config.providers[config.default_provider];
  const currentModel = config.default_model?.split("/").pop() || "";

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Settings size={20} />
        <h1 style={styles.title}>Settings</h1>
      </div>

      {/* Current Provider */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Current Provider</h2>
        <div style={styles.infoRow}>
          <span style={styles.label}>Provider</span>
          <span style={styles.value}>{config.default_provider}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.label}>Base URL</span>
          <span style={styles.valueMono}>{currentProvider?.base_url || "—"}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.label}>API Mode</span>
          <span style={styles.value}>{currentProvider?.api_mode || "—"}</span>
        </div>
      </div>

      {/* Model Selection */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Model</h2>
        <p style={styles.hint}>Available models for {config.default_provider}:</p>
        <div style={styles.modelList}>
          {currentProvider?.models?.map((m) => (
            <button
              key={m}
              style={{
                ...styles.modelChip,
                ...(m === currentModel || m === currentModel.split("/").pop() ? styles.modelChipActive : {}),
              }}
              onClick={() => setDefaultModel(m)}
            >
              {m}
            </button>
          )) || <span style={styles.hint}>No models configured</span>}
        </div>
        <div style={styles.inputRow}>
          <input
            style={styles.input}
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            placeholder="Or enter model ID..."
          />
        </div>
      </div>

      {/* All Providers */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>All Providers</h2>
        {Object.entries(config.providers).map(([name, prov]) => (
          <div key={name} style={styles.providerCard}>
            <div style={styles.providerHeader}>
              <Key size={14} />
              <strong>{name}</strong>
              {name === config.default_provider && (
                <span style={styles.badge}>active</span>
              )}
            </div>
            <div style={styles.providerModels}>
              {prov.models?.slice(0, 5).join(", ")}
              {prov.models?.length > 5 && ` +${prov.models.length - 5} more`}
            </div>
          </div>
        ))}
      </div>

      {/* Save */}
      <div style={styles.actions}>
        <button
          style={{
            ...styles.saveBtn,
            ...(saveStatus === "saving" ? styles.saveBtnDisabled : {}),
          }}
          onClick={handleSave}
          disabled={saveStatus === "saving"}
        >
          {saveStatus === "saving" ? "Saving..." :
           saveStatus === "saved" ? (
            <><Check size={16} /> Saved!</>
           ) : saveStatus === "error" ? (
            <><AlertCircle size={16} /> Error — retry</>
           ) : (
            "Save Changes"
           )}
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: "720px",
    margin: "0 auto",
    padding: "2rem",
    color: "#f0f0f0",
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
  },
  loading: {
    color: "#6b6b7b",
    textAlign: "center" as const,
    marginTop: "3rem",
  },
  error: {
    color: "#ff6b35",
    textAlign: "center" as const,
    marginTop: "3rem",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "0.75rem",
    marginBottom: "2rem",
    color: "#00ff88",
  },
  title: {
    fontSize: "1.5rem",
    fontWeight: 600,
    margin: 0,
    color: "#f0f0f0",
  },
  section: {
    background: "#111118",
    border: "1px solid #1e1e28",
    borderRadius: "8px",
    padding: "1.25rem",
    marginBottom: "1.5rem",
  },
  sectionTitle: {
    fontSize: "0.875rem",
    fontWeight: 600,
    color: "#6b6b7b",
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    margin: "0 0 1rem 0",
  },
  infoRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "0.5rem 0",
    borderBottom: "1px solid #1e1e28",
  },
  label: {
    color: "#6b6b7b",
    fontSize: "0.875rem",
  },
  value: {
    color: "#f0f0f0",
    fontSize: "0.875rem",
  },
  valueMono: {
    color: "#00ff88",
    fontSize: "0.8rem",
    fontFamily: "'IBM Plex Mono', monospace",
  },
  hint: {
    color: "#6b6b7b",
    fontSize: "0.8rem",
    margin: "0.5rem 0 1rem 0",
  },
  modelList: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "0.5rem",
    marginBottom: "1rem",
  },
  modelChip: {
    padding: "0.35rem 0.75rem",
    borderRadius: "4px",
    border: "1px solid #1e1e28",
    background: "#0a0a0a",
    color: "#6b6b7b",
    fontSize: "0.8rem",
    cursor: "pointer",
    fontFamily: "'IBM Plex Mono', monospace",
  },
  modelChipActive: {
    border: "1px solid #00ff88",
    color: "#00ff88",
    background: "rgba(0,255,136,0.1)",
  },
  inputRow: {
    marginTop: "0.5rem",
  },
  input: {
    width: "100%",
    padding: "0.6rem 0.75rem",
    borderRadius: "6px",
    border: "1px solid #1e1e28",
    background: "#0a0a0a",
    color: "#f0f0f0",
    fontSize: "0.875rem",
    fontFamily: "'IBM Plex Mono', monospace",
    outline: "none",
    boxSizing: "border-box" as const,
  },
  providerCard: {
    padding: "0.75rem",
    borderRadius: "6px",
    background: "#0a0a0a",
    border: "1px solid #1e1e28",
    marginBottom: "0.5rem",
  },
  providerHeader: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    marginBottom: "0.25rem",
    color: "#f0f0f0",
  },
  badge: {
    marginLeft: "auto",
    padding: "0.15rem 0.5rem",
    borderRadius: "3px",
    background: "rgba(0,255,136,0.15)",
    color: "#00ff88",
    fontSize: "0.7rem",
    fontWeight: 600,
  },
  providerModels: {
    color: "#6b6b7b",
    fontSize: "0.75rem",
    fontFamily: "'IBM Plex Mono', monospace",
    paddingLeft: "1.25rem",
  },
  actions: {
    display: "flex",
    justifyContent: "flex-end",
  },
  saveBtn: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    padding: "0.6rem 1.25rem",
    borderRadius: "6px",
    border: "none",
    background: "#00ff88",
    color: "#0a0a0a",
    fontSize: "0.875rem",
    fontWeight: 600,
    cursor: "pointer",
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
  },
  saveBtnDisabled: {
    opacity: 0.6,
    cursor: "not-allowed",
  },
};
