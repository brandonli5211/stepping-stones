import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function App() {
  const [health, setHealth] = useState("checking...");

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((d) => setHealth(`${d.status} (database: ${d.database})`))
      .catch(() => setHealth("backend unreachable"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: 32 }}>
      <h1>Stepping Stones</h1>
      <p>Backend health: {health}</p>
    </main>
  );
}
