import { missionsApi } from "@/lib/missions-api";
import type {
  Mission,
  MissionUser,
  MissionSettings,
  MissionsStats,
  ResponsibleStat,
} from "@/lib/missions-types";
import { MissoesHeader } from "@/components/missions/MissoesHeader";
import { CompletedMissionRow } from "@/components/missions/CompletedMissionRow";
import { PieChart } from "@/components/missions/PieChart";
import { SortableMissionList } from "@/components/missions/SortableMissionList";
import { ArrowUpRight, Sparkles, TriangleAlert } from "lucide-react";

type SP = Promise<{ window?: string; custom_from?: string; custom_to?: string }>;

export default async function MissoesPage({ searchParams }: { searchParams: SP }) {
  const sp = await searchParams;
  const windowKey = sp.window || "today";

  let missions: Mission[] = [];
  let users: MissionUser[] = [];
  let settings: MissionSettings = { id: "singleton", logo_url: null, client_options: [] };
  let stats: MissionsStats | null = null;
  let error: string | null = null;

  try {
    const [missionsRes, usersRes, settingsRes, statsRes] = await Promise.all([
      missionsApi.list({ window: windowKey, custom_from: sp.custom_from, custom_to: sp.custom_to, include_completed: true }),
      missionsApi.users(),
      missionsApi.settings(),
      missionsApi.stats({ window: windowKey, custom_from: sp.custom_from, custom_to: sp.custom_to }),
    ]);
    missions = missionsRes.items;
    users = usersRes.items;
    settings = settingsRes;
    stats = statsRes;
  } catch (e) {
    error = e instanceof Error ? e.message : "Erro desconhecido";
  }

  const userBySlug = new Map(users.map((u) => [u.slug, u]));
  const principais = missions.filter((m) => m.kind === "principal" && m.status !== "concluida");
  const secundarias = missions.filter((m) => m.kind === "secundaria" && m.status !== "concluida");
  const concluidas = missions.filter((m) => m.status === "concluida");

  const completionPct = stats && stats.total > 0
    ? Math.round((stats.by_status.concluida / stats.total) * 100)
    : 0;

  return (
    <>
      <MissoesHeader users={users} settings={settings} />

      <main className="max-w-[1500px] mx-auto px-6 py-10 space-y-6">
        {/* HERO */}
        <section className="flex items-end justify-between gap-6 flex-wrap pb-2">
          <div>
            <div className="text-xs uppercase tracking-[0.25em] text-white/45 mb-2">
              Comando central · {windowLabel(windowKey)}
            </div>
            <h1 className="font-stencil text-7xl md:text-8xl tracking-[0.04em] leading-[0.9] text-white">
              MISSÕES <span className="text-ms-blue">DIÁRIAS</span>
            </h1>
          </div>
          {stats && stats.total > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-white text-black border border-white shadow-[0_14px_40px_-20px_rgba(0,180,252,0.8)]">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-semibold">
                <span className="font-stencil text-lg text-ms-blue">{completionPct}%</span> concluído no escopo
              </span>
            </div>
          )}
        </section>

        {error && <ErrorBox message={error} />}

        {/* BENTO TOP: 4 cards (1 grande branco + 3 escuros) */}
        {stats && (
          <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr_1fr_1fr] gap-4">
            <BigWhiteKpi
              label="Missões no escopo"
              value={stats.total}
              hint={`${stats.by_status.concluida} concluídas · ${stats.by_status.em_progresso} em curso`}
            />
            <DarkKpi label="Em curso" value={stats.by_status.em_progresso} tone="lilac" />
            <DarkKpi label="Abertas" value={stats.by_status.nao_iniciada} tone="blue" />
            <DarkKpi label="Concluídas" value={stats.by_status.concluida} tone="green" />
          </div>
        )}

        {/* PAINEL GERAL: donut grande + responsáveis */}
        {stats && (
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.3fr] gap-4">
            <DarkCard>
              <div className="flex flex-col h-full">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-white">Distribuição</h3>
                    <p className="text-xs text-white/40 mt-0.5">Status do escopo atual</p>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-ms-blue/15 text-ms-blue text-[10px] font-semibold uppercase tracking-wider">
                    {windowLabel(windowKey)}
                  </div>
                </div>
                <div className="flex flex-col items-center gap-6 flex-1 justify-center">
                  <PieChart
                    size={240}
                    centerLabel="Total"
                    slices={[
                      { label: "Concluídas", value: stats.by_status.concluida, color: "#ffffff" },
                      { label: "Em curso", value: stats.by_status.em_progresso, color: "#00B4FC" },
                      { label: "Abertas", value: stats.by_status.nao_iniciada, color: "#3a3d45" },
                    ]}
                  />
                  <div className="grid grid-cols-3 gap-2 w-full">
                    <LegendChip color="#ffffff" label="Concluídas" value={stats.by_status.concluida} />
                    <LegendChip color="#00B4FC" label="Em curso" value={stats.by_status.em_progresso} />
                    <LegendChip color="#3a3d45" label="Abertas" value={stats.by_status.nao_iniciada} />
                  </div>
                </div>
              </div>
            </DarkCard>

            <WhiteCard>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-black/90">Por responsável</h3>
                  <p className="text-xs text-black/45 mt-0.5">Carga e progresso na janela</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-black/50">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{stats.by_responsible.length} operadores</span>
                </div>
              </div>
              <div className="space-y-3">
                {stats.by_responsible.length === 0 ? (
                  <div className="text-black/40 text-sm py-8 text-center">Sem operadores alocados</div>
                ) : (
                  stats.by_responsible.map((r) => (
                    <ResponsibleRowLight key={r.slug} stat={r} user={userBySlug.get(r.slug)} />
                  ))
                )}
              </div>
            </WhiteCard>
          </div>
        )}

        {/* MISSÕES */}
        <section>
          <WhiteCard>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-lg font-semibold text-black/90">Missões</h3>
                <p className="text-xs text-black/45 mt-0.5">Alvos prioritários · {principais.length} ativas</p>
              </div>
            </div>
            {principais.length === 0 ? (
              <EmptyLight message="Nenhuma missão principal" />
            ) : (
              <div className="grid lg:grid-cols-2 gap-4">
                {groupByResponsible(principais, users).map(({ user, items }) => (
                  <PrincipalColumn
                    key={user.slug}
                    user={user}
                    missions={items}
                    users={users}
                    clientOptions={settings.client_options || []}
                  />
                ))}
              </div>
            )}
          </WhiteCard>
        </section>

        {/* REUNIÕES */}
        <section>
          <DarkCard>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Reuniões</h3>
                <p className="text-xs text-white/40 mt-0.5">Agenda e alinhamentos · {secundarias.length}</p>
              </div>
            </div>
            {secundarias.length === 0 ? (
              <EmptyDark message="Nenhuma reunião no momento" />
            ) : (
              <SortableMissionList
                missions={secundarias}
                users={users}
                clientOptions={settings.client_options || []}
                compact
                variant="dark"
                cardTone="meeting"
                className="grid lg:grid-cols-2 gap-3"
                storageKey="missions:reunioes"
              />
            )}
          </DarkCard>
        </section>

        {/* CONCLUÍDAS */}
        {concluidas.length > 0 && (
          <section>
            <DarkCard>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-base font-semibold text-white">Cumpridas</h3>
                  <p className="text-xs text-white/40 mt-0.5">Histórico do escopo · {concluidas.length}</p>
                </div>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                {concluidas.map((m) => (
                  <CompletedMissionRow
                    key={m.id}
                    mission={m}
                    user={userBySlug.get(m.responsible_slug)}
                    users={users}
                    clientOptions={settings.client_options || []}
                  />
                ))}
              </div>
            </DarkCard>
          </section>
        )}

        {/* PERFORMANCE — cards brancos */}
        {stats && stats.by_responsible.length > 0 && (
          <section>
            <WhiteCard>
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-lg font-semibold text-black/90">Performance</h3>
                  <p className="text-xs text-black/45 mt-0.5">Taxa de conclusão por pessoa</p>
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-4">
                {stats.by_responsible.map((r) => {
                  const u = userBySlug.get(r.slug);
                  const rate = r.total > 0 ? Math.round((r.done / r.total) * 100) : 0;
                  return <PerformanceCard key={r.slug} stat={r} user={u} rate={rate} />;
                })}
              </div>
            </WhiteCard>
          </section>
        )}
      </main>
    </>
  );
}

