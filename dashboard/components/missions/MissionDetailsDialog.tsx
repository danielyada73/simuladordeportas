"use client";

import { X, Save, Calendar, UserRound } from "lucide-react";
import { type FormEvent, useEffect, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { updateMissionAction } from "@/app/missoes/actions";
import type { Mission, MissionKind, MissionPriority, MissionUser } from "@/lib/missions-types";

type Props = {
  mission: Mission;
  users: MissionUser[];
  clientOptions: string[];
  open: boolean;
  onClose: () => void;
};

const PRIORITIES: { key: MissionPriority; label: string }[] = [
  { key: "alta", label: "Alta" },
  { key: "media", label: "Media" },
  { key: "baixa", label: "Baixa" },
];

const KINDS: { key: MissionKind; label: string }[] = [
  { key: "principal", label: "Missao" },
  { key: "secundaria", label: "Reuniao" },
];

export function MissionDetailsDialog({ mission, users, clientOptions, open, onClose }: Props) {
  const router = useRouter();
  const uniqueClientOptions = Array.from(new Set(clientOptions));
  const [name, setName] = useState(mission.name);
  const [client, setClient] = useState(mission.client || "");
  const [responsible, setResponsible] = useState(mission.responsible_slug);
  const [priority, setPriority] = useState<MissionPriority>(mission.priority);
  const [kind, setKind] = useState<MissionKind>(mission.kind);
  const [dueDate, setDueDate] = useState(mission.due_date);
  const [notes, setNotes] = useState(mission.notes || "");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!open) return;
    setName(mission.name);
    setClient(mission.client || "");
    setResponsible(mission.responsible_slug);
    setPriority(mission.priority);
    setKind(mission.kind);
    setDueDate(mission.due_date);
    setNotes(mission.notes || "");
    setError(null);
  }, [mission, open]);

  if (!open) return null;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Nome da missao e obrigatorio");
      return;
    }
    if (!responsible) {
      setError("Selecione um responsavel");
      return;
    }

    startTransition(async () => {
      const res = await updateMissionAction(mission.id, {
        name: name.trim(),
        client: client.trim() || null,
        responsible_slug: responsible,
        priority,
        kind,
        due_date: dueDate,
        notes: notes.trim() || null,
      });

      if (!res.ok) {
        setError(res.error);
        return;
      }

      onClose();
      router.refresh();
    });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-12 px-4 bg-black/70 backdrop-blur-sm overflow-y-auto"
      onClick={onClose}
    >
      <form
        onSubmit={submit}
        onClick={(event) => event.stopPropagation()}
        className="w-full max-w-2xl rounded-[30px] border border-white/10 bg-[#08090b] shadow-[0_30px_100px_-40px_rgba(0,180,252,0.55)] mb-16 overflow-hidden"
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.06]">
          <div>
            <div className="font-stencil text-4xl tracking-wider text-white">EDITAR MISSAO</div>
            <div className="text-sm text-white/40 mt-0.5">Informacoes e observacoes do card</div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-white/40 hover:text-white p-1.5 hover:bg-white/5 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Nome da missao *</label>
            <input
              autoFocus
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue transition-colors"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Cliente</label>
              <input
                list="mission-detail-client-options"
                type="text"
                value={client}
                onChange={(event) => setClient(event.target.value)}
                placeholder="Sem cliente"
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue transition-colors"
              />
              <datalist id="mission-detail-client-options">
                {uniqueClientOptions.map((option) => (
                  <option key={option} value={option} />
                ))}
              </datalist>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Responsavel *</label>
              <div className="relative">
                <UserRound className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/35" />
                <select
                  value={responsible}
                  onChange={(event) => setResponsible(event.target.value)}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:border-ms-blue transition-colors"
                >
                  {users.map((user) => (
                    <option key={user.slug} value={user.slug}>{user.display_name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Prioridade</label>
              <select
                value={priority}
                onChange={(event) => setPriority(event.target.value as MissionPriority)}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-ms-blue transition-colors"
              >
                {PRIORITIES.map((item) => (
                  <option key={item.key} value={item.key}>{item.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Tipo</label>
              <select
                value={kind}
                onChange={(event) => setKind(event.target.value as MissionKind)}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white focus:outline-none focus:border-ms-blue transition-colors"
              >
                {KINDS.map((item) => (
                  <option key={item.key} value={item.key}>{item.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Data alvo</label>
              <div className="relative">
                <Calendar className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/35" />
                <input
                  type="date"
                  value={dueDate}
                  onChange={(event) => setDueDate(event.target.value)}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl pl-11 pr-4 py-3 text-white focus:outline-none focus:border-ms-blue transition-colors"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs uppercase tracking-wider text-white/50 mb-2">Observacoes</label>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={5}
              placeholder="Sem observacoes"
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 text-white placeholder:text-white/25 focus:outline-none focus:border-ms-blue transition-colors resize-y min-h-[140px]"
            />
          </div>

          {error && (
            <div className="text-ms-blue text-sm border border-ms-blue/40 bg-ms-blue/10 px-3 py-2.5 rounded-xl">
              {error}
            </div>
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
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-ms-blue text-black font-semibold text-sm rounded-xl shadow-lg shadow-ms-blue/25 hover:bg-ms-blue-soft disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Save className="w-4 h-4" />
            {isPending ? "Salvando..." : "Salvar alteracoes"}
          </button>
        </div>
      </form>
    </div>
  );
}
