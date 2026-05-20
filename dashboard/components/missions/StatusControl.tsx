"use client";

import { useState, useTransition } from "react";
import { Check, Loader, Circle, Trash2 } from "lucide-react";
import { updateMissionStatusAction, deleteMissionAction } from "@/app/missoes/actions";
import type { MissionStatus } from "@/lib/missions-types";

type Props = { id: string; status: MissionStatus; variant?: "dark" | "light" };

const STATUSES: { key: MissionStatus; label: string; icon: any; cls: string }[] = [
  { key: "nao_iniciada", label: "Aberta", icon: Circle, cls: "bg-ms-blue/15 text-ms-blue" },
  { key: "em_progresso", label: "Em curso", icon: Loader, cls: "bg-ms-blue text-black" },
  { key: "concluida", label: "Concluída", icon: Check, cls: "bg-white text-black" },
];

export function StatusControl({ id, status, variant = "dark" }: Props) {
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
      <div style="font-family:'Bebas Neue', Impact, sans-serif; font-size:96px; letter-spacing:.12em; color:#00B4FC; text-shadow:0 0 30px rgba(0,180,252,.5); animation:popUp 1.3s ease-out forwards;">
        MISSÃO CUMPRIDA
      </div>
      <style>@keyframes popUp{0%{transform:scale(.5);opacity:0}30%{transform:scale(1.1);opacity:1}80%{transform:scale(1);opacity:1}100%{transform:scale(1);opacity:0}}</style>
    `;
    document.body.appendChild(root);
    setTimeout(() => root.remove(), 1300);
  }

  const isLight = variant === "light";
  const idleCls = isLight ? "text-black/25 hover:text-black/70 hover:bg-black/5" : "text-white/25 hover:text-white/70 hover:bg-white/5";
  const trashIdle = isLight ? "text-black/20 hover:text-ms-blue-deep hover:bg-ms-blue/10" : "text-white/20 hover:text-ms-blue hover:bg-ms-blue/10";
  const cancelCls = isLight ? "text-black/50 hover:text-black" : "text-white/50 hover:text-white";

  return (
    <div
      className="flex items-center gap-1"
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      {STATUSES.map((s) => {
        const Icon = s.icon;
        const active = status === s.key;
        return (
          <button
            key={s.key}
            onClick={() => set(s.key)}
            disabled={pending}
            title={s.label}
            className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
              active ? s.cls : idleCls
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
          </button>
        );
      })}
      {!showConfirm ? (
        <button
          onClick={() => setShowConfirm(true)}
          className={`ml-1 w-7 h-7 rounded-full flex items-center justify-center transition-all ${trashIdle}`}
          title="Excluir"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      ) : (
        <div className="ml-1 flex items-center gap-1 text-[10px]">
          <button onClick={remove} disabled={pending} className="px-2 py-1 bg-ms-blue/15 text-ms-blue rounded-full font-medium hover:bg-ms-blue/25">
            Excluir
          </button>
          <button onClick={() => setShowConfirm(false)} className={`px-2 py-1 rounded-full ${cancelCls}`}>
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
