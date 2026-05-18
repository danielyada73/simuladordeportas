import { apiGet } from "@/lib/api";
import type { AssigneeResponse, AssigneeBucket } from "@/lib/types";
import { FilterBar } from "@/components/FilterBar";
import { AutoRefresh } from "@/components/AutoRefresh";
import { Avatar } from "@/components/Badges";
import { Flame, AlertTriangle, Circle, Minus, TrendingUp, CalendarClock, AlarmClock, Loader, CircleCheck } from "lucide-react";

type SP = Promise<{ window?: string; custom_from?: string; custom_to?: string }>;

export default async function ResponsaveisPage({ searchParams }: { searchParams: SP }) {
  const sp = await searchParams;
  const windowKey = sp.window || "all";

  let data: AssigneeResponse | null = null;
  let error: string | null = null;
  try {
    data = await apiGet<AssigneeResponse>("/api/tasks/by-assignee", {
      window: windowKey,
      custom_from: sp.custom_from,
      custom_to: sp.custom_to,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Erro desconhecido";
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <div className="text-xs text-muted uppercase tracking-wider">Equipe</div>
          <h1 className="text-3xl font-semibold">Responsáveis</h1>
          <p className="text-sm text-muted-strong">Carga e progresso por pessoa</p>
        </div>
        <AutoRefresh intervalMs={60000} />
      </div>

      <FilterBar />

      {error && (
        <div className="card border-urgent/30 bg-urgent/5 text-urgent flex items-start gap-3 p-4 text-sm">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <div className="font-medium">Não foi possível carregar do Monday</div>
            <div className="text-urgent/70 mt-0.5 text-xs">{error}</div>
          </div>
        </div>
      )}

      {data && (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {data.assignees.length === 0 && (
            <div className="col-span-full text-center text-muted py-16">Nenhuma tarefa atribuída nessa janela.</div>
          )}
          {data.assignees.map((a) => <PersonCard key={a.assignee} bucket={a} />)}
        </div>
      )}
    </div>
  );
}

function PersonCard({ bucket }: { bucket: AssigneeBucket }) {
  const completion = bucket.total > 0 ? Math.round((bucket.done / bucket.total) * 100) : 0;
  const open = bucket.total - bucket.done;
  return (
    <div className="card shadow-card overflow-hidden">
      {/* Header */}
      <div className="p-5 flex items-center gap-4 border-b border-border">
        <Avatar name={bucket.assignee} size={44} />
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-lg truncate">{bucket.assignee}</div>
          <div className="text-xs text-muted-strong">{bucket.total} tarefas no escopo</div>
        </div>
        <div className="text-right">
          <div className="numeric text-2xl font-semibold leading-none">{completion}%</div>
          <div className="text-[10px] uppercase tracking-wider text-muted mt-1">Conclusão</div>
        </div>
      </div>

      {/* Progress bar */}
      <div className="px-5 pt-4">
        <div className="h-1.5 bg-border rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-low to-medium rounded-full transition-all"
            style={{ width: `${completion}%` }}
          />
        </div>
      </div>

      {/* Status grid */}
      <div className="grid grid-cols-3 gap-3 p-5 pt-4">
        <Stat icon={CircleCheck} label="Concluídas" value={bucket.done} tone="text-done" />
        <Stat icon={Loader} label="Em curso" value={bucket.in_progress} tone="text-progress" />
        <Stat icon={AlarmClock} label="Atrasadas" value={bucket.overdue} tone={bucket.overdue > 0 ? "text-urgent" : "text-muted-strong"} />
      </div>

      <div className="px-5 pb-3 flex items-center justify-between text-xs text-muted-strong">
        <span className="flex items-center gap-1.5"><CalendarClock className="w-3.5 h-3.5" />Próximos 7 dias</span>
        <span className="numeric font-semibold text-text">{bucket.next_7_days}</span>
      </div>

      {/* Priority breakdown */}
      <div className="px-5 py-4 border-t border-border bg-surface-2/30">
        <div className="text-[10px] uppercase tracking-wider text-muted mb-3">Distribuição por prioridade</div>
        <div className="space-y-2">
          <PrioRow icon={Flame} label="Urgente" value={bucket.by_priority.urgente} total={open} color="bg-urgent" textColor="text-urgent" />
          <PrioRow icon={AlertTriangle} label="Alta" value={bucket.by_priority.alta} total={open} color="bg-high" textColor="text-high" />
          <PrioRow icon={Circle} label="Média" value={bucket.by_priority.media} total={open} color="bg-medium" textColor="text-medium" />
          <PrioRow icon={Minus} label="Baixa" value={bucket.by_priority.baixa} total={open} color="bg-low" textColor="text-low" />
        </div>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, tone }: { icon: any; label: string; value: number; tone: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2/40 p-3 text-center">
      <Icon className={`w-4 h-4 mx-auto mb-1.5 ${tone}`} />
      <div className={`numeric text-xl font-semibold leading-none ${tone}`}>{value}</div>
      <div className="text-[10px] text-muted mt-1.5 uppercase tracking-wider">{label}</div>
    </div>
  );
}

function PrioRow({ icon: Icon, label, value, total, color, textColor }: { icon: any; label: string; value: number; total: number; color: string; textColor: string }) {
  const pct = total > 0 ? (value / total) * 100 : 0;
  return (
    <div className="flex items-center gap-3 text-xs">
      <div className="flex items-center gap-1.5 w-16 shrink-0">
        <Icon className={`w-3 h-3 ${textColor}`} />
        <span className="text-muted-strong">{label}</span>
      </div>
      <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className={`numeric w-6 text-right font-semibold ${value > 0 ? textColor : "text-muted"}`}>{value}</div>
    </div>
  );
}
