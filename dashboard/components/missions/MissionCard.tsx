import { Flame, AlertTriangle, Minus, Calendar } from "lucide-react";
import { StatusControl } from "./StatusControl";
import type { Mission } from "@/lib/missions-types";

const PRIO = {
  alta: { Icon: Flame, dotColor: "bg-urgent", chip: "bg-urgent/15 text-urgent border-urgent/25" },
  media: { Icon: AlertTriangle, dotColor: "bg-camo-amber", chip: "bg-camo-amber/15 text-camo-amber border-camo-amber/25" },
  baixa: { Icon: Minus, dotColor: "bg-camo-cyan", chip: "bg-camo-cyan/15 text-camo-cyan border-camo-cyan/25" },
} as const;

function fmtDate(iso: string): { d: string; m: string; overdue: boolean } {
  if (!iso) return { d: "—", m: "", overdue: false };
  const [, mo, da] = iso.split("-");
  const date = new Date(`${iso}T12:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  return { d: da, m: months[parseInt(mo, 10) - 1], overdue: date < today };
}

export function MissionCard({ mission, compact = false }: { mission: Mission; compact?: boolean }) {
  const prio = PRIO[mission.priority] || PRIO.media;
  const PrioIcon = prio.Icon;
  const date = fmtDate(mission.due_date);
  const isDone = mission.status === "concluida";

  if (compact) {
    return (
      <div className={`group flex items-center gap-3 px-3.5 py-2.5 rounded-xl border border-white/[0.06] bg-white/[0.025] hover:bg-white/[0.045] hover:border-white/10 transition-all ${isDone ? "opacity-50" : ""}`}>
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${prio.dotColor}`} />
        <div className="flex-1 min-w-0">
          <div className={`text-sm font-medium truncate ${isDone ? "line-through text-white/40" : "text-white/90"}`}>
            {mission.name}
          </div>
          <div className="text-xs text-white/40 truncate mt-0.5">
            {mission.client || "Sem cliente"}
          </div>
        </div>
        <div className={`text-xs numeric shrink-0 ${date.overdue && !isDone ? "text-urgent" : "text-white/50"}`}>
          {date.d} {date.m}
        </div>
        <StatusControl id={mission.id} status={mission.status} />
      </div>
    );
  }

  return (
    <div className={`group relative rounded-2xl border border-white/[0.06] bg-white/[0.025] hover:bg-white/[0.04] hover:border-white/10 transition-all overflow-hidden ${isDone ? "opacity-70" : ""}`}>
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-semibold uppercase tracking-wider ${prio.chip}`}>
                <PrioIcon className="w-2.5 h-2.5" />
                {mission.priority}
              </span>
              {mission.client && (
                <span className="text-[11px] text-white/40 truncate">{mission.client}</span>
              )}
            </div>
            <h4 className={`font-medium leading-snug text-[15px] ${isDone ? "line-through text-white/40" : "text-white/95"}`}>
              {mission.name}
            </h4>
          </div>
        </div>

        {mission.notes && (
          <p className="text-xs text-white/50 border-l-2 border-white/10 pl-2.5 italic">{mission.notes}</p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <div className={`flex items-center gap-1.5 text-xs ${date.overdue && !isDone ? "text-urgent" : "text-white/50"}`}>
            <Calendar className="w-3.5 h-3.5" />
            <span className="numeric">{date.d} {date.m}</span>
          </div>
          <StatusControl id={mission.id} status={mission.status} />
        </div>
      </div>
    </div>
  );
}
