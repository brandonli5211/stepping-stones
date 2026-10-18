import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const sampleCall = {
  title: "Pay bill",
  agent: "Sample agent",
  rating: "The customer rated this call 10/10.",
  flags: [
    "Never verified the customer's identity",
    "Never read the amount back",
    "Logged $422 when the customer said $122",
  ],
};

export default function App() {
  const [health, setHealth] = useState("checking...");

  useEffect(() => {
    fetch(`${API_URL}/api/health`)
      .then((r) => r.json())
      .then((d) => setHealth(`${d.status} (database: ${d.database})`))
      .catch(() => setHealth("backend unreachable"));
  }, []);

  return (
    <main>
      <p className="eyebrow">Stepping Stones</p>
      <h1>Post-call coaching</h1>
      <article className="call">
        <p className="label">Sample call</p>
        <h2>{sampleCall.title}</h2>
        <p>{sampleCall.agent}</p>
        <p>{sampleCall.rating}</p>
        <ul>
          {sampleCall.flags.map((flag) => (
            <li key={flag}>{flag}</li>
          ))}
        </ul>
      </article>
      <p className="health">Backend health: {health}</p>
    </main>
  );
}
