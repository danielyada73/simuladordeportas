"use client";

import { X, Flame, AlertTriangle, Circle, Minus, Crosshair, Target } from "lucide-react";
import { useEffect, useState, useTransition } from "react";
import { createMissionAction, type CreateMissionInput } from "@/app/missoes/actions";
import type { MissionUser, MissionPriority, MissionKind } from "@/lib/missions-types";

type Props = {
  open: boolean;
  onClose: () => void;
  users: MissionUser[];
  clientOptions: string[];
};

const PRIORITIES: { key: MissionPriority; label: string; icon: any; color: string }[] = [
  { key: "alta", label: "ALTA", icon: Flame, color: "text-urgent border-urgent/50 bg-urgent/10" },
  { key: "media", label: "MÉDIA", icon: AlertTriangle, color: "text-camo-amber border-camo-amber/50 bg-camo-amber/10" },
  { key: "baixa", label: "BAIXA", icon: Minus, color: "text-camo-cyan border-camo-cyan/50 bg-camo-cyan/10" },
];

const KINDS: { key: MissionKind; label: string; icon: any }[] = [
  { key: "principal", label: "PRINCIPAL", icon: Target },
  { key: "secundaria", label: "SECUNDÁRIA", icon: Crosshair },
];

function todayISO() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function CreateMissionDialog({ open, onClose, users, clientOptions }: Props) {
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
      if (res.ok) onClose();
      else setError(res.error);
    });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-camo-deep/80 backdrop-blur-sm" onClick={onClose}>
      <form
        onSubmit={submit}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-camo-base border border-camo-cyan/30 rounded-sm shadow-tactical"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-camo-line">
          <div>
            <div className="font-stencil text-3xl tracking-widest text-camo-cyan">NOVA MISSÃO</div>
            <div className="text-xs text-camo-cyan/50 uppercase tracking-wider">Briefing operacional</div>
          </div>
          <button type="button" onClick={onClose} className="text-camo-cyan/60 hover:text-camo-cyan">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Nome */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Nome da missão *</label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: Subir novos criativos vídeo Meta"
              className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2.5 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan"
            />
          </div>

          {/* Cliente + Responsável */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Cliente</label>
              <input
                list="client-options"
                type="text"
                value={client}
                onChange={(e) => setClient(e.target.value)}
                placeholder="Nome do cliente"
                className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2.5 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan"
              />
              <datalist id="client-options">
                {clientOptions.map((c) => <option key={c} value={c} />)}
              </datalist>
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Responsável *</label>
              <select
                value={responsible}
                onChange={(e) => setResponsible(e.target.value)}
                className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2.5 text-text focus:outline-none focus:border-camo-cyan"
              >
                {users.map((u) => <option key={u.slug} value={u.slug}>{u.display_name}</option>)}
              </select>
            </div>
          </div>

          {/* Prioridade */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Prioridade</label>
            <div className="grid grid-cols-3 gap-2">
              {PRIORITIES.map((p) => {
                const Icon = p.icon;
                const active = priority === p.key;
                return (
                  <button
                    type="button"
                    key={p.key}
                    onClick={() => setPriority(p.key)}
                    className={`flex items-center justify-center gap-2 py-2.5 border rounded-sm font-stencil tracking-widest text-sm transition-all ${
                      active ? p.color + " font-semibold" : "border-camo-line text-camo-cyan/50 hover:border-camo-cyan/40"
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
            <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Tipo</label>
            <div className="grid grid-cols-2 gap-2">
              {KINDS.map((k) => {
                const Icon = k.icon;
                const active = kind === k.key;
                return (
                  <button
                    type="button"
                    key={k.key}
                    onClick={() => setKind(k.key)}
                    className={`flex items-center justify-center gap-2 py-2.5 border rounded-sm font-stencil tracking-widest text-sm transition-all ${
                      active ? "border-camo-cyan text-camo-cyan bg-camo-mid/50 font-semibold" : "border-camo-line text-camo-cyan/50 hover:border-camo-cyan/40"
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
            <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Data alvo</label>
            <input
              type="date"
              value={due}
              onChange={(e) => setDue(e.target.value)}
              className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2.5 text-text focus:outline-none focus:border-camo-cyan"
            />
          </div>

          {/* Observações */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-camo-cyan/70 mb-2">Observações</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              placeholder="Notas adicionais (opcional)"
              className="w-full bg-camo-deep border border-camo-line rounded-sm px-3 py-2.5 text-text placeholder:text-camo-cyan/30 focus:outline-none focus:border-camo-cyan resize-none"
            />
          </div>

          {error && (
            <div className="text-urgent text-sm border border-urgent/40 bg-urgent/10 px-3 py-2 rounded-sm">{error}</div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-camo-line bg-camo-deep/60">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-camo-cyan/70 hover:text-camo-cyan uppercase tracking-wider text-sm"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={isPending}
            className="px-6 py-2 bg-camo-cyan text-camo-deep font-stencil tracking-widest rounded-sm shadow-tactical hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {isPending ? "ENVIANDO..." : "CADASTRAR MISSÃO"}
          </button>
        </div>
      </form>
    </div>
  );
}
