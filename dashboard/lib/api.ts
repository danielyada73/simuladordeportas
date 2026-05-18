// Cliente HTTP server-side. NUNCA expor API_TOKEN no browser.
// Em DEMO_MODE, retorna dados ficticios pra previsualizacao visual.

import { demoTasks, demoByAssignee, demoStages } from "./demo-data";

const BASE_URL = process.env.API_BASE_URL || "";
const TOKEN = process.env.API_TOKEN || "";
export const DEMO_MODE = (process.env.DEMO_MODE || "").toLowerCase() === "true";

if (typeof window !== "undefined") {
  throw new Error("lib/api.ts e server-only — nao importe no client");
}

export async function apiGet<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  if (DEMO_MODE) {
    const window = params?.window || "all";
    if (path.includes("by-assignee")) return demoByAssignee(window, params?.custom_from, params?.custom_to) as unknown as T;
    if (path.includes("clients/stages")) return demoStages() as unknown as T;
    if (path.includes("/tasks")) return demoTasks(window, params?.custom_from, params?.custom_to) as unknown as T;
    throw new Error(`Demo endpoint nao mapeado: ${path}`);
  }

  if (!BASE_URL) throw new Error("API_BASE_URL nao configurada");
  if (!TOKEN) throw new Error("API_TOKEN nao configurada");

  const url = new URL(path.startsWith("/") ? path.slice(1) : path, BASE_URL.endsWith("/") ? BASE_URL : BASE_URL + "/");
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${TOKEN}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}
