import type { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string | number;
  hint?: string;
  icon: LucideIcon;
  tone?: "default" | "urgent" | "high" | "done";
  trend?: { value: string; direction: "up" | "down" | "flat" };
};

const TONE_BG = {
  default: "bg-medium/10 text-medium",
  urgent: "bg-urgent/10 text-urgent",
  high: "bg-high/10 text-high",
  done: "bg-done/10 text-done",
};

export function KpiCard({ label, value, hint, icon: Icon, tone = "default" }: Props) {
  return (
    <div className="card card-hover shadow-card p-5 flex items-start gap-4">
      <div className={`shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${TONE_BG[tone]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-xs text-muted uppercase tracking-wider">{label}</div>
        <div className="numeric text-3xl font-semibold mt-1 text-text leading-none">{value}</div>
        {hint && <div className="text-xs text-muted-strong mt-1.5">{hint}</div>}
      </div>
    </div>
  );
}
