"use client";

import { X, Flame, AlertTriangle, Minus, Crosshair, Target } from "lucide-react";
import { useEffect, useState, useTransition } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { createMissionAction, type CreateMissionInput } from "@/app/missoes/actions";
import type { MissionUser, MissionPriority, MissionKind } from "@/lib/missions-types";

type Props = {
  open: boolean;
  onClose: () => void;
  users: MissionUser[];
  clientOptions: string[];
};

const PRIORITIES: { key: MissionPriority; label: string; icon: any; activeCls: string }[] = [
  { key: "alta", label: "Alta", icon: Flame, activeCls: "bg-ms-blue text-black border-ms-blue" },
  { key: "media", label: "Média", icon: AlertTriangle, activeCls: "bg-white text-black border-white" },
  { key: "baixa", label: "Baixa", icon: Minus, activeCls: "bg-white/10 text-white border-white/20" },
];

const KINDS: { key: MissionKind; label: string; icon: any }[] = [
  { key: "principal", label: "Principal", icon: Target },
  { key: "secundaria", label: "Secundária", icon: Crosshair },
];

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function pickWindowForDate(dateISO: string): string {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(`${dateISO}T12:00:00`);
  target.setHours(0, 0, 0, 0);
  const diff = Math.round((target.getTime() - today.getTime()) / 86400000);
  if (diff < 0) return "overdue";
  if (diff === 0) return "today";
  if (diff === 1) return "tomorrow";
  if (diff <= 7) return "week";
  if (diff <= 30) return "month";
  return "all";
}