// ============================================================ Cards base

function DarkCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`relative rounded-[30px] border border-white/[0.08] bg-[#101113] p-6 overflow-hidden shadow-[0_20px_80px_-45px_rgba(0,180,252,0.55)] ${className}`}>
      {children}
    </div>
  );
}

function WhiteCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`relative rounded-[30px] bg-white p-6 overflow-hidden shadow-[0_1px_0_rgba(255,255,255,0.1)_inset,0_24px_70px_-28px_rgba(0,0,0,0.75)] ${className}`}>
      {children}
    </div>
  );
}

// ============================================================ KPI

function BigWhiteKpi({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="relative rounded-[30px] bg-white p-6 overflow-hidden">
      <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-ms-blue/20 blur-2xl pointer-events-none" />
      <div className="relative flex items-end justify-between gap-6 h-full">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-black/45">{label}</div>
          <div className="font-stencil text-7xl text-black tracking-wide leading-[0.9] mt-2">{value}</div>
          {hint && <div className="text-xs text-black/50 mt-3">{hint}</div>}
        </div>
        <div className="w-12 h-12 rounded-full bg-ms-blue text-black flex items-center justify-center shrink-0">
          <ArrowUpRight className="w-5 h-5" strokeWidth={2.5} />
        </div>
      </div>
    </div>
  );
}

