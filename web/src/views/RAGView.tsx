import { useEffect, useRef, useState } from "react";
import { FileText, Upload, Search, Trash2, Send, Bot, User, AlertCircle, ChevronDown, X, Plus, File, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

interface Document {
  doc_id: string;
  title: string;
  file_type: string;
  chunk_count: number;
  uploaded_at: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface SearchResult {
  text: string;
  doc_id: string;
  doc_title: string;
  chunk_index: number;
  score: number;
}

const ACCENT = "#00ff88";
const BG = "#0a0a0a";
const SURFACE = "#111118";
const BORDER = "#1e1e28";
const TEXT = "#f0f0f0";
const TEXT2 = "#6b6b7b";
const ORANGE = "#ff6b35";

export default function RAGView() {
  const [tab, setTab] = useState<"upload" | "chat">("upload");
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Chat state
  const [query, setQuery] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [citations, setCitations] = useState<SearchResult[]>([]);
  const [showCitations, setShowCitations] = useState(false);
  const [model, setModel] = useState("MiniMax-M2.7-highspeed");
  const [config, setConfig] = useState<any>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { loadDocs(); loadConfig(); }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  async function loadConfig() {
    try {
      const res = await fetch("/api/v1/config");
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        setModel(data.default_model?.split("/").pop() || data.default_model || "llama3");
      }
    } catch { /* ignore */ }
  }

  async function loadDocs() {
    try {
      const res = await fetch("/api/v1/rag/documents");
      if (res.ok) {
        const data = await res.json();
        setDocs(data.documents || []);
      }
    } catch { /* ignore */ }
  }

  async function uploadDocument() {
    if (!selectedFile) return;
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      const res = await fetch("/api/v1/rag/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        setUploadResult(data);
        setSelectedFile(null);
        loadDocs();
      } else {
        setUploadError(data.detail || "Upload failed");
      }
    } catch (e: any) {
      setUploadError(e.message || "Network error");
    }
    setUploading(false);
  }

  async function deleteDoc(docId: string) {
    if (!confirm("Delete this document?")) return;
    try {
      await fetch(`/api/v1/rag/documents/${docId}`, { method: "DELETE" });
      loadDocs();
    } catch { /* ignore */ }
  }

  async function sendChat() {
    if (!query.trim() || isStreaming) return;
    const text = query.trim();
    setQuery("");
    setChatError(null);
    setChatMessages((m) => [...m, { role: "user", content: text }]);
    setIsStreaming(true);

    // Add placeholder
    setChatMessages((m) => [...m, { role: "assistant", content: "" }]);

    try {
      // First search for context
      const searchRes = await fetch("/api/v1/rag/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text, top_k: 5 }),
      });
      let localCitations: SearchResult[] = [];
      if (searchRes.ok) {
        const searchData = await searchRes.json();
        localCitations = searchData.results || [];
        setCitations(localCitations);
      }

      // Then stream chat
      const modelFull = config?.providers
        ? Object.entries(config.providers).find(([, p]) => p.models?.some((m: string) => m.includes(model.split("/").pop() || model)))?.[0] + "/" + model.split("/").pop()
        : model;

      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${wsProtocol}//${window.location.host}/api/v1/stream/default`);
      ws.onopen = () => {
        ws.send(JSON.stringify({
          message: text,
          model: modelFull || config?.default_model,
          rag: true,
        }));
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "token") {
            setChatMessages((m) => {
              const last = m[m.length - 1];
              return [...m.slice(0, -1), { role: "assistant", content: last.content + data.content }];
            });
          } else if (data.type === "done") {
            ws.close();
          } else if (data.type === "error") {
            setChatError(data.error || "Error");
            setChatMessages((m) => m.filter((x) => x.content !== ""));
            ws.close();
          }
        } catch { /* ignore */ }
      };
      ws.onerror = () => {
        setChatError("Connection error");
        setChatMessages((m) => m.filter((x) => x.content !== ""));
      };
      ws.onclose = () => setIsStreaming(false);

    } catch (e: any) {
      setChatError(e.message || "Failed");
      setIsStreaming(false);
      setChatMessages((m) => m.filter((x) => x.content !== ""));
    }
  }

  const fileTypeLabel = (ft: string) => {
    if (ft.includes("pdf")) return "PDF";
    if (ft.includes("word") || ft.includes("document")) return "DOCX";
    if (ft.includes("markdown")) return "MD";
    return "TXT";
  };

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1.5rem" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
        <FileText size={20} style={{ color: ACCENT }} />
        <h1 style={{ margin: 0, fontSize: "1.2rem", fontWeight: 600 }}>RAG</h1>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <button
            onClick={() => setTab("upload")}
            style={{ padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 13, fontFamily: "'Space Grotesk', system-ui, sans-serif", background: tab === "upload" ? ACCENT : SURFACE, color: tab === "upload" ? "#000" : TEXT2, fontWeight: tab === "upload" ? 600 : 400 }}
          >
            Upload
          </button>
          <button
            onClick={() => setTab("chat")}
            style={{ padding: "7px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 13, fontFamily: "'Space Grotesk', system-ui, sans-serif", background: tab === "chat" ? ACCENT : SURFACE, color: tab === "chat" ? "#000" : TEXT2, fontWeight: tab === "chat" ? 600 : 400 }}
          >
            Chat with Docs
          </button>
        </div>
      </div>

      {/* ── Upload Tab ── */}
      {tab === "upload" && (
        <div>
          {/* Upload area */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 20, marginBottom: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Upload Document</h3>

            {!selectedFile ? (
              <label style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "32px 20px", border: `2px dashed ${BORDER}`, borderRadius: 8, cursor: "pointer", transition: "border-color 150ms" }}>
                <Upload size={24} style={{ color: TEXT2, marginBottom: 10 }} />
                <span style={{ color: TEXT, fontSize: 14, marginBottom: 4 }}>Click to select a file</span>
                <span style={{ color: TEXT2, fontSize: 12 }}>PDF, DOCX, TXT, MD — up to 50MB</span>
                <input type="file" accept=".pdf,.docx,.txt,.md" style={{ display: "none" }} onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setSelectedFile(f);
                }} />
              </label>
            ) : (
              <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", background: BG, border: `1px solid ${BORDER}`, borderRadius: 8, marginBottom: 12 }}>
                <File size={18} style={{ color: ACCENT, flexShrink: 0 }} />
                <div style={{ flex: 1 }}>
                  <span style={{ fontSize: 14, color: TEXT }}>{selectedFile.name}</span>
                  <span style={{ fontSize: 12, color: TEXT2, marginLeft: 8 }}>{(selectedFile.size / 1024).toFixed(1)} KB</span>
                </div>
                <button onClick={() => setSelectedFile(null)} style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 4, display: "flex", alignItems: "center" }}>
                  <X size={14} />
                </button>
              </div>
            )}

            {uploadError && (
              <div style={{ background: "rgba(255,107,53,0.1)", border: "1px solid rgba(255,107,53,0.25)", borderRadius: 6, padding: "9px 13px", fontSize: 13, color: ORANGE, marginBottom: 10, display: "flex", gap: 8, alignItems: "center" }}>
                <AlertCircle size={13} style={{ flexShrink: 0 }} />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadResult && (
              <div style={{ background: "rgba(0,255,136,0.08)", border: "1px solid rgba(0,255,136,0.2)", borderRadius: 6, padding: "9px 13px", fontSize: 13, color: ACCENT, marginBottom: 10, display: "flex", gap: 8, alignItems: "center" }}>
                <CheckCircle size={13} style={{ flexShrink: 0 }} />
                <span>Uploaded "{uploadResult.title}" — {uploadResult.chunks_stored} chunks stored.</span>
              </div>
            )}

            <button
              onClick={uploadDocument}
              disabled={!selectedFile || uploading}
              style={{ display: "flex", alignItems: "center", gap: 6, padding: "9px 18px", background: selectedFile && !uploading ? ACCENT : SURFACE, color: selectedFile && !uploading ? "#000" : TEXT2, border: "none", borderRadius: 7, fontSize: 13, cursor: selectedFile && !uploading ? "pointer" : "not-allowed", fontFamily: "'Space Grotesk', system-ui, sans-serif", marginTop: 10, opacity: uploading ? 0.6 : 1 }}
            >
              <Upload size={13} /> {uploading ? "Processing…" : "Upload & Index"}
            </button>
          </div>

          {/* Documents list */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <h3 style={{ margin: 0, fontSize: 13, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Indexed Documents</h3>
              <span style={{ background: "rgba(0,255,136,0.1)", color: ACCENT, fontSize: 11, padding: "2px 8px", borderRadius: 10, fontFamily: "'IBM Plex Mono', monospace" }}>{docs.length}</span>
            </div>

            {docs.length === 0 ? (
              <div style={{ textAlign: "center" as const, padding: "32px 0", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10 }}>
                <FileText size={28} style={{ color: BORDER, marginBottom: 10 }} />
                <p style={{ color: TEXT2, fontSize: 14, margin: "0 0 4px" }}>No documents indexed yet.</p>
                <p style={{ color: TEXT2, fontSize: 13 }}>Upload a PDF, DOCX, or TXT file above.</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {docs.map((doc) => (
                  <div key={doc.doc_id} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "12px 14px", display: "flex", gap: 12, alignItems: "center" }}>
                    <FileText size={16} style={{ color: ACCENT, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{doc.title}</div>
                      <div style={{ display: "flex", gap: 10, fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>
                        <span>{fileTypeLabel(doc.file_type)}</span>
                        <span>{doc.chunk_count} chunks</span>
                        <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => deleteDoc(doc.doc_id)}
                      style={{ background: "transparent", border: "none", color: TEXT2, cursor: "pointer", padding: 5, borderRadius: 5, display: "flex", alignItems: "center", flexShrink: 0 }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Chat Tab ── */}
      {tab === "chat" && (
        <div style={{ display: "flex", gap: 16 }}>
          {/* Chat area */}
          <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
            {/* Model selector */}
            <div style={{ display: "flex", gap: 8, marginBottom: 14, alignItems: "center" }}>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                style={{ padding: "7px 10px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 6, color: TEXT, fontSize: 12, fontFamily: "'IBM Plex Mono', monospace", outline: "none" }}
              >
                {config && Object.entries(config.providers).map(([provider, prov]: [string, any]) =>
                  prov.models?.map((m: string) => (
                    <option key={`${provider}/${m}`} value={`${provider}/${m}`}>
                      {provider}/{m}
                    </option>
                  ))
                )}
              </select>
              <span style={{ fontSize: 11, color: TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>RAG: ON</span>
              {citations.length > 0 && (
                <button
                  onClick={() => setShowCitations(!showCitations)}
                  style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", background: showCitations ? "rgba(0,255,136,0.12)" : SURFACE, border: `1px solid ${showCitations ? ACCENT : BORDER}`, borderRadius: 5, fontSize: 11, color: showCitations ? ACCENT : TEXT2, cursor: "pointer", fontFamily: "'Space Grotesk', system-ui, sans-serif" }}
                >
                  <FileText size={11} /> {citations.length} citations
                </button>
              )}
            </div>

            {/* Messages */}
            <div style={{ flex: 1, overflowY: "auto" as const, padding: "16px 0", display: "flex", flexDirection: "column", gap: 12, minHeight: 300 }}>
              {chatMessages.length === 0 && (
                <div style={{ textAlign: "center" as const, padding: "40px 0" }}>
                  <Search size={28} style={{ color: BORDER, marginBottom: 10 }} />
                  <p style={{ color: TEXT2, fontSize: 14 }}>Ask questions about your documents.</p>
                  <p style={{ color: TEXT2, fontSize: 12, marginTop: 4 }}>{docs.length} document{docs.length !== 1 ? "s" : ""} indexed.</p>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 8, maxWidth: "78%", padding: "9px 13px", borderRadius: msg.role === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px", background: msg.role === "user" ? ACCENT : SURFACE, border: msg.role === "user" ? "none" : `1px solid ${BORDER}`, color: msg.role === "user" ? "#000" : TEXT, fontSize: 14, lineHeight: 1.5 }}>
                    {msg.role === "user" ? <User size={13} style={{ flexShrink: 0, marginTop: 2 }} /> : <Bot size={13} style={{ color: ACCENT, flexShrink: 0, marginTop: 2 }} />}
                    <span style={{ whiteSpace: "pre-wrap" as const }}>{msg.content}</span>
                  </div>
                </div>
              ))}
              {isStreaming && chatMessages[chatMessages.length - 1]?.role !== "assistant" && (
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 13px", borderRadius: "14px 14px 14px 2px", background: SURFACE, border: `1px solid ${BORDER}`, color: TEXT2, fontSize: 14 }}>
                    <Bot size={13} style={{ color: ACCENT }} />
                    <span>searching…</span>
                  </div>
                </div>
              )}
              {chatError && (
                <div style={{ background: "rgba(255,107,53,0.1)", border: "1px solid rgba(255,107,53,0.25)", borderRadius: 8, padding: "9px 13px", fontSize: 13, color: ORANGE, display: "flex", gap: 8, alignItems: "center" }}>
                  <AlertCircle size={13} style={{ flexShrink: 0 }} />
                  <span>{chatError}</span>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
                placeholder="Ask about your documents…"
                rows={1}
                style={{ flex: 1, padding: "9px 13px", background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 14, resize: "none", outline: "none", maxHeight: 120, fontFamily: "'Space Grotesk', system-ui, sans-serif", lineHeight: 1.5 }}
                onInput={(e) => { const t = e.target as HTMLTextAreaElement; t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 120) + "px"; }}
              />
              <button
                onClick={sendChat}
                disabled={!query.trim() || isStreaming}
                style={{ width: 40, height: 40, border: "none", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", background: query.trim() && !isStreaming ? ACCENT : SURFACE, color: query.trim() && !isStreaming ? "#000" : TEXT2, cursor: query.trim() && !isStreaming ? "pointer" : "not-allowed", flexShrink: 0 }}
              >
                <Send size={15} />
              </button>
            </div>
          </div>

          {/* Citations panel */}
          {showCitations && citations.length > 0 && (
            <div style={{ width: 280, flexShrink: 0, background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 14, maxHeight: 500, overflowY: "auto" as const }}>
              <h4 style={{ margin: "0 0 12px", fontSize: 12, color: TEXT2, textTransform: "uppercase" as const, letterSpacing: "0.06em" }}>Retrieved Context</h4>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {citations.map((c, i) => (
                  <div key={i} style={{ background: BG, border: `1px solid ${BORDER}`, borderRadius: 6, padding: "9px 11px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      <span style={{ fontSize: 10, color: ACCENT, fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600 }}>{c.doc_title}</span>
                      <span style={{ marginLeft: "auto", fontSize: 10, color: Number((c.score * 100).toFixed(0)) > 80 ? ACCENT : TEXT2, fontFamily: "'IBM Plex Mono', monospace" }}>{(c.score * 100).toFixed(0)}%</span>
                    </div>
                    <p style={{ margin: 0, fontSize: 12, color: TEXT, lineHeight: 1.5, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 4, WebkitBoxOrient: "vertical" as const }}>
                      {c.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
