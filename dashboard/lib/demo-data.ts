import type { TasksResponse, AssigneeResponse, StagesResponse, Task } from "./types";

const today = () => new Date().toISOString().slice(0, 10);
const offset = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
};

const TASKS: Task[] = [
  { id: "1001", name: "Subir novos criativos vídeo Meta", client: "Impera Imóveis", board_type: "otimizacoes", board_name: "Impera Imóveis- 4. OTIMIZAÇÕES", group_name: "Meta - Maio", status: "Em progresso", priority: "Urgente", priority_rank: 1, due_date: today(), assignees: ["Daniel"], latest_update: "Cliente aprovou roteiros ontem 18h. Gravando hoje.", is_done: false },
  { id: "1002", name: "Recarga de saldo Google Ads", client: "JPA Construções", board_type: "saldo", board_name: "JPA Construções- 5. SALDO", group_name: "Meta - Maio", status: "", priority: "Urgente", priority_rank: 1, due_date: today(), assignees: ["Jefferson"], latest_update: "Saldo: R$ 12,50. Diário: R$ 80. Vai pausar em horas.", is_done: false },
  { id: "1003", name: "Pixel + API conversão LP", client: "Casa do Churras", board_type: "campanhas", board_name: "Casa do Churras- 3. CAMPANHAS", group_name: "Google, Tags e Conversões", status: "Em progresso", priority: "Alta", priority_rank: 2, due_date: today(), assignees: ["Jefferson"], latest_update: "GTM publicado. Falta validar evento purchase.", is_done: false },
  { id: "1004", name: "Aprovar copy LP com cliente", client: "Casa do Churras", board_type: "lp", board_name: "Casa do Churras- 2. CRIAÇÃO DE LP", group_name: "CRIAÇÃO DE LP", status: "", priority: "Alta", priority_rank: 2, due_date: offset(1), assignees: ["Daniel"], latest_update: "Enviado WhatsApp 16:30. Aguardando retorno.", is_done: false },
  { id: "1005", name: "Reunião briefing cliente novo", client: "Studio Verde", board_type: "briefing", board_name: "Studio Verde- 1. BRIEFING", group_name: "BRIEFING", status: "", priority: "Alta", priority_rank: 2, due_date: offset(1), assignees: ["Daniel", "Gustavo"], latest_update: "", is_done: false },
  { id: "1006", name: "Otimização Semana 3", client: "Impera Imóveis", board_type: "otimizacoes", board_name: "Impera Imóveis- 4. OTIMIZAÇÕES", group_name: "Google - Maio", status: "Em progresso", priority: "Média", priority_rank: 3, due_date: offset(-1), assignees: ["Jefferson"], latest_update: "CPL subiu 23%. Trocar palavras-chave de cauda longa.", is_done: false },
  { id: "1007", name: "Configurar BM + Pixel", client: "Studio Verde", board_type: "campanhas", board_name: "Studio Verde- 3. CAMPANHAS", group_name: "Meta", status: "", priority: "Média", priority_rank: 3, due_date: offset(2), assignees: ["Jefferson"], latest_update: "", is_done: false },
  { id: "1008", name: "Layout novo bloco prova social LP", client: "JPA Construções", board_type: "lp", board_name: "JPA Construções- 2. CRIAÇÃO DE LP", group_name: "CRIAÇÃO DE LP", status: "Em progresso", priority: "Média", priority_rank: 3, due_date: offset(3), assignees: ["Daniel"], latest_update: "Layout v2 enviado. Cliente pediu fonte maior.", is_done: false },
  { id: "1009", name: "Verificar conversões GA4", client: "Pizzaria Donato", board_type: "campanhas", board_name: "Pizzaria Donato- 3. CAMPANHAS", group_name: "Google, Tags e Conversões", status: "Feito", priority: "Baixa", priority_rank: 4, due_date: offset(-2), assignees: ["Jefferson"], latest_update: "Eventos disparando ok no Tag Assistant.", is_done: true },
  { id: "1010", name: "Atualizar foto perfil Instagram", client: "Pizzaria Donato", board_type: "otimizacoes", board_name: "Pizzaria Donato- 4. OTIMIZAÇÕES", group_name: "Meta - Maio", status: "", priority: "Baixa", priority_rank: 4, due_date: offset(5), assignees: ["Gustavo"], latest_update: "", is_done: false },
  { id: "1011", name: "Renovar domínio anual", client: "Casa do Churras", board_type: "lp", board_name: "Casa do Churras- 2. CRIAÇÃO DE LP", group_name: "CRIAÇÃO DE LP", status: "", priority: "Baixa", priority_rank: 4, due_date: offset(10), assignees: ["Daniel"], latest_update: "", is_done: false },
  { id: "1012", name: "Recarga Meta - Maio Semana 4", client: "JPA Construções", board_type: "saldo", board_name: "JPA Construções- 5. SALDO", group_name: "Meta - Maio", status: "", priority: "Média", priority_rank: 3, due_date: offset(2), assignees: ["Jefferson"], latest_update: "", is_done: false },
];

