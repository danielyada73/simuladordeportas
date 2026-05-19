import { missionsApi } from "@/lib/missions-api";
import type {
  Mission,
  MissionUser,
  MissionSettings,
  MissionsStats,
  ResponsibleStat,
} from "@/lib/missions-types";
import { MissoesHeader } from "@/components/missions/MissoesHeader";
import { MissionCard } from "@/components/missions/MissionCard";
import { PieChart } from "@/components/missions/PieChart";
import {
  Target,
  Crosshair,
  Trophy,
  CheckCircle2,
  Loader2,
  Circle,
  Flame,
  AlertTriangle,
  TriangleAlert,
  ArrowUpRight,
} from "lucide-react";

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

  return (
    <>
      <MissoesHeader users={users} settings={settings} />

      <main className="max-w-[1500px] mx-auto px-6 py-10 space-y-8">
        {/* HERO */}
        <section className="flex items-start justify-between gap-6 flex-wrap">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-white/40 mb-2">
              Comando central · {windowLabel(windowKey)}
            </div>
            <h1 className="font-stencil text-6xl md:text-7xl tracking-[0.04em] leading-none text-white">
              MISSÕES <span className="text-accent">DIÁRIAS</span>
            </h1>
            <p className="text-white/50 text-sm mt-3 max-w-md">
              Painel paralelo ao Monday — tarefas avulsas, status e progresso da equipe em tempo real.
            </p>
          </div>
        </section>

        {error && <ErrorBox message={error} />}

        {/* KPI TILES */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KpiTile
              icon={Target}
              label="Total no escopo"
              value={stats.total}
              accent="from-accent/30 to-accent/5"
              iconBg="bg-accent/15 text-accent"
            />
            <KpiTile
              icon={CheckCircle2}
              label="Concluídas"
              value={stats.by_status.concluida}
              accent="from-low/30 to-low/5"
              iconBg="bg-low/15 text-low"
              hint={stats.total > 0 ? `${Math.round((stats.by_status.concluida / stats.total) * 100)}% do escopo` : undefined}
            />
            <KpiTile
              icon={Loader2}
              label="Em curso"
              value={stats.by_status.em_progresso}
              accent="from-camo-amber/30 to-camo-amber/5"
              iconBg="bg-camo-amber/15 text-camo-amber"
            />
            <KpiTile
              icon={Circle}
              label="Abertas"
              value={stats.by_status.nao_iniciada}
              accent="from-camo-cyan/30 to-camo-cyan/5"
              iconBg="bg-camo-cyan/15 text-camo-cyan"
            />
          </div>
        )}

        {/* PAINEL GERAL */}
        {stats && (
          <Card>
            <CardHeader title="Painel geral" subtitle="Distribuição da operação" />
            <div className="grid lg:grid-cols-[280px_1fr] gap-8 items-start p-6">
              <div className="flex flex-col items-center gap-5">
                <PieChart
                  size={220}
                  centerLabel="Total"
                  slices={[
                    { label: "Concluídas", value: stats.by_status.concluida, color: "#10b981" },
                    { label: "Em curso", value: stats.by_status.em_progresso, color: "#fbbf24" },
                    { label: "Abertas", value: stats.by_status.nao_iniciada, color: "#22d3ee" },
                  ]}
                />
                <div className="flex flex-col gap-2 w-full">
                  <Legend color="#10b981" label="Concluídas" value={stats.by_status.concluida} />
                  <Legend color="#fbbf24" label="Em curso" value={stats.by_status.em_progresso} />
                  <Legend color="#22d3ee" label="Abertas" value={stats.by_status.nao_iniciada} />
                </div>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <KindStat icon={Target} label="Missões principais" value={stats.by_kind.principal} />
                  <KindStat icon={Crosshair} label="Secundárias" value={stats.by_kind.secundaria} />
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wider text-white/40 mb-3">Por responsável</div>
                  <div className="space-y-2">
                    {stats.by_responsible.length === 0 ? (
                      <div className="text-white/30 text-sm">Nenhum operador alocado</div>
                    ) : (
                      stats.by_responsible.map((r) => (
                        <ResponsibleRow key={r.slug} stat={r} user={userBySlug.get(r.slug)} />
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* MISSÕES PRINCIPAIS */}
        <section className="space-y-4">
          <SectionHeader title="Missões principais" subtitle="Alvos prioritários" icon={Target} count={principais.length} />
          {principais.length === 0 ? (
            <EmptyPanel message="Nenhuma missão principal nessa janela" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-5">
              {groupByResponsible(principais, users).map(({ user, items }) => (
                <PrincipalColumn key={user.slug} user={user} missions={items} />
              ))}
            </div>
          )}
        </section>

        {/* SECUNDÁRIAS */}
        <section className="space-y-4">
          <SectionHeader title="Missões secundárias" subtitle="Apoio operacional" icon={Crosshair} count={secundarias.length} />
          {secundarias.length === 0 ? (
            <EmptyPanel message="Nada secundário no momento" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-x-5 gap-y-2.5">
              {secundarias.map((m) => (
                <MissionCard key={m.id} mission={m} compact />
              ))}
            </div>
          )}
        </section>

        {/* CONCLUÍDAS */}
        <section className="space-y-4">
          <SectionHeader title="Missões cumpridas" subtitle="Histórico do escopo" icon={Trophy} count={concluidas.length} />
          {concluidas.length === 0 ? (
            <EmptyPanel message="Nenhuma missão cumprida ainda" />
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {concluidas.map((m) => (
                <CompletedRow key={m.id} mission={m} user={userBySlug.get(m.responsible_slug)} />
              ))}
            </div>
          )}
        </section>

        {/* HISTÓRICO */}
        {stats && stats.by_responsible.length > 0 && (
          <Card>
            <CardHeader title="Performance da equipe" subtitle="Taxas de conclusão na janela atual" />
            <div className="p-6 grid md:grid-cols-3 gap-4">
              {stats.by_responsible.map((r) => {
                const u = userBySlug.get(r.slug);
                const rate = r.total > 0 ? Math.round((r.done / r.total) * 100) : 0;
                return <PerformanceCard key={r.slug} stat={r} user={u} rate={rate} />;
              })}
            </div>
          </Card>
        )}
      </main>
    </>
  );
}

// ============================================================ Componentes

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden backdrop-blur-sm">
      {children}
    </div>
  );
}

function CardHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
      <div>
        <h3 className="text-base font-semibold text-white">{title}</h3>
        {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

function SectionHeader({
  title,
  subtitle,
  icon: Icon,
  count,
}: {
  title: string;
  subtitle?: string;
  icon?: any;
  count?: number;
}) {
  return (
    <div className="flex items-end justify-between gap-3">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
            <Icon className="w-4.5 h-4.5 text-white/70" />
          </div>
        )}
        <div>
          <h2 className="text-xl font-semibold text-white leading-none">{title}</h2>
          {subtitle && <p className="text-xs text-white/40 mt-1">{subtitle}</p>}
        </div>
        {typeof count === "number" && (
          <span className="ml-1 inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-lg bg-white/[0.06] text-white/70 text-xs font-semibold numeric">
            {count}
          </span>
        )}
      </div>
    </div>
  );
}