function DarkKpi({ label, value, tone }: { label: string; value: number; tone: "lilac" | "blue" | "green" }) {
  const toneCls = {
    lilac: "bg-ms-blue",
    blue: "bg-ms-blue",
    green: "bg-white",
  }[tone];
  return (
    <div className="relative rounded-[30px] border border-white/[0.08] bg-[#101113] p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <span className={`w-2.5 h-2.5 rounded-full ${toneCls}`} style={{ boxShadow: `0 0 12px currentColor` }} />
        <div className="text-xs uppercase tracking-[0.2em] text-white/35">{label}</div>
      </div>
      <div className="font-stencil text-6xl text-white leading-none tracking-wide">{value}</div>
    </div>
  );
}

// ============================================================ Legend / Responsável

function LegendChip({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="rounded-[20px] bg-white/[0.05] border border-white/[0.06] px-3 py-2.5 flex flex-col gap-0.5">
      <div className="flex items-center gap-1.5">
        <span className="inline-block w-2 h-2 rounded-full" style={{ background: color }} />
        <span className="text-[10px] uppercase tracking-wider text-white/45">{label}</span>
      </div>
      <span className="font-stencil text-2xl text-white leading-none">{value}</span>
    </div>
  );
}

function ResponsibleRowLight({ stat, user }: { stat: ResponsibleStat; user?: MissionUser }) {
  const pct = stat.total > 0 ? Math.round((stat.done / stat.total) * 100) : 0;
  const name = user?.display_name || stat.slug;
  return (
    <div className="flex items-center gap-3 rounded-[22px] bg-black/[0.035] hover:bg-black/[0.06] transition-colors px-3 py-2.5">
      {user?.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.photo_url} alt={name} className="w-11 h-11 rounded-full object-cover ring-2 ring-white" />
      ) : (
        <div className="w-11 h-11 rounded-full bg-ms-blue flex items-center justify-center font-bold text-white ring-2 ring-white">
          {name[0]}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-3">
          <div className="font-semibold text-black/85 text-sm">{name}</div>
          <div className="font-stencil text-xl text-black leading-none">{pct}%</div>
        </div>
        <div className="h-1.5 bg-black/[0.08] rounded-full mt-2 overflow-hidden">
          <div className="h-full bg-ms-blue rounded-full" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[11px]">
          <Stat label="total" value={stat.total} />
          <Stat label="curso" value={stat.in_progress} tone="text-ms-blue-deep" />
          <Stat label="feita" value={stat.done} tone="text-black" />
          <span className="text-black/15">·</span>
          <Stat label="alta" value={stat.alta} tone="text-ms-blue-deep" />
          <Stat label="méd" value={stat.media} />
          <Stat label="baixa" value={stat.baixa} />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-black/70" }: { label: string; value: number; tone?: string }) {
  return (
    <span className="flex gap-1">
      <span className="text-black/35">{label}</span>
      <span className={`numeric font-semibold ${tone}`}>{value}</span>
    </span>
  );
}

// ============================================================ Principal column (no card branco)

function PrincipalColumn({
  user,
  missions,
  users,
  clientOptions,
}: {
  user: MissionUser;
  missions: Mission[];
  users: MissionUser[];
  clientOptions: string[];
}) {
  return (
    <div className="rounded-[24px] bg-black/[0.035] overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-black/[0.06]">
        {user.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.photo_url}
            alt={user.display_name}
            className="w-11 h-11 rounded-full object-cover ring-2 ring-white"
          />
        ) : (
          <div className="w-11 h-11 rounded-full bg-ms-blue flex items-center justify-center font-bold text-white ring-2 ring-white">
            {user.display_name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-semibold text-black/85">{user.display_name}</div>
          <div className="text-xs text-black/45 mt-0.5">{missions.length} missões ativas</div>
        </div>
        <div className="font-stencil text-3xl text-black/75 leading-none">{String(missions.length).padStart(2, "0")}</div>
      </div>
      <div className="p-3">
        <SortableMissionList
          missions={missions}
          users={users}
          clientOptions={clientOptions}
          variant="light"
          storageKey={`missions:principais:${user.slug}`}
        />
      </div>
    </div>
  );
}

// ============================================================ Performance

function PerformanceCard({ stat, user, rate }: { stat: ResponsibleStat; user?: MissionUser; rate: number }) {
  const name = user?.display_name || stat.slug;
  return (
    <div className="rounded-[24px] bg-black/[0.035] p-4 space-y-4">
      <div className="flex items-center gap-3">
        {user?.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.photo_url} alt={name} className="w-11 h-11 rounded-full object-cover ring-2 ring-white" />
        ) : (
          <div className="w-11 h-11 rounded-full bg-ms-blue flex items-center justify-center font-bold text-white ring-2 ring-white">
            {name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-semibold text-black/85 text-sm">{name}</div>
          <div className="text-xs text-black/45 mt-0.5">Taxa de conclusão</div>
        </div>
        <div className="font-stencil text-3xl text-black leading-none">{rate}%</div>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <MiniStat label="Total" value={stat.total} />
        <MiniStat label="OK" value={stat.done} tone="text-black" />
        <MiniStat label="Curso" value={stat.in_progress} tone="text-ms-blue-deep" />
        <MiniStat label="Alta" value={stat.alta} tone="text-ms-blue-deep" />
      </div>
    </div>
  );
}

function MiniStat({ label, value, tone = "text-black" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-xl bg-white py-2">
      <div className={`font-stencil text-xl leading-none ${tone}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-black/40 mt-1">{label}</div>
    </div>
  );
}

// ============================================================ Empty / Error

function EmptyDark({ message }: { message: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-white/10 py-12 text-center">
      <div className="text-white/40 text-sm">{message}</div>
    </div>
  );
}

function EmptyLight({ message }: { message: string }) {
  return (
    <div className="rounded-[24px] border border-dashed border-black/10 py-12 text-center">
      <div className="text-black/40 text-sm">{message}</div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-[24px] border border-ms-blue/30 bg-ms-blue/10 px-4 py-3 text-ms-blue flex items-start gap-3">
      <TriangleAlert className="w-5 h-5 mt-0.5 shrink-0" />
      <div>
        <div className="font-semibold">Falha ao carregar missões</div>
        <div className="text-xs mt-1 text-ms-blue/80 font-mono">{message}</div>
      </div>
    </div>
  );
}

// ============================================================ Utils

function groupByResponsible(missions: Mission[], users: MissionUser[]): { user: MissionUser; items: Mission[] }[] {
  const groups = new Map<string, { user: MissionUser; items: Mission[] }>();
  for (const m of missions) {
    const user = users.find((u) => u.slug === m.responsible_slug) || {
      slug: m.responsible_slug,
      display_name: m.responsible_slug,
      photo_url: null,
      accent_color: "#00B4FC",
      is_active: true,
      sort_order: 99,
    };
    const g = groups.get(user.slug) || { user, items: [] };
    g.items.push(m);
    groups.set(user.slug, g);
  }
  return Array.from(groups.values()).sort((a, b) => a.user.sort_order - b.user.sort_order);
}

function windowLabel(w: string): string {
  const m: Record<string, string> = {
    today: "Hoje",
    tomorrow: "Amanhã",
    overdue: "Atrasadas",
    week: "Próximos 7 dias",
    month: "Próximos 30 dias",
    all: "Todas",
    custom: "Período customizado",
  };
  return m[w] || w;
}
