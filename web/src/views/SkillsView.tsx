import { useEffect, useState } from "react";
import { Wrench, Plus, Trash2, Check, X, ArrowUpRight, Link2, BookOpen, Send } from "lucide-react";

interface Skill {
  name: string;
  description: string;
  metadata: Record<string, any>;
  installed: boolean;
  path?: string;
}

interface Proposal {
  id: string;
  skill_name: string;
  description: string;
  trigger: string;
  content: string;
  status: string;
  created_at: string;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

type Tab = "marketplace" | "proposals";

export default function SkillsView() {
  const [tab, setTab] = useState<Tab>("marketplace");
  const [skills, setSkills] = useState<Skill[]>([]);
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInstallForm, setShowInstallForm] = useState(false);
  const [installUrl, setInstallUrl] = useState("");
  const [installing, setInstalling] = useState(false);
  const [installMsg, setInstallMsg] = useState<{ type: "ok" | "err"; msg: string } | null>(null);

  // Proposal form
  const [showProposalForm, setShowProposalForm] = useState(false);
  const [proposalForm, setProposalForm] = useState({ skill_name: "", description: "", trigger: "", content: "" });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { loadSkills(); loadProposals(); }, []);

  async function loadSkills() {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/skills/marketplace");
      if (res.ok) setSkills(await res.json());
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function loadProposals() {
    try {
      const res = await fetch("/api/v1/skills/proposals");
      if (res.ok) setProposals(await res.json());
    } catch { /* ignore */ }
  }

  async function installSkill() {
    if (!installUrl.trim()) return;
    setInstalling(true);
    setInstallMsg(null);
    try {
      const res = await fetch("/api/v1/skills/marketplace/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: installUrl }),
      });
      const data = await res.json();
      if (res.ok) {
        setInstallMsg({ type: "ok", msg: `Installed "${data.name}"` });
        setInstallUrl("");
        setShowInstallForm(false);
        loadSkills();
      } else {
        setInstallMsg({ type: "err", msg: data.detail || "Failed" });
      }
    } catch {
      setInstallMsg({ type: "err", msg: "Network error" });
    }
    setInstalling(false);
  }

  async function uninstallSkill(name: string) {
    if (!confirm(`Remove skill "${name}"?`)) return;
    try {
      await fetch(`/api/v1/skills/marketplace/${name}`, { method: "DELETE" });
      loadSkills();
    } catch { /* ignore */ }
  }

  async function submitProposal() {
    if (!proposalForm.skill_name || !proposalForm.content) return;
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/skills/proposals", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(proposalForm),
      });
      if (res.ok) {
        setProposalForm({ skill_name: "", description: "", trigger: "", content: "" });
        setShowProposalForm(false);
        loadProposals();
      }
    } catch { /* ignore */ }
    setSubmitting(false);
  }

  async function approveProposal(pid: string) {
    try {
      await fetch(`/api/v1/skills/proposals/${pid}/approve`, { method: "POST" });
      loadProposals();
      loadSkills();
    } catch { /* ignore */ }
  }

  async function rejectProposal(pid: string) {
    try {
      await fetch(`/api/v1/skills/proposals/${pid}/reject`, { method: "POST" });
      loadProposals();
    } catch { /* ignore */ }
  }

  const tabStyle = (active: boolean): React.CSSProperties => ({
    padding: "7px 16px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontSize: 13,
    fontFamily: "'Space Grotesk', system-ui, sans-serif",
    background: active ? ACCENT : SURFACE,
    color: active ? "#000" : TEXT2,
    fontWeight: active ? 600 : 400,
    transition: "all 150ms",
  });

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <Wrench size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Skills</h1>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <button style={tabStyle(tab === "marketplace")} onClick={() => setTab("marketplace")}>Marketplace</button>
          <button style={tabStyle(tab === "proposals")} onClick={() => setTab("proposals")}>
            Proposals {proposals.filter((p) => p.status === "proposed").length > 0 && <span style={{ background: "rgba(0,0,0,0.2)", borderRadius: 8, padding: "0 5px", marginLeft: 4, fontSize: 11 }}>{proposals.filter((p) => p.status === "proposed").length}</span>}
          </button>
        </div>
      </div>

      {/* ── Marketplace ── */}
      {tab === "marketplace" && (
        <div>
          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <button
              onClick={() => setShowInstallForm(true)}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 14px", background: ACCENT, color: "#000", border: "none", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
            >
              <Plus size={13} /> Install from URL
            </button>
          </div>

          {showInstallForm && (
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16, marginBottom: 16 }}>
              <h3 style={{ margin: "0 0 12px", fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Install Skill from URL</h3>
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  value={installUrl}
                  onChange={(e) => setInstallUrl(e.target.value)}
                  placeholder="https://example.com/SKILL.md"
                  style={{ flex: 1, padding: "8px 12px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 13, outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
                />
                <button onClick={installSkill} disabled={installing} style={{ padding: "8px 16px", background: ACCENT, color: "#000", border: "none", borderRadius: 6, fontSize: 13, cursor: installing ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: installing ? 0.6 : 1 }}>
                  {installing ? "Installing…" : "Install"}
                </button>
                <button onClick={() => { setShowInstallForm(false); setInstallMsg(null); }} style={{ padding: "8px 12px", background: "transparent", color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
                  <X size={13} />
                </button>
              </div>
              {installMsg && <p style={{ margin: "8px 0 0", fontSize: 13, color: installMsg.type === "ok" ? ACCENT : ORANGE }}>{installMsg.msg}</p>}
            </div>
          )}

          {loading ? (
            <p style={{ color: TEXT2, fontSize: 13 }}>Loading…</p>
          ) : skills.length === 0 ? (
            <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
              <Wrench size={32} style={{ color: BORDER, marginBottom: 12 }} />
              <p style={{ color: TEXT2, fontSize: 14, marginBottom: 4 }}>No skills installed yet.</p>
              <p style={{ color: TEXT2, fontSize: 13 }}>Install skills from URL or create proposals.</p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
              {skills.map((skill) => (
                <div key={skill.name} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 14 }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                    <BookOpen size={15} style={{ color: ACCENT, flexShrink: 0, marginTop: 2 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{skill.name}</div>
                      <p style={{ margin: 0, fontSize: 12, color: TEXT2, lineHeight: 1.4 }}>
                        {skill.description || "No description"}
                      </p>
                    </div>
                    <button
                      onClick={() => uninstallSkill(skill.name)}
                      style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 3, borderRadius: 4, display: "flex", alignItems: "center", flexShrink: 0 }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                  {skill.metadata && Object.keys(skill.metadata).length > 0 && (
                    <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap" as const, gap: 4 }}>
                      {Object.entries(skill.metadata).slice(0, 4).map(([k, v]) => (
                        <span key={k} style={{ fontSize: 10, padding: "2px 6px", background: "rgba(0,255,136,0.06)", color: TEXT2, borderRadius: 4, fontFamily: "'IBM Plex Mono', monospace" }}>
                          {k}: {String(v).slice(0, 20)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Proposals ── */}
      {tab === "proposals" && (
        <div>
          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <button
              onClick={() => setShowProposalForm(true)}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 14px", background: ACCENT, color: "#000", border: "none", borderRadius: 7, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
            >
              <Plus size={13} /> Propose Skill
            </button>
          </div>

          {showProposalForm && (
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16, marginBottom: 16 }}>
              <h3 style={{ margin: "0 0 12px", fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>New Skill Proposal</h3>
              {[
                { key: "skill_name", label: "Skill Name", placeholder: "e.g. github-repos" },
                { key: "description", label: "Description", placeholder: "What does this skill do?" },
                { key: "trigger", label: "Trigger", placeholder: "When should this skill activate?" },
              ].map(({ key, label, placeholder }) => (
                <div key={key} style={{ marginBottom: 10 }}>
                  <label style={{ display: "block", fontSize: 12, color: TEXT2, marginBottom: 4 }}>{label}</label>
                  <input
                    value={proposalForm[key as keyof typeof proposalForm]}
                    onChange={(e) => setProposalForm((f) => ({ ...f, [key]: e.target.value }))}
                    placeholder={placeholder}
                    style={{ width: "100%", padding: "8px 12px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 13, outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif", boxSizing: "border-box" }}
                  />
                </div>
              ))}
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: "block", fontSize: 12, color: TEXT2, marginBottom: 4 }}>SKILL.md Content</label>
                <textarea
                  value={proposalForm.content}
                  onChange={(e) => setProposalForm((f) => ({ ...f, content: e.target.value }))}
                  placeholder="# Skill Name&#10;&#10;## Description&#10;..." rows={6}
                  style={{ width: "100%", padding: "8px 12px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 13, resize: "vertical", outline: "none", fontFamily: "'IBM Plex Mono', monospace", boxSizing: "border-box" }}
                />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={submitProposal}
                  disabled={submitting}
                  style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 16px", background: ACCENT, color: "#000", border: "none", borderRadius: 6, fontSize: 13, cursor: submitting ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: submitting ? 0.6 : 1 }}
                >
                  <Send size={12} /> {submitting ? "Submitting…" : "Submit Proposal"}
                </button>
                <button onClick={() => setShowProposalForm(false)} style={{ padding: "8px 14px", background: "transparent", color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>Cancel</button>
              </div>
            </div>
          )}

          {proposals.length === 0 ? (
            <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
              <Wrench size={32} style={{ color: BORDER, marginBottom: 12 }} />
              <p style={{ color: TEXT2, fontSize: 14 }}>No proposals yet.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {proposals.map((p) => (
                <div key={p.id} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: 14 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{p.skill_name}</span>
                    <span style={{
                      fontSize: 10,
                      padding: "2px 7px",
                      borderRadius: 10,
                      fontFamily: "'IBM Plex Mono', monospace",
                      background: p.status === "approved" ? "rgba(0,255,136,0.1)" : p.status === "rejected" ? "rgba(255,107,53,0.1)" : "rgba(255,200,0,0.1)",
                      color: p.status === "approved" ? ACCENT : p.status === "rejected" ? ORANGE : "#ffc800",
                    }}>
                      {p.status}
                    </span>
                  </div>
                  <p style={{ margin: "0 0 6px", fontSize: 12, color: TEXT2 }}>{p.description}</p>
                  {p.trigger && <p style={{ margin: "0 0 8px", fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>Trigger: {p.trigger}</p>}
                  <div style={{ display: "flex", gap: 8 }}>
                    {p.status === "proposed" && (
                      <>
                        <button onClick={() => approveProposal(p.id)} style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 10px", background: "rgba(0,255,136,0.1)", color: ACCENT, border: "none", borderRadius: 5, fontSize: 12, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
                          <Check size={11} /> Approve
                        </button>
                        <button onClick={() => rejectProposal(p.id)} style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 10px", background: "rgba(255,107,53,0.1)", color: ORANGE, border: "none", borderRadius: 5, fontSize: 12, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
                          <X size={11} /> Reject
                        </button>
                      </>
                    )}
                    <span style={{ marginLeft: "auto", fontSize: 10, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace", alignSelf: "center" }}>
                      {new Date(p.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
