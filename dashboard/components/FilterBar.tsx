"use client";

import { Calendar, CalendarClock, AlarmClock, CalendarDays, CalendarRange, List } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { LucideIcon } from "lucide-react";

type WindowDef = { key: string; label: string; icon: LucideIcon };

const WINDOWS: WindowDef[] = [
  { key: "today", label: "Hoje", icon: Calendar },
  { key: "tomorrow", label: "Amanhã", icon: CalendarClock },
  { key: "overdue", label: "Atrasadas", icon: AlarmClock },
  { key: "week", label: "Semana", icon: CalendarDays },
  { key: "month", label: "Mês", icon: CalendarRange },
  { key: "all", label: "Tudo", icon: List },
];

export function FilterBar({ showCustom = true }: { showCustom?: boolean }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const current = params.get("window") || "today";

  const setWindow = (key: string) => {
    const next = new URLSearchParams(params.toString());
    next.set("window", key);
    if (key !== "custom") {
      next.delete("custom_from");
      next.delete("custom_to");
    }
    router.push(`${pathname}?${next.toString()}`);
  };

  const setCustomRange = (from: string, to: string) => {
    const next = new URLSearchParams(params.toString());
    next.set("window", "custom");
    if (from) next.set("custom_from", from);
    if (to) next.set("custom_to", to);
    router.push(`${pathname}?${next.toString()}`);
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex bg-surface border border-border rounded-xl p-1 shadow-card">
        {WINDOWS.map((w) => {
          const Icon = w.icon;
          const active = current === w.key;
          return (
            <button
              key={w.key}
              onClick={() => setWindow(w.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-all ${
                active
                  ? "bg-bg text-text shadow-card font-medium"
                  : "text-muted-strong hover:text-text"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {w.label}
            </button>
          );
        })}
      </div>
      {showCustom && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            defaultValue={params.get("custom_from") || ""}
            onChange={(e) => setCustomRange(e.target.value, params.get("custom_to") || "")}
            className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm hover:border-border-strong focus:border-accent focus:outline-none"
          />
          <span className="text-muted text-sm">→</span>
          <input
            type="date"
            defaultValue={params.get("custom_to") || ""}
            onChange={(e) => setCustomRange(params.get("custom_from") || "", e.target.value)}
            className="bg-surface border border-border rounded-lg px-3 py-1.5 text-sm hover:border-border-strong focus:border-accent focus:outline-none"
          />
        </div>
      )}
    </div>
  );
}
