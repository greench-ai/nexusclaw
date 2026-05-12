import { useEffect, useState } from "react";
import { MessageSquare, Plus, Trash2, Edit2, X, Check, ChevronDown } from "lucide-react";

interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
  user_prompt_template: string;
  focus_mode: string;
  variables: string[];
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

type Mode = "copilot" | "academic" | "writing" | "custom";

const MODE_LABELS: Record<string, string> = {
  copilot: "Copilot (k=3)",
  academic: "Academic (+arxiv boost)",
  writing: "Writing (+prose boost)",
  custom: "Custom",
};

export default function PromptsView() {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", description: "", system_prompt: "", user_prompt_template: "", focus_mode: "copilot" });
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadTemplates(); }, []);

  async function loadTemplates() {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/prompts");
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function createTemplate() {
    if (!form.name || !form.system_prompt) return;
    setSaving(true);
    try {
      const res = await fetch("/api/v1/prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setShowCreate(false);
        setForm({ name: "", description: "", system_prompt: "", user_prompt_template: "", focus_mode: "copilot" });
        loadTemplates();
      }
    } catch { /* ignore */ }
    setSaving(false);
  }

  async function deleteTemplate(name: string) {
    if (!confirm(`Delete template "${name}"?`)) return;
    try {
      await fetch(`/api/v1/prompts/${name}`, { method: "DELETE" });
      loadTemplates();
    } catch { /* ignore */ }
  }

  async function saveEdit(name: string) {
    setSaving(true);
    try {
      const res = await fetch(`/api/v1/prompts/${name}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setEditing(null);
        setForm({ name: "", description: "", system_prompt: "", user_prompt_template: "", focus_mode: "copilot" });
        loadTemplates();
      }
    } catch { /* ignore */ }
    setSaving(false);
  }

  function startEdit(tpl: PromptTemplate) {
    setEditing(tpl.name);
    setForm({
      name: tpl.name,
      description: tpl.description,
      system_prompt: tpl.system_prompt,
      user_prompt_template: tpl.user_prompt_template,
      focus_mode: tpl.focus_mode,
    });
    setExpanded(null);
  }

  const fieldStyle: React.CSSProperties = {
    width: "100%",
    padding: "8px 11px",
    background: BG,
    border: `1px solid ${BORDER}`,
    borderRadius: 6,
    color: TEXT,
    fontSize: 13,
    outline: "none",
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    boxSizing: "border-box" as const,
    lineHeight: 1.5,
  };

  const monoStyle: React.CSSProperties = {
    ...fieldStyle,
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: 12,
  };

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <MessageSquare size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Prompt Templates</h1>
        <button
          onClick={() => { setShowCreate(true); setEditing(null); setForm({ name: "", description: "", system_prompt: "", user_prompt_template: "", focus_mode: "copilot" }); }}
          style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", background: ACCENT, color: "#000", border: "none", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
        >
          <Plus size={13} /> New Template
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 18, marginBottom: 20 }}>
          <h3 style={{ margin: "0 0 14px", fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>New Prompt Template</h3>
          {[
            { key: "name", label: "Template Name", placeholder: "e.g. code-reviewer", multiline: false },
            { key: "description", label: "Description", placeholder: "What does this template do?", multiline: false },
          ].map(({ key, label, placeholder }) => (
            <div key={key} style={{ marginBottom: 10 }}>
              <label style={{ display: "block", fontSize: 12, color: TEXT2, marginBottom: 4 }}>{label}</label>
              <input
                value={form[key as keyof typeof form]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder}
                style={fieldStyle}
              />
            </div>
          ))}
          <div style={{ marginBottom: 10 }}>
            <label style={{ display: "block", fontSize: 12, color: TEXT2, marginBottom: 4 }}>
              System Prompt <span style={{ color: ORANGE }}>*</span>
              <span style={{ marginLeft: 8, fontSize: 11, color: TEXT2 }}>Use {'{{variable}}'} for placeholders</span>
            </label>
            <textarea
              value={form.system_prompt}
              onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
              placeholder="You are a helpful coding assistant. The user is working on: {{project}}"
              rows={4}
              style={{ ...monoStyle, resize: "vertical" }}
            />
          </div>
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", fontSize: 12, color: TEXT2, marginBottom: 4 }}>
              User Prompt Template <span style={{ fontSize: 11, color: TEXT2 }}>(optional)</span>
            </label>
            <textarea
              value={form.user_prompt_template}
              onChange={(e) => setForm((f) => ({ ...f, user_prompt_template: e.target.value }))}
              placeholder="Review the code in {{file}} for {{issue}}"
              rows={2}
              style={{ ...monoStyle, resize: "vertical" }}
            />
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={createTemplate}
              disabled={saving || !form.name || !form.system_prompt}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 16px", background: ACCENT, color: "#000", border: "none", borderRadius: 7, fontSize: 13, cursor: saving ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: saving ? 0.6 : 1 }}
            >
              <Check size={13} /> {saving ? "Saving…" : "Create Template"}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              style={{ padding: "8px 14px", background: "transparent", color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Templates list */}
      {loading ? (
        <p style={{ color: TEXT2, fontSize: 13 }}>Loading…</p>
      ) : templates.length === 0 && !showCreate ? (
        <div style={{ textAlign: "center" as const, padding: "40px 0", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10 }}>
          <MessageSquare size={28} style={{ color: BORDER, marginBottom: 10 }} />
          <p style={{ color: TEXT2, fontSize: 14, margin: "0 0 4px" }}>No prompt templates yet.</p>
          <p style={{ color: TEXT2, fontSize: 13 }}>Create one to customize how the AI responds.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {templates.map((tpl) => (
            <div key={tpl.name} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, overflow: "hidden" }}>
              {/* Header row */}
              <div
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", cursor: "pointer" }}
                onClick={() => setExpanded(expanded === tpl.name ? null : tpl.name)}
              >
                <ChevronDown size={13} style={{ color: TEXT2, transform: expanded === tpl.name ? "rotate(180deg)" : "none", transition: "transform 150ms", flexShrink: 0 }} />
                <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{tpl.name}</span>
                {tpl.focus_mode && (
                  <span style={{ fontSize: 10, padding: "2px 7px", borderRadius: 10, background: "rgba(0,255,136,0.08)", color: ACCENT, fontFamily: "'IBM Plex Mono', monospace" }}>
                    {MODE_LABELS[tpl.focus_mode] || tpl.focus_mode}
                  </span>
                )}
                {tpl.variables.length > 0 && (
                  <span style={{ fontSize: 10, padding: "2px 7px", borderRadius: 10, background: "rgba(255,255,255,0.05)", color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                    {tpl.variables.map((v) => `{{${v}}}`).join(" ")}
                  </span>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); startEdit(tpl); }}
                  style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 4, display: "flex", alignItems: "center", borderRadius: 4 }}
                  title="Edit"
                >
                  <Edit2 size={13} />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteTemplate(tpl.name); }}
                  style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 4, display: "flex", alignItems: "center", borderRadius: 4 }}
                  title="Delete"
                >
                  <Trash2 size={13} />
                </button>
              </div>

              {/* Expanded detail */}
              {expanded === tpl.name && (
                <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${BORDER}` }}>
                  {tpl.description && (
                    <p style={{ margin: "10px 0 6px", fontSize: 13, color: TEXT2 }}>{tpl.description}</p>
                  )}
                  <div style={{ marginBottom: 8 }}>
                    <span style={{ fontSize: 10, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em", fontFamily: "'IBM Plex Mono', monospace" }}>System Prompt</span>
                    <pre style={{ margin: "4px 0 0", padding: "8px 10px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, fontFamily: "'IBM Plex Mono', monospace", color: TEXT, whiteSpace: "pre-wrap" as const, lineHeight: 1.5, maxHeight: 150, overflowY: "auto" as const }}>
                      {tpl.system_prompt}
                    </pre>
                  </div>
                  {tpl.user_prompt_template && (
                    <div>
                      <span style={{ fontSize: 10, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em", fontFamily: "'IBM Plex Mono', monospace" }}>User Prompt</span>
                      <pre style={{ margin: "4px 0 0", padding: "8px 10px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, fontFamily: "'IBM Plex Mono', monospace", color: ACCENT, whiteSpace: "pre-wrap" as const, lineHeight: 1.5 }}>
                        {tpl.user_prompt_template}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Edit form */}
              {editing === tpl.name && (
                <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${BORDER}` }}>
                  {[
                    { key: "description", label: "Description" },
                  ].map(({ key, label }) => (
                    <div key={key} style={{ marginBottom: 8, marginTop: 10 }}>
                      <label style={{ display: "block", fontSize: 11, color: TEXT2, marginBottom: 3 }}>{label}</label>
                      <input
                        value={form.description}
                        onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                        style={fieldStyle}
                      />
                    </div>
                  ))}
                  <div style={{ marginBottom: 8 }}>
                    <label style={{ display: "block", fontSize: 11, color: TEXT2, marginBottom: 3 }}>System Prompt *</label>
                    <textarea
                      value={form.system_prompt}
                      onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
                      rows={4}
                      style={{ ...monoStyle, resize: "vertical", width: "100%", boxSizing: "border-box" as const }}
                    />
                  </div>
                  <div style={{ marginBottom: 10 }}>
                    <label style={{ display: "block", fontSize: 11, color: TEXT2, marginBottom: 3 }}>User Prompt Template</label>
                    <textarea
                      value={form.user_prompt_template}
                      onChange={(e) => setForm((f) => ({ ...f, user_prompt_template: e.target.value }))}
                      rows={2}
                      style={{ ...monoStyle, resize: "vertical", width: "100%", boxSizing: "border-box" as const }}
                    />
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      onClick={() => saveEdit(tpl.name)}
                      disabled={saving || !form.system_prompt}
                      style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", background: ACCENT, color: "#000", border: "none", borderRadius: 6, fontSize: 12, cursor: saving ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: saving ? 0.6 : 1 }}
                    >
                      <Check size={12} /> {saving ? "Saving…" : "Save"}
                    </button>
                    <button
                      onClick={() => { setEditing(null); setForm({ name: "", description: "", system_prompt: "", user_prompt_template: "", focus_mode: "copilot" }); }}
                      style={{ padding: "7px 12px", background: "transparent", color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