export function CreateMissionDialog({ open, onClose, users, clientOptions }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const uniqueClientOptions = Array.from(new Set(clientOptions));

  const [name, setName] = useState("");
  const [client, setClient] = useState("");
  const [responsible, setResponsible] = useState(users[0]?.slug || "");
  const [priority, setPriority] = useState<MissionPriority>("media");
  const [kind, setKind] = useState<MissionKind>("principal");
  const [due, setDue] = useState(todayISO());
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (open) {
      setName("");
      setClient("");
      setResponsible(users[0]?.slug || "");
      setPriority("media");
      setKind("principal");
      setDue(todayISO());
      setNotes("");
      setError(null);
    }
  }, [open, users]);

  if (!open) return null;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!name.trim()) { setError("Nome da missão é obrigatório"); return; }
    if (!responsible) { setError("Selecione um responsável"); return; }

    const payload: CreateMissionInput = {
      name: name.trim(),
      client: client.trim() || undefined,
      responsible_slug: responsible,
      priority,
      kind,
      due_date: due,
      notes: notes.trim() || undefined,
    };

    startTransition(async () => {
      const res = await createMissionAction(payload);
      if (!res.ok) {
        setError(res.error);
        return;
      }
      const targetWindow = pickWindowForDate(due);
      const current = params.get("window") || "today";
      const next = new URLSearchParams(params.toString());

      // Se a missao criada nao cabe na janela atual, troca pra janela que mostra
      if (targetWindow !== current && current !== "all") {
        next.set("window", targetWindow);
        next.delete("custom_from");
        next.delete("custom_to");
      }

      showToast(`✓ Missão criada · ${windowLabel(targetWindow)}`);
      onClose();
      router.push(`${pathname}?${next.toString()}`);
      router.refresh();
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-12 px-4 bg-black/70 backdrop-blur-sm overflow-y-auto" onClick={onClose}>
      <form
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl rounded-[30px] border border-white/10 bg-[#08090b] shadow-[0_30px_100px_-40px_rgba(0,180,252,0.55)] mb-16 overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.06]">
          <div>
            <div className="font-stencil text-4xl tracking-wider text-white">NOVA MISSÃO</div>
            <div className="text-sm text-white/40 mt-0.5">Briefing operacional</div>
          </div>
          <button type="button" onClick={onClose} className="text-white/40 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Nome */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Nome da missão *</label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Subir novos criativos vídeo Meta"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-accent transition-colors"
            />
          </div>

          {/* Cliente + Responsável */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Cliente</label>
              <input
                list="client-options"
                type="text"
                value={client}
                onChange={(e) => setClient(e.target.value)}
                placeholder="Nome do cliente"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-accent transition-colors"
              />
              <datalist id="client-options">
                {uniqueClientOptions.map((c) => <option key={c} value={c} />)}
              </datalist>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Responsável *</label>
              <select
                value={responsible}
                onChange={(e) => setResponsible(e.target.value)}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent transition-colors"
              >
                {users.map((u) => <option key={u.slug} value={u.slug}>{u.display_name}</option>)}
              </select>
            </div>
          </div>

          {/* Prioridade */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Prioridade</label>
            <div className="grid grid-cols-3 gap-2">
              {PRIORITIES.map((p) => {
                const Icon = p.icon;
                const active = priority === p.key;
                return (
                  <button
                    type="button"
                    key={p.key}
                    onClick={() => setPriority(p.key)}
                    className={`flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm transition-all ${
                      active
                        ? p.activeCls + " font-semibold"
                        : "border-white/[0.08] text-white/50 hover:border-white/20"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tipo */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Tipo</label>
            <div className="grid grid-cols-2 gap-2">
              {KINDS.map((k) => {
                const Icon = k.icon;
                const active = kind === k.key;
                return (
                  <button
                    type="button"
                    key={k.key}
                    onClick={() => setKind(k.key)}
                    className={`flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm transition-all ${
                      active
                        ? "bg-ms-blue text-black border-ms-blue font-semibold"
                        : "border-white/[0.08] text-white/50 hover:border-white/20"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {k.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Data */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Data alvo</label>
            <input
              type="date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent transition-colors"
            />
            <div className="text-xs text-white/40 mt-1.5">
              Será exibida no filtro: <span className="text-accent font-semibold">{windowLabel(pickWindowForDate(due))}</span>
            </div>
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Observações</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Notas adicionais (opcional)"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-accent transition-colors resize-none"
            />
          </div>

          {error && (
            <div className="text-urgent text-sm border border-urgent/40 bg-urgent/10 px-3 py-2.5 rounded-xl">{error}</div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.06]">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 text-white/60 hover:text-white text-sm transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="px-6 py-2.5 bg-ms-blue text-black font-semibold text-sm rounded-xl shadow-lg shadow-ms-blue/25 hover:bg-ms-blue-soft disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isPending ? "Enviando..." : "Cadastrar missão"}
          </button>
        </div>
      </form>
    </div>
  );
}

function windowLabel(w: string): string {
  const m: Record<string, string> = {
    today: "Hoje",
    tomorrow: "Amanhã",
    overdue: "Atrasadas",
    week: "Semana",
    month: "Mês",
    all: "Tudo",
  };
  return m[w] || w;
}

function showToast(message: string) {
  if (typeof window === "undefined") return;
  const root = document.createElement("div");
  root.style.cssText = "position:fixed;top:80px;left:50%;transform:translateX(-50%);z-index:60;pointer-events:none;";
  root.innerHTML = `
    <div style="background:#08090b;border:1px solid rgba(0,180,252,0.45);color:#00B4FC;padding:12px 20px;border-radius:16px;font-family:Inter,system-ui,sans-serif;font-weight:600;font-size:14px;box-shadow:0 10px 40px rgba(0,180,252,0.25);animation:slideIn 2.5s ease-out forwards;">
      ${message}
    </div>
    <style>@keyframes slideIn{0%{transform:translateY(-20px);opacity:0}10%{transform:translateY(0);opacity:1}85%{transform:translateY(0);opacity:1}100%{transform:translateY(-20px);opacity:0}}</style>
  `;
  document.body.appendChild(root);
  setTimeout(() => root.remove(), 2500);
}
