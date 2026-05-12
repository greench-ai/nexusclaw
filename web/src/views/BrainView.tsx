import { useEffect, useState } from "react";
import { Brain, Search, Plus, Trash2, ArrowLeft, Zap, Database, BookOpen, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

interface BrainStats {
  status: string;
  memory_count: number;
  llm: string;
  embedder: string;
}

interface Memory {
  id: string;
  text: string;
  created_at?: string;
  metadata?: Record<string, any>;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

export default function BrainView() {
  const [stats, setStats] = useState<BrainStats | null>(null);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [newMemory, setNewMemory] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
    loadMemories();
  }, []);

  async function loadStats() {
    try {
      const res = await fetch("/api/v1/brain/stats");
      if (res.ok) setStats(await res.json());
    } catch { /* ignore */ }
  }

  async function loadMemories() {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/brain/memories");
      if (res.ok) {
        const data = await res.json();
        setMemories(data.results || []);
      }
    } catch { /* ignore */ }
    setLoading(false);
  }

  async function doSearch() {
    if (!query.trim()) { setSearchResults(null); return; }
    setSearching(true);
    try {
      const res = await fetch("/api/v1/brain/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 10 }),
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } catch { /* ignore */ }
    setSearching(false);
  }

  async function addMemory() {
    if (!newMemory.trim()) return;
    setAdding(true);
    try {
      const res = await fetch("/api/v1/brain/memories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: newMemory, user_id: "default" }),
      });
      if (res.ok) {
        setNewMemory("");
        loadMemories();
        loadStats();
      }
    } catch { /* ignore */ }
    setAdding(false);
  }

  async function deleteMemory(id: string) {
    if (!confirm("Delete this memory?")) return;
    try {
      await fetch(`/api/v1/brain/memories/${id}`, { method: "DELETE" });
      loadMemories();
      loadStats();
    } catch { /* ignore */ }
  }

  const displayMemories = searchResults !== null ? searchResults : memories;

  return (
    <div style={{ minHeight: "100vh", background: BG, color: TEXT, fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ borderBottom: `1px solid ${BORDER}`, padding: "0 1.5rem", height: 56, display: "flex", alignItems: "center", gap: 12 }}>
        <Link to="/chat" style={{ color: TEXT2, display: "flex", alignItems: "center", textDecoration: "none" }}>
          <ArrowLeft size={16} />
        </Link>
        <Brain size={18} style={{ color: ACCENT }} />
        <span style={{ fontWeight: 600, fontSize: 15 }}>Digital Brain</span>
        {stats && (
          <div style={{ marginLeft: 16, display: "flex", gap: 16 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
              <Database size={11} /> {stats.memory_count} memories
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
              <Zap size={11} /> {stats.llm}
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
              <BookOpen size={11} /> {stats.embedder}
            </span>
          </div>
        )}
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: stats?.status === "connected" ? ACCENT : ORANGE, display: "inline-block" }} />
          <span style={{ fontSize: 12, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
            {stats?.status === "connected" ? "Connected" : "Disconnected"}
          </span>
        </div>
      </div>

      <div style={{ maxWidth: 860, margin: "0 auto", padding: "2rem 1.5rem" }}>
        {/* Search */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", gap: 10 }}>
            <div style={{ flex: 1, position: "relative" }}>
              <Search size={14} style={{ position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)", color: TEXT2 }} />
              <input
                value={query}
                onChange={(e) => { setQuery(e.target.value); if (!e.target.value) setSearchResults(null); }}
                onKeyDown={(e) => e.key === "Enter" && doSearch()}
                placeholder="Search memories…"
                style={{ width: "100%", padding: "10px 14px 10px 36px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 14, outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif", boxSizing: "border-box" }}
              />
            </div>
            <button
              onClick={doSearch}
              disabled={searching || !query.trim()}
              style={{ padding: "10px 18px", background: ACCENT, color: "#000", border: "none", borderRadius: 8, fontSize: 13, cursor: searching ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: searching ? 0.6 : 1 }}
            >
              {searching ? "Searching…" : "Search"}
            </button>
            {searchResults !== null && (
              <button
                onClick={() => { setSearchResults(null); setQuery(""); }}
                style={{ padding: "10px 14px", background: SURFACE, color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 8, fontSize: 13, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Add memory */}
        <div style={{ marginBottom: 24, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 13, color: TEXT2, fontWeight: 500, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Add Memory</h3>
          <textarea
            value={newMemory}
            onChange={(e) => setNewMemory(e.target.value)}
            placeholder="Store a fact, preference, or piece of context…"
            rows={3}
            style={{ width: "100%", background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "9px 12px", color: TEXT, fontSize: 13, resize: "vertical", outline: "none", fontFamily: "'Space Grotesk', system-ui, sans-serif", boxSizing: "border-box", lineHeight: 1.5 }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 10 }}>
            <button
              onClick={addMemory}
              disabled={adding || !newMemory.trim()}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 16px", background: ACCENT, color: "#000", border: "none", borderRadius: 6, fontSize: 13, cursor: adding ? "not-allowed" : "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif", opacity: adding ? 0.6 : 1 }}
            >
              <Plus size={13} /> {adding ? "Adding…" : "Add to Brain"}
            </button>
          </div>
        </div>

        {/* Results */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <h3 style={{ margin: 0, fontSize: 13, color: TEXT2, fontWeight: 500, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>
              {searchResults !== null ? "Search Results" : "All Memories"}
            </h3>
            <span style={{ background: "rgba(0,255,136,0.1)", color: ACCENT, fontSize: 11, padding: "2px 8px", borderRadius: 10, fontFamily: "'IBM Plex Mono', monospace" }}>
              {displayMemories.length}
            </span>
          </div>

          {loading ? (
            <p style={{ color: TEXT2, fontSize: 13 }}>Loading…</p>
          ) : displayMemories.length === 0 ? (
            <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
              <Brain size={32} style={{ color: BORDER, marginBottom: 12 }} />
              <p style={{ color: TEXT2, fontSize: 14 }}>
                {searchResults !== null ? "No results found." : "No memories yet. Add one above!"}
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {displayMemories.map((mem: any) => {
                const score = mem.score !== undefined ? (mem.score * 100).toFixed(0) : null;
                return (
                  <div key={mem.id} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "12px 14px", display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: "0 0 4px", fontSize: 14, lineHeight: 1.5, color: TEXT }}>{mem.text}</p>
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        {mem.created_at && (
                          <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                            {new Date(mem.created_at).toLocaleDateString()}
                          </span>
                        )}
                        {score && (
                          <span style={{ fontSize: 11, color: Number(score) > 80 ? ACCENT : TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                            {score}% match
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteMemory(mem.id)}
                      style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 4, borderRadius: 4, display: "flex", alignItems: "center", flexShrink: 0 }}
                      title="Delete memory"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
