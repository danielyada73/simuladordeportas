export type MissionStatus = "nao_iniciada" | "em_progresso" | "concluida";
export type MissionPriority = "alta" | "media" | "baixa";
export type MissionKind = "principal" | "secundaria";

export type Mission = {
  id: string;
  name: string;
  client: string | null;
  responsible_slug: string;
  priority: MissionPriority;
  kind: MissionKind;
  due_date: string;
  status: MissionStatus;
  notes: string | null;
  sort_order: number | null;
  created_by_slug: string | null;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
};

export type MissionUser = {
  slug: string;
  display_name: string;
  photo_url: string | null;
  accent_color: string;
  is_active: boolean;
  sort_order: number;
};

export type MissionSettings = {
  id: string;
  logo_url: string | null;
  client_options: string[];
};

export type ResponsibleStat = {
  slug: string;
  total: number;
  done: number;
  in_progress: number;
  not_started: number;
  alta: number;
  media: number;
  baixa: number;
  principal: number;
  secundaria: number;
};

export type MissionsStats = {
  window: string;
  total: number;
  by_status: Record<MissionStatus, number>;
  by_priority: Record<MissionPriority, number>;
  by_kind: Record<MissionKind, number>;
  by_responsible: ResponsibleStat[];
};

export type MissionsListResponse = { window: string; count: number; items: Mission[] };
export type UsersListResponse = { count: number; items: MissionUser[] };
