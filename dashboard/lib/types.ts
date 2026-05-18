export type Task = {
  id: string;
  name: string;
  client: string;
  board_type: string;
  board_name: string;
  group_name: string;
  status: string;
  priority: string;
  priority_rank: number;
  due_date: string;
  assignees: string[];
  latest_update: string;
  is_done: boolean;
};

export type TasksResponse = {
  window: string;
  count: number;
  total_before_limit: number;
  items: Task[];
};

export type AssigneeBucket = {
  assignee: string;
  total: number;
  done: number;
  overdue: number;
  in_progress: number;
  next_7_days: number;
  by_priority: {
    urgente: number;
    alta: number;
    media: number;
    baixa: number;
    outros: number;
  };
};

export type AssigneeResponse = {
  window: string;
  assignees: AssigneeBucket[];
};

export type ClientStage = {
  client: string;
  current_stage: number;
  current_stage_label: string;
  health: "green" | "yellow" | "red";
  total_overdue: number;
  boards: Record<string, { total: number; done: number; overdue: number; pct_done: number }>;
};

export type StagesResponse = {
  count: number;
  clients: ClientStage[];
};

export type WindowKey =
  | "all"
  | "today"
  | "tomorrow"
  | "overdue"
  | "week"
  | "month"
  | "custom";
