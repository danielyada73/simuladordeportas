"use client";

import { Calendar, Flag, UserRound, X } from "lucide-react";
import type { ReactNode } from "react";
import type { Mission, MissionUser } from "@/lib/missions-types";

type Props = {
  mission: Mission;
  users: MissionUser[];
  open: boolean;
  onClose: () => void;
};

const PRIORITY_LABEL = {
  alta: "Alta",
  media: "Media",
  baixa: "Baixa",
};

const STATUS_LABEL = {
  nao_iniciada: "Aberta",
  em_progresso: "Em curso",
  concluida: "Concluida",
};

export function MissionViewDialog({ mission, users, open, onClose }: Props) {
  if (!open) return null;

  const responsible = users.find((user) => user.slug === mission.responsible_slug)?.display_name || mission.responsible_slug;
  const hasNotes = Boolean(mission.notes?.trim());

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-12 px-4 bg-black/70 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
      <div
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-2xl rounded-[30px] border border-white/10 bg-[#08090b] shadow-[0_30px_100px_-40px_rgba(0,180,252,0.55)] mb-16 overflow-hidden"
      >
        <div className="flex items-start justify-between gap-5 px-6 py-5 border-b border-white/[0.06]">
          <div className="min-w-0">
            <div className="font-stencil text-4xl tracking-wider text-white leading-none">DETALHES</div>
            <h3 className="text-xl font-semibold text-white mt-3 leading-snug">{mission.name}</h3>
            {mission.client && <div className="text-sm text-white/45 mt-1">{mission.client}</div>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/40 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <InfoChip icon={<UserRound className="w-4 h-4" />} label="Responsavel" value={responsible} />
            <InfoChip icon={<Calendar className="w-4 h-4" />} label="Data alvo" value={formatDate(mission.due_date)} />
            <InfoChip icon={<Flag className="w-4 h-4" />} label="Prioridade" value={PRIORITY_LABEL[mission.priority]} />
            <InfoChip label="Status" value={STATUS_LABEL[mission.status]} />
          </div>

          {hasNotes && (
            <div className="rounded-2xl border border-ms-blue/20 bg-ms-blue/10 p-4">
              <div className="text-xs uppercase tracking-wider text-ms-blue mb-2 font-semibold">Observacoes</div>
              <div className="text-sm leading-relaxed text-white/85 whitespace-pre-wrap">{mission.notes}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoChip({ icon, label, value }: { icon?: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-4">
      <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-white/40">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function formatDate(iso: string): string {
  if (!iso) return "-";
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}
