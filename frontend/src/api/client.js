// Every call to the backend goes through this file, so the API address lives in one place.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function getJson(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

export function listCalls() {
  return getJson('/api/conversations');
}

export function getCall(callId) {
  return getJson(`/api/conversations/${encodeURIComponent(callId)}`);
}