function KpiTile({
  icon: Icon,
  label,
  value,
  hint,
  accent,
  iconBg,
}: {
  icon: any;
  label: string;
  value: number;
  hint?: string;
  accent: string;
  iconBg: string;
}) {
  return (
    <div className={`relative rounded-2xl border border-white/[0.06] bg-gradient-to-br ${accent} overflow-hidden group hover:border-white/10 transition-colors`}>
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full opacity-30 blur-2xl bg-white/40" />
      <div className="relative p-5 flex items-center gap-4">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${iconBg}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs uppercase tracking-wider text-white/50">{label}</div>
          <div className="font-stencil text-4xl text-white leading-none mt-1">{value}</div>
          {hint && <div className="text-[11px] text-white/40 mt-1.5">{hint}</div>}
        </div>
      </div>
    </div>
  );
}

function PrincipalColumn({ user, missions }: { user: MissionUser; missions: Mission[] }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.06] bg-white/[0.02]">
        {user.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={user.photo_url}
            alt={user.display_name}
            className="w-11 h-11 rounded-full object-cover ring-2 ring-accent/40"
          />
        ) : (
          <div className="w-11 h-11 rounded-full bg-gradient-to-br from-accent/40 to-accent/10 ring-2 ring-accent/40 flex items-center justify-center font-bold text-white">
            {user.display_name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-semibold text-white">{user.display_name}</div>
          <div className="text-xs text-white/40 mt-0.5">{missions.length} missões ativas</div>
        </div>
        <div className="text-right">
          <div className="font-stencil text-3xl text-white/90 leading-none">{String(missions.length).padStart(2, "0")}</div>
        </div>
      </div>
      <div className="p-3 space-y-2.5">
        {missions.map((m) => <MissionCard key={m.id} mission={m} />)}
      </div>
    </div>
  );
}

