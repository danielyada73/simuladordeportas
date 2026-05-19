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
  History,
  TriangleAlert,
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

  const now = new Date();
  const opCode = `OPS-${String(now.getFullYear()).slice(2)}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}Z`;

  return (
    <>
      <MissoesHeader users={users} settings={settings} />

      <main className="max-w-[1500px] mx-auto px-6 py-8 space-y-10">
        {/* Classified stripe */}
        <ClassifiedStripe opCode={opCode} window={windowKey} />

        {/* HERO */}
        <section className="relative py-8">
          <CornerBrackets />
          <div className="relative text-center">
            <div className="inline-flex items-center gap-3 text-camo-amber text-[10px] tracking-[0.5em] uppercase mb-3">
              <span className="w-8 h-px bg-camo-amber/60" />
              Comando Central · Alpha
              <span className="w-8 h-px bg-camo-amber/60" />
            </div>
            <h1 className="font-stencil tracking-[0.18em] text-camo-cyan text-7xl md:text-8xl lg:text-[8rem] leading-[0.85] relative">
              MISSÕES
              <span className="block text-camo-amber/95 text-5xl md:text-6xl lg:text-7xl mt-2 tracking-[0.22em]">
                DIÁRIAS
              </span>
            </h1>
            <div className="mt-6 flex items-center justify-center gap-6 text-[10px] uppercase tracking-[0.3em] text-camo-cyan/50 font-mono">
              <span>// {windowLabel(windowKey)}</span>
              <span className="w-1 h-1 bg-camo-cyan/40 rounded-full" />
              <span>// {opCode}</span>
              <span className="w-1 h-1 bg-camo-cyan/40 rounded-full" />
              <span>// {stats?.total ?? 0} ALVOS</span>
            </div>
          </div>
        </section>

        {error && <ErrorBox message={error} />}

        {/* PAINEL GERAL */}
        {stats && (
          <Section title="Painel Geral" subtitle="Distribuição operacional" code="01">
            <div className="grid lg:grid-cols-[280px_1fr] gap-8 items-start">
              {/* Pizza com anéis tipo radar */}
              <div className="flex flex-col items-center">
                <div className="relative">
                  <RadarRings size={260} />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <PieChart
                      size={200}
                      centerLabel="Total"
                      slices={[
                        { label: "Concluídas", value: stats.by_status.concluida, color: "#10b981" },
                        { label: "Em curso", value: stats.by_status.em_progresso, color: "#fbbf24" },
                        { label: "Abertas", value: stats.by_status.nao_iniciada, color: "#22d3ee" },
                      ]}
                    />
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-1 gap-1.5 text-[10px] uppercase tracking-widest w-full">
                  <Legend color="#10b981" label="Concluídas" value={stats.by_status.concluida} />
                  <Legend color="#fbbf24" label="Em curso" value={stats.by_status.em_progresso} />
                  <Legend color="#22d3ee" label="Abertas" value={stats.by_status.nao_iniciada} />
                </div>
              </div>

              {/* Lado direito: tipos + responsáveis */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <KindStat icon={Target} label="Missões Principais" value={stats.by_kind.principal} />
                  <KindStat icon={Crosshair} label="Secundárias" value={stats.by_kind.secundaria} />
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-[0.3em] text-camo-cyan/50 mb-2 flex items-center gap-2">
                    <span className="w-4 h-px bg-camo-cyan/40" />
                    Operadores em campo
                  </div>
                  <div className="space-y-2.5">
                    {stats.by_responsible.length === 0 ? (
                      <div className="text-camo-cyan/40 text-sm font-mono">// nenhum operador alocado</div>
                    ) : (
                      stats.by_responsible.map((r) => (
                        <ResponsibleRow key={r.slug} stat={r} user={userBySlug.get(r.slug)} />
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </Section>
        )}

        {/* MISSÕES PRINCIPAIS */}
        <Section title="Missões Principais" subtitle="Alvos prioritários" code="02" stamp="ATIVAS">
          {principais.length === 0 ? (
            <EmptyPanel message="Nenhuma missão principal ativa" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-5">
              {groupByResponsible(principais, users).map(({ user, items }) => (
                <PrincipalColumn key={user.slug} user={user} missions={items} />
              ))}
            </div>
          )}
        </Section>

        {/* SECUNDÁRIAS */}
        <Section title="Missões Secundárias" subtitle="Apoio operacional" code="03">
          {secundarias.length === 0 ? (
            <EmptyPanel message="Nada secundário no momento" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-x-5 gap-y-2">
              {secundarias.map((m) => (
                <MissionCard key={m.id} mission={m} compact />
              ))}
            </div>
          )}
        </Section>

        {/* CONCLUÍDAS */}
        <Section title="Missões Cumpridas" subtitle="Confirmadas" code="04" icon={Trophy} stamp="CONCLUÍDAS">
          {concluidas.length === 0 ? (
            <EmptyPanel message="Nenhuma missão cumprida ainda" />
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {concluidas.map((m) => (
                <CompletedRow key={m.id} mission={m} user={userBySlug.get(m.responsible_slug)} />
              ))}
            </div>
          )}
        </Section>

        {/* HISTÓRICO */}
        {stats && <HistoryFooter stats={stats} users={users} />}
      </main>
    </>
  );
}

// ============================================================ Sub-componentes

function ClassifiedStripe({ opCode, window }: { opCode: string; window: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-[10px] font-mono uppercase tracking-[0.25em] text-camo-amber/80 border-y border-camo-amber/30 py-1.5">
      <div className="flex items-center gap-2">
        <span className="inline-block w-2 h-2 bg-camo-amber/80 animate-pulse" />
        <span>// CLASSIFIED — ALPHA TEAM EYES ONLY</span>
      </div>
      <div className="hidden md:flex items-center gap-4 text-camo-cyan/60">
        <span>{opCode}</span>
        <span>// {window.toUpperCase()}</span>
      </div>
    </div>
  );
}

function CornerBrackets() {
  return (
    <>
      <div className="absolute top-2 left-2 w-8 h-8 border-t-2 border-l-2 border-camo-cyan/40" />
      <div className="absolute top-2 right-2 w-8 h-8 border-t-2 border-r-2 border-camo-cyan/40" />
      <div className="absolute bottom-2 left-2 w-8 h-8 border-b-2 border-l-2 border-camo-cyan/40" />
      <div className="absolute bottom-2 right-2 w-8 h-8 border-b-2 border-r-2 border-camo-cyan/40" />
    </>
  );
}

function RadarRings({ size }: { size: number }) {
  const cx = size / 2;
  const cy = size / 2;
  return (
    <svg width={size} height={size} className="absolute inset-0">
      <g fill="none" stroke="#22d3ee" strokeOpacity="0.18">
        <circle cx={cx} cy={cy} r={size / 2 - 4} strokeDasharray="2 6" />
        <circle cx={cx} cy={cy} r={size / 2 - 18} strokeDasharray="1 4" strokeOpacity="0.12" />
        <line x1={cx} y1={6} x2={cx} y2={size - 6} strokeOpacity="0.08" />
        <line x1={6} y1={cy} x2={size - 6} y2={cy} strokeOpacity="0.08" />
      </g>
      {/* Marcadores cardeais */}
      <g fill="#22d3ee" opacity="0.4" fontSize="9" fontFamily="JetBrains Mono, monospace">
        <text x={cx} y={14} textAnchor="middle">N</text>
        <text x={cx} y={size - 4} textAnchor="middle">S</text>
        <text x={6} y={cy + 4} textAnchor="start">W</text>
        <text x={size - 6} y={cy + 4} textAnchor="end">E</text>
      </g>
    </svg>
  );
}

function Section({
  title,
  subtitle,
  code,
  icon: Icon,
  stamp,
  children,
}: {
  title: string;
  subtitle?: string;
  code?: string;
  icon?: any;
  stamp?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="relative">
      {/* Header da seção */}
      <div className="flex items-end justify-between border-b border-camo-line pb-3 mb-5">
        <div className="flex items-end gap-4">
          {code && (
            <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-camo-cyan/40 mb-1">
              ▸ SEÇÃO {code}
            </div>
          )}
          <div>
            <div className="flex items-center gap-2.5">
              {Icon && <Icon className="w-5 h-5 text-camo-cyan" />}
              <h2 className="font-stencil text-3xl md:text-4xl tracking-[0.15em] text-camo-cyan leading-none">
                {title.toUpperCase()}
              </h2>
            </div>
            {subtitle && (
              <div className="text-[10px] uppercase tracking-[0.25em] text-camo-cyan/40 mt-1.5 font-mono">
                // {subtitle.toLowerCase()}
              </div>
            )}
          </div>
        </div>
        {stamp && (
          <div className="hidden md:flex items-center gap-2 px-2.5 py-1 border border-camo-amber/50 text-camo-amber text-[9px] font-stencil tracking-[0.3em] -rotate-2">
            <span className="w-1.5 h-1.5 bg-camo-amber rounded-full animate-pulse" />
            {stamp}
          </div>
        )}
      </div>
      {children}
    </section>
  );
}

function PrincipalColumn({ user, missions }: { user: MissionUser; missions: Mission[] }) {
  return (
    <div className="relative border border-camo-line bg-camo-base/30 backdrop-blur-sm">
      <CornerBrackets />
      <div className="flex items-center gap-3 px-4 py-3 border-b border-camo-line bg-camo-mid/20">
        {user.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.photo_url} alt={user.display_name} className="w-11 h-11 rounded-full object-cover border-2 border-camo-cyan/50" />
        ) : (
          <div className="w-11 h-11 rounded-full bg-camo-mid border-2 border-camo-cyan/50 flex items-center justify-center font-stencil text-camo-cyan text-xl">
            {user.display_name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-stencil text-xl tracking-[0.15em] text-camo-cyan leading-none">
            {user.display_name.toUpperCase()}
          </div>
          <div className="text-[10px] uppercase tracking-[0.25em] text-camo-cyan/50 mt-1 font-mono">
            // {missions.length} alvos ativos
          </div>
        </div>
        <div className="text-right">
          <div className="font-stencil text-4xl text-camo-cyan/80 leading-none">
            {String(missions.length).padStart(2, "0")}
          </div>
          <div className="text-[9px] uppercase tracking-[0.3em] text-camo-cyan/40 mt-0.5">UNITS</div>
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
    <div className="flex items-center gap-3 border border-camo-line bg-camo-deep/50 px-3 py-2.5 hover:border-camo-cyan/40 transition-colors">
      {user?.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.photo_url} alt={name} className="w-10 h-10 rounded-full object-cover border-2 border-camo-cyan/50" />
      ) : (
        <div className="w-10 h-10 rounded-full bg-camo-mid border-2 border-camo-cyan/50 flex items-center justify-center font-stencil text-camo-cyan">
          {name[0]}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-3">
          <div className="font-stencil text-base md:text-lg tracking-[0.15em] text-camo-cyan">
            {name.toUpperCase()}
          </div>
          <div className="text-xs text-camo-cyan/60 font-mono numeric">{pct}%</div>
        </div>
        <div className="h-[2px] bg-camo-line mt-1 overflow-hidden">
          <div className="h-full bg-gradient-to-r from-camo-cyan to-camo-amber" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1.5 text-[10px] uppercase tracking-wider font-mono">
          <Stat label="tot" value={stat.total} />
          <Stat label="curso" value={stat.in_progress} tone="text-camo-amber" />
          <Stat label="feita" value={stat.done} tone="text-low" />
          <span className="text-camo-line">·</span>
          <Stat label="alta" value={stat.alta} tone="text-urgent" />
          <Stat label="méd" value={stat.media} />
          <Stat label="baixa" value={stat.baixa} />
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-camo-cyan" }: { label: string; value: number; tone?: string }) {
  return (
    <span className="flex gap-1">
      <span className="text-camo-cyan/40">{label}</span>
      <span className={`numeric font-semibold ${tone}`}>{value}</span>
    </span>
  );
}

function KindStat({ icon: Icon, label, value }: { icon: any; label: string; value: number }) {
  return (
    <div className="relative border border-camo-line bg-camo-deep/50 p-4">
      <div className="absolute top-1.5 right-1.5 text-[9px] font-mono tracking-wider text-camo-cyan/30">
        {label.startsWith("Mis") ? "PRI" : "SEC"}
      </div>
      <div className="flex items-center gap-3">
        <div className="p-2 bg-camo-mid/40 border border-camo-line">
          <Icon className="w-5 h-5 text-camo-cyan" />
        </div>
        <div>
          <div className="font-stencil text-3xl text-camo-cyan leading-none">{value}</div>
          <div className="text-[10px] uppercase tracking-[0.25em] text-camo-cyan/50 mt-1">{label}</div>
        </div>
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-2 px-2 py-1 border border-camo-line bg-camo-deep/40">
      <div className="flex items-center gap-2">
        <span className="inline-block w-2 h-2" style={{ background: color, boxShadow: `0 0 8px ${color}80` }} />
        <span className="text-camo-cyan/70">{label}</span>
      </div>
      <span className="numeric text-text font-semibold">{value}</span>
    </div>
  );
}

function CompletedRow({ mission, user }: { mission: Mission; user?: MissionUser }) {
  return (
    <div className="relative flex items-center gap-3 border border-low/30 bg-low/[0.06] px-3 py-2.5">
      <div className="absolute top-0 left-0 h-full w-0.5 bg-low" />
      <div className="w-7 h-7 rounded-full bg-low/20 border border-low/40 flex items-center justify-center shrink-0">
        <svg viewBox="0 0 24 24" className="w-4 h-4 text-low" fill="none" stroke="currentColor" strokeWidth="3">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-text/80 truncate line-through">{mission.name}</div>
        <div className="text-[10px] uppercase tracking-[0.2em] text-camo-cyan/40 font-mono">
          // {user?.display_name || mission.responsible_slug}
          {mission.client ? ` · ${mission.client}` : ""}
        </div>
      </div>
    </div>
  );
}

function HistoryFooter({ stats, users }: { stats: MissionsStats; users: MissionUser[] }) {
  const userBySlug = new Map(users.map((u) => [u.slug, u]));
  return (
    <Section title="Histórico" subtitle="Performance no escopo" code="05" icon={History}>
      <div className="grid md:grid-cols-3 gap-4">
        {stats.by_responsible.length === 0 ? (
          <div className="col-span-full text-camo-cyan/40 text-sm font-mono">// sem registros</div>
        ) : (
          stats.by_responsible.map((r) => {
            const u = userBySlug.get(r.slug);
            const rate = r.total > 0 ? Math.round((r.done / r.total) * 100) : 0;
            return (
              <div key={r.slug} className="relative border border-camo-line bg-camo-deep/50 p-4 space-y-3">
                <CornerBrackets />
                <div className="flex items-center gap-3">
                  {u?.photo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={u.photo_url} alt={u.display_name} className="w-10 h-10 rounded-full object-cover border border-camo-cyan/40" />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-camo-mid border border-camo-cyan/40 flex items-center justify-center font-stencil text-camo-cyan">
                      {(u?.display_name || r.slug)[0]}
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="font-stencil text-lg tracking-[0.15em] text-camo-cyan leading-none">
                      {(u?.display_name || r.slug).toUpperCase()}
                    </div>
                    <div className="text-[10px] uppercase tracking-[0.25em] text-camo-cyan/50 mt-1 font-mono">
                      // taxa {rate}%
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-1.5">
                  <Mini label="tot" value={r.total} />
                  <Mini label="ok" value={r.done} tone="text-low" />
                  <Mini label="curso" value={r.in_progress} tone="text-camo-amber" />
                  <Mini label="alta" value={r.alta} tone="text-urgent" />
                </div>
              </div>
            );
          })
        )}
      </div>
    </Section>
  );
}

function Mini({ label, value, tone = "text-camo-cyan" }: { label: string; value: number; tone?: string }) {
  return (
    <div className="border border-camo-line/60 bg-camo-base/40 px-2 py-1.5 text-center">
      <div className={`font-stencil text-xl leading-none ${tone}`}>{value}</div>
      <div className="text-[9px] uppercase tracking-[0.25em] text-camo-cyan/40 mt-1 font-mono">{label}</div>
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="relative border border-dashed border-camo-line/60 bg-camo-deep/20 py-10 text-center">
      <CornerBrackets />
      <div className="font-stencil text-base tracking-[0.3em] text-camo-cyan/40">
        // {message.toUpperCase()}
      </div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="border border-urgent/40 bg-urgent/10 px-4 py-3 text-urgent flex items-start gap-3">
      <TriangleAlert className="w-5 h-5 mt-0.5 shrink-0" />
      <div>
        <div className="font-stencil tracking-[0.15em] text-lg">FALHA DE CONEXÃO</div>
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
      accent_color: "#22d3ee",
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
    today: "hoje",
    tomorrow: "amanhã",
    overdue: "atrasadas",
    week: "próximos 7 dias",
    month: "próximos 30 dias",
    all: "todas",
    custom: "intervalo customizado",
  };
  return (m[w] || w).toUpperCase();
}
