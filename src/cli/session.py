"""
NexusClaw Session Manager
Export, import, and manage chat sessions.
"""
import os, json, asyncio, shutil, zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional
import aiohttp

DEFAULT_DB = Path("~/.nexusclaw/sessions.db").expanduser()

class SessionManager:
    """Manage NexusClaw chat sessions — export, import, list, search."""
    
    def __init__(self, db_path: str = None):
        self.db_path = Path(db_path or DEFAULT_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Init sessions table."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                provider TEXT,
                model TEXT,
                soul_name TEXT,
                tags TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        """)
        conn.commit()
        conn.close()
    
    def list_sessions(self, limit: int = 50) -> list[dict]:
        """List all sessions."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.execute("""
            SELECT id, title, created_at, updated_at, message_count, provider, model, soul_name, tags
            FROM sessions ORDER BY updated_at DESC LIMIT ?
        """, (limit,))
        sessions = [dict(zip([c[0] for c in cur.description], row)) for row in cur.fetchall()]
        conn.close()
        return sessions
    
    def get_session(self, session_id: str) -> dict | None:
        """Get a session with all messages."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        
        sess = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not sess:
            conn.close()
            return None
        
        cols = [c[0] for c in conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).description]
        session = dict(zip(cols, sess))
        
        msgs = conn.execute("SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id", (session_id,)).fetchall()
        session["messages"] = [{"role": m[0], "content": m[1], "timestamp": m[2]} for m in msgs]
        conn.close()
        return session
    
    def create_session(self, session_id: str, title: str = "", provider: str = "ollama", model: str = "llama3.2") -> dict:
        """Create a new session."""
        import sqlite3
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO sessions (id, title, created_at, updated_at, provider, model, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, title or f"Session {now[:16]}", now, now, provider, model, ""))
        conn.commit()
        conn.close()
        return {"id": session_id, "title": title, "created_at": now}
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to a session."""
        import sqlite3
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, now))
        conn.execute("UPDATE sessions SET updated_at = ?, message_count = message_count + 1 WHERE id = ?", (now, session_id))
        conn.commit()
        conn.close()
    
    def export_session(self, session_id: str, output_path: str = None) -> str:
        """Export a session to JSON file."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        path = output_path or f"session_{session_id[:8]}_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(path, "w") as f:
            json.dump(session, f, indent=2)
        return path
    
    def export_all(self, output_dir: str = "~/NexusClaw/exports") -> str:
        """Export all sessions to a zip file."""
        output_dir = Path(output_dir).expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = output_dir / f"sessions_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.zip"
        
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for sess in self.list_sessions(limit=1000):
                sess_data = self.get_session(sess["id"])
                zf.writestr(f"sessions/{sess['id']}.json", json.dumps(sess_data, indent=2))
        
        return str(zip_path)
    
    def import_session(self, json_path: str) -> dict:
        """Import a session from JSON file."""
        import sqlite3
        with open(json_path) as f:
            session = json.load(f)
        
        conn = sqlite3.connect(str(self.db_path))
        
        # Insert session
        conn.execute("""
            INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at, message_count, provider, model, soul_name, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["id"],
            session.get("title", ""),
            session.get("created_at", datetime.utcnow().isoformat()),
            session.get("updated_at", datetime.utcnow().isoformat()),
            len(session.get("messages", [])),
            session.get("provider", ""),
            session.get("model", ""),
            session.get("soul_name", ""),
            session.get("tags", "")
        ))
        
        # Insert messages
        for msg in session.get("messages", []):
            conn.execute("""
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session["id"], msg["role"], msg["content"], msg.get("timestamp", datetime.utcnow().isoformat())))
        
        conn.commit()
        conn.close()
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        import sqlite3
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        return True

# CLI helpers
def cli_list():
    sm = SessionManager()
    sessions = sm.list_sessions()
    if not sessions:
        print("No sessions found.")
        return
    print(f"\n{'Title':<30} {'Updated':<20} {'Messages':<8} {'Provider':<10} {'ID':<8}")
    print("-" * 80)
    for s in sessions:
        print(f"{s['title'][:29]:<30} {s['updated_at'][:19]:<20} {s['message_count']:<8} {s.get('provider',''):<10} {s['id'][:8]}")

def cli_export(session_id: str, output: str = None):
    sm = SessionManager()
    path = sm.export_session(session_id, output)
    print(f"Exported to: {path}")

def cli_export_all(output_dir: str = None):
    sm = SessionManager()
    path = sm.export_all(output_dir)
    print(f"Exported all to: {path}")

def cli_import(json_path: str):
    sm = SessionManager()
    session = sm.import_session(json_path)
    print(f"Imported: {session['id']} ({len(session.get('messages', []))} messages)")

def cli_delete(session_id: str):
    sm = SessionManager()
    sm.delete_session(session_id)
    print(f"Deleted: {session_id}")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        cli_list()
    elif cmd == "export" and len(sys.argv) > 2:
        cli_export(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "export-all":
        cli_export_all(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "import" and len(sys.argv) > 2:
        cli_import(sys.argv[2])
    elif cmd == "delete" and len(sys.argv) > 2:
        cli_delete(sys.argv[2])
    else:
        print("Usage: session.py [list|export|export-all|import|delete] [args]")
