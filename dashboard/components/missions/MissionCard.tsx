import { Flame, AlertTriangle, Minus, Clock, Calendar } from "lucide-react";
import { StatusControl } from "./StatusControl";
import type { Mission } from "@/lib/missions-types";

const PRIO = {
  alta: { Icon: Flame, color: "text-urgent border-urgent/40 bg-urgent/10" },
  media: { Icon: AlertTriangle, color: "text-camo-amber border-camo-amber/40 bg-camo-amber/10" },
  baixa: { Icon: Minus, color: "text-camo-cyan border-camo-cyan/40 bg-camo-cyan/10" },
} as const;

function fmtDate(iso: string): { d: string; m: string; overdue: boolean } {
  if (!iso) return { d: "—", m: "", overdue: false };
  const [y, mo, da] = iso.split("-");
  const date = new Date(`${iso}T12:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const months = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  return { d: da, m: months[parseInt(mo, 10) - 1], overdue: date < today };
}

export function MissionCard({ mission, compact = false }: { mission: Mission; compact?: boolean }) {
  const prio = PRIO[mission.priority] || PRIO.media;
  const PrioIcon = prio.Icon;
  const date = fmtDate(mission.due_date);
  const isDone = mission.status === "concluida";

  if (compact) {
    return (
      <div className={`group flex items-center gap-3 px-3 py-2 border border-camo-line bg-camo-deep/40 hover:border-camo-cyan/30 transition-colors ${isDone ? "opacity-60" : ""}`}>
        <PrioIcon className={`w-3.5 h-3.5 shrink-0 ${prio.color.split(" ")[0]}`} />
        <div className="flex-1 min-w-0">
          <div className={`text-sm text-text truncate ${isDone ? "line-through text-camo-cyan/50" : ""}`}>
            {mission.name}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-camo-cyan/40">
            {mission.client || "—"}
          </div>
        </div>
        <div className={`text-xs numeric ${date.overdue && !isDone ? "text-urgent" : "text-camo-cyan/70"}`}>
          {date.d} {date.m}
        </div>
        <StatusControl id={mission.id} status={mission.status} />
      </div>
    );
  }

  return (
    <div className={`group relative border border-camo-line bg-camo-deep/60 hover:border-camo-cyan/40 transition-all ${isDone ? "opacity-70" : ""}`}>
      {/* Cinta lateral colorida (prioridade) */}
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${mission.priority === "alta" ? "bg-urgent" : mission.priority === "media" ? "bg-camo-amber" : "bg-camo-cyan"}`} />

      <div className="p-4 pl-5 space-y-3">
        <div className="flex items-start gap-3">
          <div className={`shrink-0 px-2 py-0.5 border text-[10px] uppercase tracking-widest rounded-sm flex items-center gap-1 ${prio.color}`}>
            <PrioIcon className="w-3 h-3" />
            {mission.priority}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className={`font-medium text-text leading-snug ${isDone ? "line-through text-camo-cyan/50" : ""}`}>
              {mission.name}
            </h4>
            {mission.client && (
              <div className="text-[10px] uppercase tracking-wider text-camo-cyan/60 mt-1">
                {mission.client}
              </div>
            )}
          </div>
        </div>

        {mission.notes && (
          <p className="text-xs text-camo-cyan/60 border-l-2 border-camo-line pl-3 italic">{mission.notes}</p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <div className={`flex items-center gap-1.5 text-xs ${date.overdue && !isDone ? "text-urgent" : "text-camo-cyan/70"}`}>
            <Calendar className="w-3 h-3" />
            <span className="numeric">{date.d} {date.m}</span>
          </div>
          <StatusControl id={mission.id} status={mission.status} />
        </div>
      </div>
    </div>
  );
}