function filterTasks(window: string, customFrom?: string, customTo?: string, includeDone = false): Task[] {
  const todayStr = today();
  const within = (due: string, start: string, end: string) => due >= start && due <= end;

  let filtered = TASKS;
  if (window === "today") filtered = TASKS.filter((t) => t.due_date === todayStr);
  else if (window === "tomorrow") filtered = TASKS.filter((t) => t.due_date === offset(1));
  else if (window === "overdue") filtered = TASKS.filter((t) => t.due_date && t.due_date < todayStr && !t.is_done);
  else if (window === "week") filtered = TASKS.filter((t) => within(t.due_date, todayStr, offset(7)));
  else if (window === "month") filtered = TASKS.filter((t) => within(t.due_date, todayStr, offset(30)));
  else if (window === "custom" && customFrom && customTo) filtered = TASKS.filter((t) => within(t.due_date, customFrom, customTo));

  if (!includeDone) filtered = filtered.filter((t) => !t.is_done);
  filtered = [...filtered].sort((a, b) => a.priority_rank - b.priority_rank || a.due_date.localeCompare(b.due_date));
  return filtered;
}

export function demoTasks(window: string, customFrom?: string, customTo?: string): TasksResponse {
  const items = filterTasks(window, customFrom, customTo, false);
  return { window, count: items.length, total_before_limit: items.length, items };
}

export function demoByAssignee(window: string, customFrom?: string, customTo?: string): AssigneeResponse {
  const items = filterTasks(window, customFrom, customTo, true);
  const todayStr = today();
  const buckets = new Map<string, ReturnType<typeof emptyBucket>>();

  for (const t of items) {
    for (const name of t.assignees) {
      if (!buckets.has(name)) buckets.set(name, emptyBucket(name));
      const b = buckets.get(name)!;
      b.total++;
      if (t.is_done) b.done++;
      const isOverdue = t.due_date && t.due_date < todayStr && !t.is_done;
      if (isOverdue) b.overdue++;
      else if (!t.is_done) b.in_progress++;
      if (t.due_date >= todayStr && t.due_date <= offset(7) && !t.is_done) b.next_7_days++;
      const p = t.priority.toLowerCase();
      if (p === "urgente" || p === "crítico" || p === "critico") b.by_priority.urgente++;
      else if (p === "alta") b.by_priority.alta++;
      else if (p === "média" || p === "media") b.by_priority.media++;
      else if (p === "baixa") b.by_priority.baixa++;
      else b.by_priority.outros++;
    }
  }
  return { window, assignees: Array.from(buckets.values()).sort((a, b) => b.overdue - a.overdue || b.in_progress - a.in_progress) };
}

function emptyBucket(name: string) {
  return {
    assignee: name,
    total: 0, done: 0, overdue: 0, in_progress: 0, next_7_days: 0,
    by_priority: { urgente: 0, alta: 0, media: 0, baixa: 0, outros: 0 },
  };
}

export function demoStages(): StagesResponse {
  return {
    count: 4,
    clients: [
      { client: "JPA Construções", current_stage: 6, current_stage_label: "Otimização + Saldo (loop semanal)", health: "red", total_overdue: 2,
        boards: { briefing: { total: 5, done: 5, overdue: 0, pct_done: 100 }, lp: { total: 5, done: 5, overdue: 0, pct_done: 100 }, campanhas: { total: 10, done: 10, overdue: 0, pct_done: 100 }, otimizacoes: { total: 8, done: 6, overdue: 1, pct_done: 75 }, saldo: { total: 6, done: 5, overdue: 1, pct_done: 83 } } },
      { client: "Impera Imóveis", current_stage: 6, current_stage_label: "Otimização + Saldo (loop semanal)", health: "red", total_overdue: 1,
        boards: { briefing: { total: 5, done: 5, overdue: 0, pct_done: 100 }, lp: { total: 5, done: 5, overdue: 0, pct_done: 100 }, campanhas: { total: 10, done: 10, overdue: 0, pct_done: 100 }, otimizacoes: { total: 9, done: 7, overdue: 1, pct_done: 78 }, saldo: { total: 6, done: 6, overdue: 0, pct_done: 100 } } },
      { client: "Casa do Churras", current_stage: 3, current_stage_label: "Criacao de LP", health: "yellow", total_overdue: 0,
        boards: { briefing: { total: 5, done: 5, overdue: 0, pct_done: 100 }, lp: { total: 5, done: 3, overdue: 0, pct_done: 60 }, campanhas: { total: 10, done: 2, overdue: 0, pct_done: 20 } } },
      { client: "Studio Verde", current_stage: 1, current_stage_label: "Briefing", health: "yellow", total_overdue: 0,
        boards: { briefing: { total: 5, done: 1, overdue: 0, pct_done: 20 } } },
      { client: "Pizzaria Donato", current_stage: 6, current_stage_label: "Otimização + Saldo (loop semanal)", health: "green", total_overdue: 0,
        boards: { briefing: { total: 5, done: 5, overdue: 0, pct_done: 100 }, lp: { total: 5, done: 5, overdue: 0, pct_done: 100 }, campanhas: { total: 10, done: 10, overdue: 0, pct_done: 100 }, otimizacoes: { total: 8, done: 8, overdue: 0, pct_done: 100 }, saldo: { total: 6, done: 6, overdue: 0, pct_done: 100 } } },
    ],
  };
}
