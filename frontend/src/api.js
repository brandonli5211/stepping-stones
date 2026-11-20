const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Optional: VITE_AGENT_ID shows only that agent's calls, VITE_WEEKS limits to the last N weeks.
const AGENT_ID = import.meta.env.VITE_AGENT_ID;
const WEEKS = import.meta.env.VITE_WEEKS;

export async function fetchCalls({ callType, hasMissed, limit = 10 } = {}) {
  const params = new URLSearchParams({ limit });
  if (callType) params.set("call_type", callType);
  if (hasMissed) params.set("has_missed", "true");
  if (AGENT_ID) params.set("agent_id", AGENT_ID);
  if (WEEKS) params.set("weeks", WEEKS);
  const response = await fetch(`${API_URL}/calls?${params}`);
  if (!response.ok) throw new Error(`GET /calls failed (${response.status})`);
  return response.json();
}
