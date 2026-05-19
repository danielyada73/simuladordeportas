import { apiGet } from "./api";
import type {
  Mission,
  MissionsListResponse,
  MissionsStats,
  MissionSettings,
  UsersListResponse,
} from "./missions-types";

const BASE_URL = process.env.API_BASE_URL || "";
const TOKEN = process.env.API_TOKEN || "";

async function apiSend<T>(path: string, method: string, body?: unknown): Promise<T> {
  if (typeof window !== "undefined") throw new Error("missions-api é server-only");
  if (!BASE_URL) throw new Error("API_BASE_URL nao configurada");
  if (!TOKEN) throw new Error("API_TOKEN nao configurada");

  const url = new URL(path.startsWith("/") ? path.slice(1) : path, BASE_URL.endsWith("/") ? BASE_URL : BASE_URL + "/");
  const res = await fetch(url.toString(), {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

export const missionsApi = {
  list: (params: { window: string; custom_from?: string; custom_to?: string; include_completed?: boolean }) =>
    apiGet<MissionsListResponse>("/api/missions", {
      window: params.window,
      custom_from: params.custom_from,
      custom_to: params.custom_to,
      include_completed: params.include_completed === false ? "false" : "true",
    }),

  stats: (params: { window: string; custom_from?: string; custom_to?: string }) =>
    apiGet<MissionsStats>("/api/missions/stats", {
      window: params.window,
      custom_from: params.custom_from,
      custom_to: params.custom_to,
    }),

  users: () => apiGet<UsersListResponse>("/api/mission-users"),

  settings: () => apiGet<MissionSettings>("/api/mission-settings"),

  create: (payload: Partial<Mission>) => apiSend<Mission>("/api/missions", "POST", payload),
  patch: (id: string, payload: Partial<Mission>) => apiSend<Mission>(`/api/missions/${id}`, "PATCH", payload),
  remove: (id: string) => apiSend<{ deleted: boolean }>(`/api/missions/${id}`, "DELETE"),

  patchSettings: (payload: Partial<MissionSettings>) =>
    apiSend<MissionSettings>("/api/mission-settings", "PATCH", payload),
  upsertUser: (payload: {
    slug: string;
    display_name: string;
    photo_url?: string;
    accent_color?: string;
  }) => apiSend("/api/mission-users", "POST", payload),
  patchUser: (slug: string, payload: Partial<{ display_name: string; photo_url: string; accent_color: string; is_active: boolean; sort_order: number }>) =>
    apiSend(`/api/mission-users/${slug}`, "PATCH", payload),
};
