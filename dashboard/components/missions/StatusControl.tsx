"use client";

import { useState, useTransition } from "react";
import { Check, Loader, Circle, Trash2 } from "lucide-react";
import { updateMissionStatusAction, deleteMissionAction } from "@/app/missoes/actions";
import type { MissionStatus } from "@/lib/missions-types";

type Props = { id: string; status: MissionStatus };

const STATUSES: { key: MissionStatus; label: string; icon: any; activeCls: string }[] = [
  { key: "nao_iniciada", label: "Aberta", icon: Circle, activeCls: "bg-white/10 text-white" },
  { key: "em_progresso", label: "Em curso", icon: Loader, activeCls: "bg-camo-amber/20 text-camo-amber" },
  { key: "concluida", label: "Concluída", icon: Check, activeCls: "bg-low/20 text-low" },
];

export function StatusControl({ id, status }: Props) {
  const [pending, start] = useTransition();
  const [showConfirm, setShowConfirm] = useState(false);

  function set(s: MissionStatus) {
    if (s === status) return;
    start(async () => {
      const res = await updateMissionStatusAction(id, s);
      if (res.ok && s === "concluida") celebrate();
    });
  }

  function remove() {
    start(async () => {
      await deleteMissionAction(id);
    });
  }

  function celebrate() {
    if (typeof window === "undefined") return;
    const root = document.createElement("div");
    root.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:60;display:flex;align-items:center;justify-content:center;";
    root.innerHTML = `
      <div style="font-family:'Bebas Neue', Impact, sans-serif; font-size:96px; letter-spacing:.12em; color:#ff5a1f; text-shadow:0 0 30px rgba(255,90,31,.5); animation:popUp 1.3s ease-out forwards;">
        MISSÃO CUMPRIDA
      </div>
      <style>@keyframes popUp{0%{transform:scale(.5);opacity:0}30%{transform:scale(1.1);opacity:1}80%{transform:scale(1);opacity:1}100%{transform:scale(1);opacity:0}}</style>
    `;
    document.body.appendChild(root);
    setTimeout(() => root.remove(), 1300);
  }

  return (
    <div className="flex items-center gap-1">
      {STATUSES.map((s) => {
        const Icon = s.icon;
        const active = status === s.key;
        return (
          <button
            key={s.key}
            onClick={() => set(s.key)}
            disabled={pending}
            title={s.label}
            className={`p-1.5 rounded-md transition-all ${
              active
                ? s.activeCls + " ring-1 ring-inset ring-white/10"
                : "text-white/30 hover:text-white/70 hover:bg-white/5"
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
          </button>
        );
      })}
      {!showConfirm ? (
        <button
          onClick={() => setShowConfirm(true)}
          className="ml-1 p-1.5 text-white/20 hover:text-urgent hover:bg-urgent/10 rounded-md transition-all"
          title="Excluir"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ) : (
        <div className="ml-1 flex items-center gap-1 text-[10px]">
          <button onClick={remove} disabled={pending} className="px-2 py-1 bg-urgent/20 text-urgent rounded-md font-medium hover:bg-urgent/30">
            Excluir
          </button>
          <button onClick={() => setShowConfirm(false)} className="px-2 py-1 text-white/50 hover:text-white rounded-md">
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
