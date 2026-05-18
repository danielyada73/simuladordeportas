import { apiGet } from "@/lib/api";
import type { StagesResponse } from "@/lib/types";
import { AutoRefresh } from "@/components/AutoRefresh";
import { HealthDot } from "@/components/Badges";
import { KpiCard } from "@/components/KpiCard";
import { Building2, AlarmClock, TrendingUp, AlertTriangle, ChevronRight } from "lucide-react";

const BOARDS: { key: string; label: string }[] = [
  { key: "briefing", label: "Briefing" },
  { key: "lp", label: "LP" },
  { key: "campanhas", label: "Campanhas" },
  { key: "otimizacoes", label: "Otimização" },
  { key: "saldo", label: "Saldo" },
];

const STAGE_COLOR: Record<number, string> = {
  1: "bg-medium/15 text-medium border-medium/30",
  3: "bg-high/15 text-high border-high/30",
  5: "bg-progress/15 text-progress border-progress/30",
  6: "bg-low/15 text-low border-low/30",
};

export default async function ClientesPage() {
  let data: StagesResponse | null = null;
  let error: string | null = null;
  try {
    data = await apiGet<StagesResponse>("/api/clients/stages");
  } catch (e) {
    error = e instanceof Error ? e.message : "Erro desconhecido";
  }

  const totalClients = data?.clients.length ?? 0;
  const inOptim = data?.clients.filter((c) => c.current_stage === 6).length ?? 0;
  const critical = data?.clients.filter((c) => c.health === "red").length ?? 0;
  const totalOverdue = data?.clients.reduce((acc, c) => acc + c.total_overdue, 0) ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <div className="text-xs text-muted uppercase tracking-wider">Portfólio</div>
          <h1 className="text-3xl font-semibold">Clientes & Etapa POP</h1>
          <p className="text-sm text-muted-strong">{totalClients} clientes ativos · acompanhamento do processo</p>
        </div>
        <AutoRefresh intervalMs={120000} />
      </div>

      <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
        <KpiCard label="Clientes ativos" value={totalClients} icon={Building2} />
        <KpiCard label="Em otimização" value={inOptim} hint="Etapa 6 do POP" icon={TrendingUp} tone="done" />
        <KpiCard label="Críticos" value={critical} hint="com atraso" icon={AlertTriangle} tone="urgent" />
        <KpiCard label="Tarefas atrasadas" value={totalOverdue} hint="soma de todos" icon={AlarmClock} tone="high" />
      </div>

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
        <div className="card shadow-card overflow-hidden">
          <div className="grid grid-cols-[1.5fr_1.4fr_90px_1fr_1fr_1fr_1fr_1fr_30px] gap-4 px-5 py-3 border-b border-border bg-surface-2/50 text-[11px] uppercase tracking-wider text-muted font-medium">
            <div>Cliente</div>
            <div>Etapa atual</div>
            <div className="text-center">Atraso</div>
            {BOARDS.map((b) => <div key={b.key} className="text-center">{b.label}</div>)}
            <div />
          </div>
          {data.clients.length === 0 ? (
            <div className="py-12 text-center text-muted">Nenhum cliente encontrado no Monday.</div>
          ) : (
            data.clients.map((c, i) => (
              <div
                key={c.client}
                className={`grid grid-cols-[1.5fr_1.4fr_90px_1fr_1fr_1fr_1fr_1fr_30px] gap-4 px-5 py-4 items-center hover:bg-surface-2/40 transition-colors ${
                  i !== 0 ? "border-t border-border" : ""
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <HealthDot health={c.health} />
                  <span className="font-medium text-text truncate">{c.client}</span>
                </div>
                <div>
                  <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-xs font-medium ${STAGE_COLOR[c.current_stage] || "bg-border text-muted border-border"}`}>
                    <span className="numeric font-bold">{c.current_stage}</span>
                    <span>{c.current_stage_label}</span>
                  </span>
                </div>
                <div className="text-center">
                  {c.total_overdue > 0 ? (
                    <span className="inline-flex items-center gap-1 text-urgent numeric font-semibold text-sm">
                      <AlarmClock className="w-3.5 h-3.5" />{c.total_overdue}
                    </span>
                  ) : (
                    <span className="text-muted text-sm">—</span>
                  )}
                </div>
                {BOARDS.map((b) => {
                  const board = c.boards[b.key];
                  if (!board) {
                    return (
                      <div key={b.key} className="text-center text-muted text-xs">—</div>
                    );
                  }
                  const isDone = board.pct_done >= 100;
                  return (
                    <div key={b.key} className="flex flex-col items-center gap-1">
                      <div className="text-xs text-muted-strong numeric">{board.done}/{board.total}</div>
                      <div className="w-full max-w-[80px] h-1 bg-border rounded-full overflow-hidden">
                        <div
                          className={`h-full ${isDone ? "bg-done" : board.pct_done >= 50 ? "bg-progress" : "bg-medium"}`}
                          style={{ width: `${Math.min(100, board.pct_done)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
                <ChevronRight className="w-4 h-4 text-muted" />
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
