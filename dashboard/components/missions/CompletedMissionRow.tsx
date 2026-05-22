"use client";

import { useState, useTransition } from "react";
import { Check, Settings, Trash2 } from "lucide-react";
import { deleteMissionAction } from "@/app/missoes/actions";
import { MissionDetailsDialog } from "./MissionDetailsDialog";
import { MissionViewDialog } from "./MissionViewDialog";
import type { Mission, MissionUser } from "@/lib/missions-types";

type Props = {
  mission: Mission;
  user?: MissionUser;
  users: MissionUser[];
  clientOptions: string[];
};

export function CompletedMissionRow({ mission, user, users, clientOptions }: Props) {
  const [viewOpen, setViewOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [pending, startTransition] = useTransition();

  function remove() {
    startTransition(async () => {
      await deleteMissionAction(mission.id);
    });
  }

  return (
    <>
      <div
        role="button"
        tabIndex={0}
        onClick={() => setViewOpen(true)}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") setViewOpen(true);
        }}
        className="group flex items-center gap-3 rounded-[22px] bg-white/[0.08] border border-white/[0.12] px-3.5 py-3 cursor-pointer hover:bg-white/[0.11] transition-colors"
      >
        <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center shrink-0">
          <Check className="w-4 h-4 text-black" strokeWidth={3} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-white/85 truncate line-through">{mission.name}</div>
          <div className="text-xs text-white/45 truncate mt-0.5">
            {user?.display_name || mission.responsible_slug}
            {mission.client ? ` - ${mission.client}` : ""}
          </div>
        </div>

        <div className="flex items-center gap-1" onClick={(event) => event.stopPropagation()}>
          <button
            type="button"
            onClick={() => setEditOpen(true)}
            className="w-8 h-8 rounded-full flex items-center justify-center text-white/35 hover:text-white hover:bg-white/10 transition-all"
            title="Editar"
          >
            <Settings className="w-4 h-4" />
          </button>
          {!confirmDelete ? (
            <button
              type="button"
              onClick={() => setConfirmDelete(true)}
              className="w-8 h-8 rounded-full flex items-center justify-center text-white/25 hover:text-ms-blue hover:bg-ms-blue/10 transition-all"
              title="Excluir"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          ) : (
            <div className="flex items-center gap-1 text-[10px]">
              <button
                type="button"
                onClick={remove}
                disabled={pending}
                className="px-2 py-1 rounded-full bg-ms-blue/15 text-ms-blue font-medium hover:bg-ms-blue/25 disabled:opacity-50"
              >
                Excluir
              </button>
              <button
                type="button"
                onClick={() => setConfirmDelete(false)}
                className="px-2 py-1 rounded-full text-white/50 hover:text-white"
              >
                x
              </button>
            </div>
          )}
        </div>
      </div>

      <MissionViewDialog
        mission={mission}
        users={users}
        open={viewOpen}
        onClose={() => setViewOpen(false)}
      />
      <MissionDetailsDialog
        mission={mission}
        users={users}
        clientOptions={clientOptions}
        open={editOpen}
        onClose={() => setEditOpen(false)}
      />
    </>
  );
}
