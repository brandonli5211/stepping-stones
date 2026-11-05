import { useEffect, useState } from "react";
import { matchPath } from "./router.jsx";
import { sampleResponses } from "./sampleData.js";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
// VITE_SAMPLE_DATA=true always serves sampleData.js. Otherwise the real API is
// used, and sampleData.js only fills in endpoints the backend doesn't have yet.
const SAMPLE_DATA = import.meta.env.VITE_SAMPLE_DATA === "true";

export async function apiGet(path) {
  if (!SAMPLE_DATA) {
    const response = await fetch(`${API_URL}${path}`).catch(() => null);
    if (response?.ok) return response.json();
  }
  for (const [pattern, build] of Object.entries(sampleResponses)) {
    const params = matchPath(pattern, path);
    if (params) return build(params);
  }
}

/** Loads `path` and returns its data, or null until it arrives. */
export function useApi(path) {
  const [data, setData] = useState(null);
  useEffect(() => {
    setData(null);
    apiGet(path).then(setData);
  }, [path]);
  return data;
}
