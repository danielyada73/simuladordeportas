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
import { Flame, AlertTriangle, Minus, Target, Crosshair, Trophy, History, TriangleAlert } from "lucide-react";

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

      <main className="max-w-[1600px] mx-auto px-6 py-10 space-y-12">
        {/* HERO */}
        <section className="relative flex items-center justify-center py-10">
          <SoldierGlyph side="left" />
          <div className="text-center px-6">
            <div className="text-camo-cyan/60 text-xs uppercase tracking-[0.4em] mb-2">comando central</div>
            <h1 className="font-stencil tracking-[0.15em] text-camo-cyan text-7xl md:text-8xl leading-none drop-shadow-[0_0_25px_rgba(34,211,238,0.25)]">
              MISSÕES <span className="text-camo-amber">DIÁRIAS</span>
            </h1>
            <div className="text-camo-cyan/50 text-xs uppercase tracking-[0.3em] mt-3">{windowLabel(windowKey)}</div>
          </div>
          <SoldierGlyph side="right" />
        </section>

        {error && <ErrorBox message={error} />}

        {/* PAINEL GERAL */}
        {stats && (
          <Section title="Painel Geral" subtitle="Distribuição da operação">
            <div className="grid lg:grid-cols-[auto_1fr] gap-8 items-start">
              {/* Pizza por status */}
              <div className="flex flex-col items-center gap-4">
                <PieChart
                  size={220}
                  centerLabel="Total"
                  slices={[
                    { label: "Concluídas", value: stats.by_status.concluida, color: "#10b981" },
                    { label: "Em curso", value: stats.by_status.em_progresso, color: "#fbbf24" },
                    { label: "Abertas", value: stats.by_status.nao_iniciada, color: "#22d3ee" },
                  ]}
                />
                <div className="flex flex-wrap justify-center gap-3 text-[11px] uppercase tracking-wider">
                  <Legend color="#10b981" label="Concluídas" value={stats.by_status.concluida} />
                  <Legend color="#fbbf24" label="Em curso" value={stats.by_status.em_progresso} />
                  <Legend color="#22d3ee" label="Abertas" value={stats.by_status.nao_iniciada} />
                </div>
              </div>

              {/* Por responsável */}
              <div className="space-y-3">
                <div className="text-xs uppercase tracking-widest text-camo-cyan/60">Por responsável</div>
                {stats.by_responsible.length === 0 ? (
                  <div className="text-camo-cyan/40 text-sm">Nenhuma missão no escopo.</div>
                ) : (
                  stats.by_responsible.map((r) => (
                    <ResponsibleRow key={r.slug} stat={r} user={userBySlug.get(r.slug)} />
                  ))
                )}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-camo-line">
                  <KindStat icon={Target} label="Principais" value={stats.by_kind.principal} />
                  <KindStat icon={Crosshair} label="Secundárias" value={stats.by_kind.secundaria} />
                </div>
              </div>
            </div>
          </Section>
        )}

        {/* MISSÕES PRINCIPAIS */}
        <Section title="Missões Principais" subtitle="Alvo prioritário, alta atenção">
          {principais.length === 0 ? (
            <EmptyPanel message="Nenhuma missão principal nessa janela" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-6">
              {groupByResponsible(principais, users).map(({ user, items }) => (
                <PrincipalColumn key={user.slug} user={user} missions={items} />
              ))}
            </div>
          )}
        </Section>

        {/* MISSÕES SECUNDÁRIAS */}
        <Section title="Missões Secundárias" subtitle="Apoio operacional">
          {secundarias.length === 0 ? (
            <EmptyPanel message="Nada secundário nessa janela" />
          ) : (
            <div className="grid lg:grid-cols-2 gap-x-6 gap-y-2">
              {secundarias.map((m) => (
                <MissionCard key={m.id} mission={m} compact />
              ))}
            </div>
          )}
        </Section>

        {/* CONCLUÍDAS */}
        <Section title="Missões Cumpridas" subtitle="Histórico do dia" icon={Trophy}>
          {concluidas.length === 0 ? (
            <EmptyPanel message="Nenhuma missão cumprida ainda. Bora?" />
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

function Section({
  title,
  subtitle,
  icon: Icon,
  children,
}: {
  title: string;
  subtitle?: string;
  icon?: any;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-5">
      <div className="flex items-end justify-between border-b border-camo-line pb-3">
        <div>
          <div className="flex items-center gap-2.5">
            {Icon && <Icon className="w-5 h-5 text-camo-cyan" />}
            <h2 className="font-stencil text-3xl tracking-widest text-camo-cyan">{title.toUpperCase()}</h2>
          </div>
          {subtitle && <div className="text-xs uppercase tracking-wider text-camo-cyan/40 mt-1">{subtitle}</div>}
        </div>
        <div className="hidden md:block text-[10px] tracking-[0.3em] text-camo-cyan/30">SETOR ▸ {title.slice(0, 3).toUpperCase()}</div>
      </div>
      {children}
    </section>
  );
}

function PrincipalColumn({ user, missions }: { user: MissionUser; missions: Mission[] }) {
  return (
    <div className="border border-camo-line bg-camo-base/40 backdrop-blur-sm">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-camo-line bg-camo-mid/20">
        {user.photo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.photo_url} alt={user.display_name} className="w-10 h-10 rounded-full object-cover border-2 border-camo-cyan/50" />
        ) : (
          <div className="w-10 h-10 rounded-full bg-camo-mid border-2 border-camo-cyan/50 flex items-center justify-center font-stencil text-camo-cyan text-xl">
            {user.display_name[0]}
          </div>
        )}
        <div className="flex-1">
          <div className="font-stencil text-xl tracking-wider text-camo-cyan leading-none">{user.display_name.toUpperCase()}</div>
          <div className="text-[10px] uppercase tracking-widest text-camo-cyan/50 mt-1">{missions.length} missões ativas</div>
        </div>
        <div className="font-stencil text-3xl text-camo-cyan/70 leading-none">{String(missions.length).padStart(2, "0")}</div>
      </div>
      <div className="p-3 space-y-3">
        {missions.map((m) => <MissionCard key={m.id} mission={m} />)}
      </div>
    </div>
  );
}

