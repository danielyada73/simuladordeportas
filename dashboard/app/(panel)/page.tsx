import { apiGet } from "@/lib/api";
import type { TasksResponse } from "@/lib/types";
import { FilterBar } from "@/components/FilterBar";
import { AutoRefresh } from "@/components/AutoRefresh";
import { PriorityBadge, StatusBadge, AvatarGroup } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import { ListTodo, AlarmClock, Flame, CircleCheck, TriangleAlert, Inbox } from "lucide-react";

type SP = Promise<{
  window?: string;
  custom_from?: string;
  custom_to?: string;
  assignee?: string;
  client?: string;
}>;

function fmtDate(iso: string): { day: string; rest: string; overdue: boolean } {
  if (!iso) return { day: "", rest: "—", overdue: false };
  const [y, m, d] = iso.split("-");
  const date = new Date(`${iso}T12:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const overdue = date < today;
  const months = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  return { day: d, rest: `${months[parseInt(m, 10) - 1]} ${y.slice(2)}`, overdue };
}

export default async function DemandasPage({ searchParams }: { searchParams: SP }) {
  const sp = await searchParams;
  const windowKey = sp.window || "today";

  let data: TasksResponse | null = null;
  let error: string | null = null;
  let allData: TasksResponse | null = null;
  let overdueData: TasksResponse | null = null;

  try {
    [data, allData, overdueData] = await Promise.all([
      apiGet<TasksResponse>("/api/tasks", {
        window: windowKey,
        custom_from: sp.custom_from,
        custom_to: sp.custom_to,
        assignee: sp.assignee,
        client: sp.client,
        include_done: "false",
        limit: "500",
      }),
      apiGet<TasksResponse>("/api/tasks", { window: "all", include_done: "false" }),
      apiGet<TasksResponse>("/api/tasks", { window: "overdue", include_done: "false" }),
    ]);
  } catch (e) {
    error = e instanceof Error ? e.message : "Erro desconhecido";
  }

  const urgentCount = data?.items.filter((t) => t.priority_rank <= 1).length ?? 0;
  const highCount = data?.items.filter((t) => t.priority_rank === 2).length ?? 0;
  const overdueCount = overdueData?.count ?? 0;
  const allCount = allData?.count ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <div className="text-xs text-muted uppercase tracking-wider">Visão geral</div>
          <h1 className="text-3xl font-semibold">Demandas</h1>
          <p className="text-sm text-muted-strong">
            {data ? `${data.count} ${data.count === 1 ? "tarefa em" : "tarefas em"} ${windowToLabel(windowKey)}` : "—"}
          </p>
        </div>
        <AutoRefresh intervalMs={60000} />
      </div>

      {/* KPI tiles */}
      <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
        <KpiCard label="Tarefas abertas" value={allCount} hint="todas em todos os clientes" icon={ListTodo} />
        <KpiCard label="Atrasadas" value={overdueCount} hint={overdueCount > 0 ? "ação necessária" : "tudo no prazo"} icon={AlarmClock} tone="urgent" />
        <KpiCard label="Urgentes nessa janela" value={urgentCount} hint="prioridade Urgente" icon={Flame} tone="high" />
        <KpiCard label="Alta nessa janela" value={highCount} hint="prioridade Alta" icon={TriangleAlert} tone="default" />
      </div>

      <FilterBar />

      {error && (
        <div className="card border-urgent/30 bg-urgent/5 text-urgent flex items-start gap-3 p-4 text-sm">
          <TriangleAlert className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <div className="font-medium">Não foi possível carregar do Monday</div>
            <div className="text-urgent/70 mt-0.5 text-xs">{error}</div>
          </div>
        </div>
      )}

      {data && (
        <div className="card overflow-hidden shadow-card">
          <div className="grid grid-cols-[80px_1fr_180px_140px_120px_140px_90px] gap-4 px-5 py-3 border-b border-border bg-surface-2/50 text-[11px] uppercase tracking-wider text-muted font-medium">
            <div>Prioridade</div>
            <div>Tarefa</div>
            <div>Cliente</div>
            <div>Etapa</div>
            <div>Status</div>
            <div>Responsável</div>
            <div className="text-right">Prazo</div>
          </div>
          {data.items.length === 0 ? (
            <EmptyState />
          ) : (
            <div>
              {data.items.map((t, i) => {
                const d = fmtDate(t.due_date);
                return (
                  <div
                    key={t.id}
                    className={`grid grid-cols-[80px_1fr_180px_140px_120px_140px_90px] gap-4 px-5 py-4 items-center hover:bg-surface-2/40 transition-colors ${
                      i !== 0 ? "border-t border-border" : ""
                    }`}
                  >
                    <div><PriorityBadge value={t.priority} /></div>
                    <div className="min-w-0">
                      <div className="font-medium text-text truncate">{t.name}</div>
                      {t.group_name && t.group_name !== t.board_type && (
                        <div className="text-xs text-muted-strong truncate mt-0.5">{t.group_name}</div>
                      )}
                    </div>
                    <div className="text-sm text-text truncate">{t.client}</div>
                    <div className="text-sm text-muted-strong capitalize">{t.board_type}</div>
                    <div><StatusBadge value={t.status} /></div>
                    <div><AvatarGroup names={t.assignees} /></div>
                    <div className={`text-right numeric text-sm ${d.overdue ? "text-urgent" : "text-text"}`}>
                      <div className="text-base font-semibold leading-none">{d.day}</div>
                      <div className="text-[11px] text-muted mt-0.5">{d.rest}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="w-12 h-12 rounded-xl bg-surface-2 border border-border flex items-center justify-center mb-4">
        <Inbox className="w-6 h-6 text-muted" />
      </div>
      <div className="text-text font-medium">Nada por aqui</div>
      <div className="text-sm text-muted-strong mt-1">Nenhuma tarefa pendente nessa janela. Bom trabalho. ✦</div>
    </div>
  );
}

function windowToLabel(w: string): string {
  const m: Record<string, string> = {
    today: "hoje",
    tomorrow: "amanhã",
    overdue: "atraso",
    week: "próximos 7 dias",
    month: "próximos 30 dias",
    all: "todos os períodos",
    custom: "intervalo customizado",
  };
  return m[w] || w;
}
