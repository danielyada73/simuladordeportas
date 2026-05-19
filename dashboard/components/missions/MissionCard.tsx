import { Calendar } from "lucide-react";
import { StatusControl } from "./StatusControl";
import type { Mission } from "@/lib/missions-types";

const PRIO_LIGHT = {
  alta: { bg: "bg-ms-blue", text: "text-black", label: "Alta" },
  media: { bg: "bg-black", text: "text-white", label: "Média" },
  baixa: { bg: "bg-black/10", text: "text-black", label: "Baixa" },
} as const;

const PRIO_DARK = {
  alta: { bg: "bg-ms-blue", text: "text-black", label: "Alta" },
  media: { bg: "bg-white", text: "text-black", label: "Média" },
  baixa: { bg: "bg-white/10", text: "text-white", label: "Baixa" },
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

export function MissionCard({ mission, compact = false, variant = "dark" }: { mission: Mission; compact?: boolean; variant?: "dark" | "light" }) {
  const palette = variant === "light" ? PRIO_LIGHT : PRIO_DARK;
  const prio = palette[mission.priority] || palette.media;
  const date = fmtDate(mission.due_date);
  const isDone = mission.status === "concluida";

  const isLight = variant === "light";
  const surface = isLight
    ? "bg-white border-black/5 hover:bg-black/[0.025]"
    : "bg-white/[0.035] border-white/[0.08] hover:bg-white/[0.06]";
  const nameColor = isLight
    ? (isDone ? "text-black/35 line-through" : "text-black/90")
    : (isDone ? "text-white/40 line-through" : "text-white/95");
  const clientColor = isLight ? "text-black/45" : "text-white/45";
  const dateColor = isLight
    ? (date.overdue && !isDone ? "text-ms-blue-deep" : "text-black/50")
    : (date.overdue && !isDone ? "text-ms-blue" : "text-white/50");

  if (compact) {
    return (
      <div className={`group flex items-center gap-3 px-3.5 py-2.5 rounded-[22px] border transition-all ${surface} ${isDone ? "opacity-60" : ""}`}>
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${prio.bg} ${prio.text}`}>
          {prio.label}
        </span>
        <div className="flex-1 min-w-0">
          <div className={`text-sm font-medium truncate ${nameColor}`}>{mission.name}</div>
          <div className={`text-xs truncate mt-0.5 ${clientColor}`}>
            {mission.client || "Sem cliente"}
          </div>
        </div>
        <div className={`text-xs numeric shrink-0 ${dateColor}`}>
          {date.d} {date.m}
        </div>
        <StatusControl id={mission.id} status={mission.status} variant={variant} />
      </div>
    );
  }

  return (
    <div className={`group rounded-[24px] border transition-all overflow-hidden ${surface} ${isDone ? "opacity-70" : ""}`}>
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5 flex-wrap">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${prio.bg} ${prio.text}`}>
                {prio.label}
              </span>
              {mission.client && (
                <span className={`text-[11px] truncate ${clientColor}`}>{mission.client}</span>
              )}
            </div>
            <h4 className={`font-semibold leading-snug text-[15px] ${nameColor}`}>
              {mission.name}
            </h4>
          </div>
        </div>

        {mission.notes && (
          <p className={`text-xs italic border-l-2 pl-2.5 ${isLight ? "text-black/55 border-black/10" : "text-white/55 border-white/10"}`}>
            {mission.notes}
          </p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <div className={`flex items-center gap-1.5 text-xs ${dateColor}`}>
            <Calendar className="w-3.5 h-3.5" />
            <span className="numeric">{date.d} {date.m}</span>
          </div>
          <StatusControl id={mission.id} status={mission.status} variant={variant} />
        </div>
      </div>
    </div>
  );
}