function ResponsibleRow({ stat, user }: { stat: ResponsibleStat; user?: MissionUser }) {
  const pct = stat.total > 0 ? Math.round((stat.done / stat.total) * 100) : 0;
  const name = user?.display_name || stat.slug;
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/[0.05] bg-white/[0.02] px-3.5 py-2.5 hover:bg-white/[0.04] transition-colors">
      {user?.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.photo_url} alt={name} className="w-9 h-9 rounded-full object-cover ring-2 ring-white/10" />
      ) : (
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-accent/40 to-accent/10 ring-2 ring-white/10 flex items-center justify-center font-bold text-white text-sm">
          {name[0]}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-3">
          <div className="font-medium text-white text-sm">{name}</div>
          <div className="text-xs text-white/60 numeric">{pct}%</div>
        </div>
        <div className="h-1 bg-white/5 rounded-full mt-1.5 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-accent to-camo-amber rounded-full" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[11px]">
          <Stat label="total" value={stat.total} />
          <Stat label="curso" value={stat.in_progress} tone="text-camo-amber" />
          <Stat label="feita" value={stat.done} tone="text-low" />
          <span className="text-white/15">·</span>
          <Stat label="alta" value={stat.alta} tone="text-urgent" />
          <Stat label="méd" value={stat.media} />
          <Stat label="baixa" value={stat.baixa} />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-white/70" }: { label: string; value: number; tone?: string }) {
  return (
    <span className="flex gap-1">
      <span className="text-white/30">{label}</span>
      <span className={`numeric font-semibold ${tone}`}>{value}</span>
    </span>
  );
}

function KindStat({ icon: Icon, label, value }: { icon: any; label: string; value: number }) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center">
          <Icon className="w-4.5 h-4.5 text-white/70" />
        </div>
        <div>
          <div className="font-stencil text-3xl text-white leading-none">{value}</div>
          <div className="text-xs text-white/40 mt-1">{label}</div>
        </div>
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/[0.05]">
      <div className="flex items-center gap-2">
        <span
          className="inline-block w-2.5 h-2.5 rounded-full"
          style={{ background: color, boxShadow: `0 0 10px ${color}80` }}
        />
        <span className="text-white/70 text-xs">{label}</span>
      </div>
      <span className="numeric font-semibold text-white text-sm">{value}</span>
    </div>
  );
}

function CompletedRow({ mission, user }: { mission: Mission; user?: MissionUser }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-low/15 bg-low/[0.04] px-3.5 py-3 hover:bg-low/[0.08] transition-colors">
      <div className="w-8 h-8 rounded-full bg-low/15 flex items-center justify-center shrink-0">
        <CheckCircle2 className="w-4 h-4 text-low" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-white/85 truncate line-through">{mission.name}</div>
        <div className="text-xs text-white/40 truncate mt-0.5">
          {user?.display_name || mission.responsible_slug}
          {mission.client ? ` · ${mission.client}` : ""}
        </div>
      </div>
    </div>
  );
}

function PerformanceCard({ stat, user, rate }: { stat: ResponsibleStat; user?: MissionUser; rate: number }) {
  const name = user?.display_name || stat.slug;
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5 space-y-4">
      <div className="flex items-center gap-3">
        {user?.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.photo_url} alt={name} className="w-12 h-12 rounded-full object-cover ring-2 ring-white/10" />
        ) : (
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent/40 to-accent/10 ring-2 ring-white/10 flex items-center justify-center font-bold text-white">
            {name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-semibold text-white">{name}</div>
          <div className="text-xs text-white/40 mt-0.5">Taxa de conclusão</div>
        </div>
        <div className="text-right">
          <div className="font-stencil text-3xl text-white leading-none">{rate}%</div>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <MiniStat label="Total" value={stat.total} />
        <MiniStat label="OK" value={stat.done} tone="text-low" />
        <MiniStat label="Curso" value={stat.in_progress} tone="text-camo-amber" />
        <MiniStat label="Alta" value={stat.alta} tone="text-urgent" />
      </div>
    </div>
  );
}

function MiniStat({ label, value, tone = "text-white" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg bg-white/[0.03] border border-white/[0.05] py-2">
      <div className={`font-stencil text-xl leading-none ${tone}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-white/40 mt-1">{label}</div>
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.015] py-12 text-center">
      <div className="text-white/40 text-sm">{message}</div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-urgent/30 bg-urgent/10 px-4 py-3 text-urgent flex items-start gap-3">
      <TriangleAlert className="w-5 h-5 mt-0.5 shrink-0" />
      <div>
        <div className="font-semibold">Falha ao carregar missões</div>
        <div className="text-xs mt-1 text-urgent/80 font-mono">{message}</div>
      </div>
    </div>
  );
}

function groupByResponsible(missions: Mission[], users: MissionUser[]): { user: MissionUser; items: Mission[] }[] {
  const groups = new Map<string, { user: MissionUser; items: Mission[] }>();
  for (const m of missions) {
    const user = users.find((u) => u.slug === m.responsible_slug) || {
      slug: m.responsible_slug,
      display_name: m.responsible_slug,
      photo_url: null,
      accent_color: "#ff5a1f",
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