function ResponsibleRow({ stat, user }: { stat: ResponsibleStat; user?: MissionUser }) {
  const pct = stat.total > 0 ? Math.round((stat.done / stat.total) * 100) : 0;
  const name = user?.display_name || stat.slug;
  return (
    <div className="flex items-center gap-4 border border-camo-line bg-camo-deep/40 px-4 py-3">
      {user?.photo_url ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={user.photo_url} alt={name} className="w-12 h-12 rounded-full object-cover border-2 border-camo-cyan/50" />
      ) : (
        <div className="w-12 h-12 rounded-full bg-camo-mid border-2 border-camo-cyan/50 flex items-center justify-center font-stencil text-camo-cyan text-lg">
          {name[0]}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between">
          <div className="font-stencil text-xl tracking-wider text-camo-cyan">{name.toUpperCase()}</div>
          <div className="text-xs text-camo-cyan/50 numeric">{pct}%</div>
        </div>
        <div className="h-1 bg-camo-line rounded-full overflow-hidden mt-1.5">
          <div className="h-full bg-gradient-to-r from-camo-cyan to-camo-amber" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex flex-wrap gap-3 mt-2 text-[10px] uppercase tracking-wider text-camo-cyan/60">
          <Stat label="Total" value={stat.total} />
          <Stat label="Curso" value={stat.in_progress} tone="text-camo-amber" />
          <Stat label="Feita" value={stat.done} tone="text-low" />
          <span className="text-camo-line">·</span>
          <Stat label="Alta" value={stat.alta} tone="text-urgent" />
          <Stat label="Méd" value={stat.media} />
          <Stat label="Baixa" value={stat.baixa} />
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
    <div className="border border-camo-line bg-camo-deep/40 p-3 flex items-center gap-3">
      <Icon className="w-4 h-4 text-camo-cyan" />
      <div className="flex-1">
        <div className="text-[10px] uppercase tracking-wider text-camo-cyan/50">{label}</div>
        <div className="font-stencil text-2xl text-camo-cyan leading-none">{value}</div>
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <span className="flex items-center gap-1.5 text-camo-cyan/70">
      <span className="inline-block w-2.5 h-2.5" style={{ background: color }} />
      <span>{label}</span>
      <span className="numeric text-text font-semibold">{value}</span>
    </span>
  );
}

function CompletedRow({ mission, user }: { mission: Mission; user?: MissionUser }) {
  return (
    <div className="flex items-center gap-3 border border-low/30 bg-low/5 px-3 py-2">
      <div className="w-7 h-7 rounded-full bg-low/20 border border-low/40 flex items-center justify-center">
        <svg viewBox="0 0 24 24" className="w-4 h-4 text-low" fill="none" stroke="currentColor" strokeWidth="3">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-text truncate line-through opacity-80">{mission.name}</div>
        <div className="text-[10px] uppercase tracking-wider text-camo-cyan/40">
          {user?.display_name || mission.responsible_slug} {mission.client ? `· ${mission.client}` : ""}
        </div>
      </div>
    </div>
  );
}

function HistoryFooter({ stats, users }: { stats: MissionsStats; users: MissionUser[] }) {
  const userBySlug = new Map(users.map((u) => [u.slug, u]));
  return (
    <section className="border border-camo-line bg-camo-base/30 p-6 mt-12">
      <div className="flex items-center gap-2.5 mb-5">
        <History className="w-5 h-5 text-camo-cyan" />
        <h2 className="font-stencil text-2xl tracking-widest text-camo-cyan">HISTÓRICO DA JANELA</h2>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        {stats.by_responsible.length === 0 ? (
          <div className="col-span-full text-camo-cyan/40 text-sm">Sem registros nessa janela.</div>
        ) : (
          stats.by_responsible.map((r) => {
            const u = userBySlug.get(r.slug);
            const rate = r.total > 0 ? Math.round((r.done / r.total) * 100) : 0;
            return (
              <div key={r.slug} className="border border-camo-line bg-camo-deep/50 p-4 space-y-2">
                <div className="flex items-center gap-3">
                  {u?.photo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={u.photo_url} alt={u.display_name} className="w-9 h-9 rounded-full object-cover border border-camo-cyan/40" />
                  ) : (
                    <div className="w-9 h-9 rounded-full bg-camo-mid border border-camo-cyan/40 flex items-center justify-center font-stencil text-camo-cyan">
                      {(u?.display_name || r.slug)[0]}
                    </div>
                  )}
                  <div>
                    <div className="font-stencil text-lg tracking-wider text-camo-cyan">{(u?.display_name || r.slug).toUpperCase()}</div>
                    <div className="text-[10px] uppercase tracking-wider text-camo-cyan/50">Taxa de conclusão {rate}%</div>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-2 text-center pt-2">
                  <Mini label="Tot" value={r.total} />
                  <Mini label="OK" value={r.done} tone="text-low" />
                  <Mini label="Curso" value={r.in_progress} tone="text-camo-amber" />
                  <Mini label="Alta" value={r.alta} tone="text-urgent" />
                </div>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

function Mini({ label, value, tone = "text-camo-cyan" }: { label: string; value: number; tone?: string }) {
  return (
    <div>
      <div className={`font-stencil text-xl leading-none ${tone}`}>{value}</div>
      <div className="text-[9px] uppercase tracking-widest text-camo-cyan/40 mt-1">{label}</div>
    </div>
  );
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <div className="border border-dashed border-camo-line bg-camo-deep/30 py-12 text-center">
      <div className="font-stencil text-xl tracking-widest text-camo-cyan/40">{message.toUpperCase()}</div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="border border-urgent/40 bg-urgent/10 px-4 py-3 text-urgent flex items-start gap-3">
      <TriangleAlert className="w-5 h-5 mt-0.5 shrink-0" />
      <div>
        <div className="font-stencil tracking-widest text-lg">FALHA DE CONEXÃO</div>
        <div className="text-xs mt-1 text-urgent/80">{message}</div>
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

function SoldierGlyph({ side }: { side: "left" | "right" }) {
  // Silhueta estilizada de soldado em SVG (subido em cima do hero)
  return (
    <svg
      viewBox="0 0 100 140"
      className={`w-20 md:w-28 h-auto text-camo-cyan/40 hidden md:block ${side === "right" ? "scale-x-[-1]" : ""}`}
      fill="currentColor"
      aria-hidden
    >
      {/* Capacete */}
      <path d="M30 25 Q30 12 50 12 Q70 12 70 25 L72 32 L28 32 Z" />
      <rect x="25" y="32" width="50" height="4" />
      {/* Cabeça */}
      <circle cx="50" cy="42" r="6" />
      {/* Tronco */}
      <path d="M35 50 L65 50 L70 90 L60 92 L55 70 L50 95 L45 70 L40 92 L30 90 Z" />
      {/* Braço c/ arma */}
      <rect x="18" y="55" width="14" height="6" />
      <rect x="10" y="58" width="20" height="3" />
      {/* Pernas */}
      <rect x="38" y="92" width="8" height="35" />
      <rect x="54" y="92" width="8" height="35" />
      <rect x="36" y="125" width="12" height="6" />
      <rect x="52" y="125" width="12" height="6" />
    </svg>
  );
}
