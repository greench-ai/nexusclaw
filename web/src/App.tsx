import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import SetupView from "./views/SetupView";
import ChatView from "./views/ChatView";

function App() {
  const [hasConfig, setHasConfig] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/v1/config")
      .then((r) => r.ok)
      .then((ok) => setHasConfig(ok))
      .catch(() => setHasConfig(false));
  }, []);

  if (hasConfig === null) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "var(--text-3)", fontFamily: "var(--font-mono)" }}>
        Loading...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={hasConfig ? <Navigate to="/chat" replace /> : <Navigate to="/setup" replace />}
        />
        <Route path="/setup" element={<SetupView />} />
        <Route path="/chat" element={<ChatView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
