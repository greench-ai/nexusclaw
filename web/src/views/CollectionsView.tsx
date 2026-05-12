import { useEffect, useState } from "react";
import { Database, RefreshCw, Trash2, ChevronDown, ChevronRight, AlertCircle, Layers } from "lucide-react";

interface QdrantCollection {
  name: string;
  vectors_count: number;
  points_count: number;
  status: string;
}

interface CollectionDetail {
  name: string;
  vectors_count: number;
  points_count: number;
  status: string;
  payload_schema: Record<string, any>;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

export default function CollectionsView() {
  const [collections, setCollections] = useState<QdrantCollection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => { loadCollections(); }, []);

  async function loadCollections() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:6333/collections");
      if (!res.ok) throw new Error(`Qdrant returned ${res.status}`);
      const data = await res.json();
      setCollections(data.result?.collections || []);
    } catch (e: any) {
      setError(e.message || "Could not connect to Qdrant at localhost:6333");
      setCollections([]);
    }
    setLoading(false);
  }

  async function loadDetail(name: string) {
    try {
      const res = await fetch(`http://localhost:6333/collections/${name}`);
      if (res.ok) {
        const data = await res.json();
        setExpanded(name);
        // Store in a local map for display — we'll use a separate state
        return data.result;
      }
    } catch { /* ignore */ }
    return null;
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "2rem 1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <Database size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>Collections</h1>
        <span style={{ marginLeft: 8, fontSize: 12, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace", background: SURFACE, padding: "2px 8px", borderRadius: 10, border: `1px solid ${BORDER}` }}>
          Qdrant :6333
        </span>
        <button
          onClick={loadCollections}
          style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", background: SURFACE, color: TEXT2, border: `1px solid ${BORDER}`, borderRadius: 6, fontSize: 12, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {error && (
        <div style={{ background: "rgba(255,107,53,0.08)", border: `1px solid rgba(255,107,53,0.2)", border-radius: 8, padding: 14, marginBottom: 16, display: "flex", gap: 10, alignItems: "flex-start"` }}>
          <AlertCircle size={14} style={{ color: ORANGE, flexShrink: 0, marginTop: 1 }} />
          <div>
            <p style={{ margin: "0 0 4px", fontSize: 13, color: ORANGE, fontWeight: 500 }}>Qdrant not connected</p>
            <p style={{ margin: 0, fontSize: 12, color: TEXT2 }}>{error}</p>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: TEXT2 }}>
              Start Qdrant: <code style={{ background: "rgba(0,255,136,0.08)", padding: "1px 5px", borderRadius: 3, color: ACCENT }}>cd ~/digital-brain && docker-compose up -d qdrant</code>
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <p style={{ color: TEXT2, fontSize: 13 }}>Loading…</p>
      ) : collections.length === 0 && !error ? (
        <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
          <Layers size={32} style={{ color: BORDER, marginBottom: 12 }} />
          <p style={{ color: TEXT2, fontSize: 14, marginBottom: 4 }}>No collections found.</p>
          <p style={{ color: TEXT2, fontSize: 13 }}>Collections are created when you ingest documents into RAG.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {collections.map((col) => (
            <div key={col.name} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, overflow: "hidden" }}>
              <div
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", cursor: "pointer" }}
                onClick={() => setExpanded(expanded === col.name ? null : col.name)}
              >
                {expanded === col.name ? (
                  <ChevronDown size={14} style={{ color: ACCENT, flexShrink: 0 }} />
                ) : (
                  <ChevronRight size={14} style={{ color: TEXT2, flexShrink: 0 }} />
                )}
                <Database size={13} style={{ color: ACCENT, flexShrink: 0 }} />
                <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{col.name}</span>
                <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                  {col.points_count?.toLocaleString() || 0} points
                </span>
                <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                  {col.vectors_count?.toLocaleString() || 0} vectors
                </span>
                <span style={{ fontSize: 10, padding: "2px 7px", borderRadius: 10, background: col.status === "green" ? "rgba(0,255,136,0.1)" : "rgba(255,200,0,0.1)", color: col.status === "green" ? ACCENT : "#ffc800", fontFamily: "'IBM Plex Mono', monospace" }}>
                  {col.status}
                </span>
              </div>
              {expanded === col.name && (
                <div style={{ padding: "0 14px 14px", borderTop: `1px solid ${BORDER}`, marginTop: 0 }}>
                  <div style={{ paddingTop: 12, display: "flex", gap: 16, flexWrap: "wrap" as const }}>
                    {[
                      { label: "Points", value: col.points_count?.toLocaleString() || "0" },
                      { label: "Vectors", value: col.vectors_count?.toLocaleString() || "0" },
                      { label: "Status", value: col.status },
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <span style={{ fontSize: 10, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em", fontFamily: "'IBM Plex Mono', monospace" }}>{label}</span>
                        <p style={{ margin: "2px 0 0", fontSize: 13, color: TEXT, fontFamily: "'IBM Plex Mono', monospace" }}>{value}</p>
                      </div>
                    ))}
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
