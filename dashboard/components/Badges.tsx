import { Flame, AlertTriangle, Circle, Minus, CircleCheck, Loader, CircleDashed } from "lucide-react";

function priorityStyle(value: string) {
  const v = (value || "").toLowerCase().trim();
  if (v === "urgente" || v === "critico" || v === "crítico" || v === "critica")
    return { cls: "bg-urgent/15 text-urgent border-urgent/30", Icon: Flame };
  if (v === "alta")
    return { cls: "bg-high/15 text-high border-high/30", Icon: AlertTriangle };
  if (v === "media" || v === "média")
    return { cls: "bg-medium/15 text-medium border-medium/30", Icon: Circle };
  if (v === "baixa")
    return { cls: "bg-low/15 text-low border-low/30", Icon: Minus };
  return { cls: "bg-border text-muted border-border", Icon: Circle };
}

export function PriorityBadge({ value }: { value: string }) {
  if (!value) return <span className="text-muted text-xs">—</span>;
  const { cls, Icon } = priorityStyle(value);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs border font-medium ${cls}`}>
      <Icon className="w-3 h-3" />
      {value}
    </span>
  );
}

function statusStyle(value: string) {
  const v = (value || "").toLowerCase().trim();
  if (["feito", "concluido", "concluído", "done", "completed", "finalizado"].includes(v))
    return { cls: "bg-done/15 text-done border-done/30", Icon: CircleCheck };
  if (["em progresso", "em andamento", "in progress", "trabalhando"].includes(v))
    return { cls: "bg-progress/15 text-progress border-progress/30", Icon: Loader };
  return { cls: "bg-border text-muted-strong border-border", Icon: CircleDashed };
}

export function StatusBadge({ value }: { value: string }) {
  const display = value || "Aberta";
  const { cls, Icon } = statusStyle(value);
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs border font-medium ${cls}`}>
      <Icon className="w-3 h-3" />
      {display}
    </span>
  );
}

const HEALTH = {
  green: { dot: "bg-low", ring: "ring-low/30", label: "OK" },
  yellow: { dot: "bg-progress", ring: "ring-progress/30", label: "Em estrutura" },
  red: { dot: "bg-urgent", ring: "ring-urgent/30", label: "Crítico" },
};

export function HealthDot({ health }: { health: "green" | "yellow" | "red" }) {
  const h = HEALTH[health];
  return <span className={`inline-block w-2 h-2 rounded-full ring-4 ${h.dot} ${h.ring}`} />;
}

export function HealthBadge({ health }: { health: "green" | "yellow" | "red" }) {
  const h = HEALTH[health];
  return (
    <span className="inline-flex items-center gap-2 text-xs">
      <span className={`w-1.5 h-1.5 rounded-full ${h.dot}`} />
      <span className="text-muted-strong">{h.label}</span>
    </span>
  );
}

export function Avatar({ name, size = 28 }: { name: string; size?: number }) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  const palette = ["from-medium to-accent", "from-low to-medium", "from-high to-urgent", "from-accent to-high"];
  const idx = (name.charCodeAt(0) || 0) % palette.length;
  return (
    <div
      className={`inline-flex items-center justify-center rounded-full bg-gradient-to-br ${palette[idx]} text-white font-semibold ring-2 ring-bg`}
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      title={name}
    >
      {initials || "?"}
    </div>
  );
}

export function AvatarGroup({ names }: { names: string[] }) {
  if (!names || names.length === 0) return <span className="text-muted text-xs">—</span>;
  const display = names.slice(0, 3);
  const extra = names.length - display.length;
  return (
    <div className="flex items-center -space-x-2">
      {display.map((n) => (
        <Avatar key={n} name={n} size={26} />
      ))}
      {extra > 0 && (
        <div className="w-[26px] h-[26px] rounded-full bg-surface border border-border flex items-center justify-center text-[10px] text-muted-strong">
          +{extra}
        </div>
      )}
    </div>
  );
}
