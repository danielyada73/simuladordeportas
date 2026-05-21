"use client";

import { useEffect, useState, useTransition } from "react";
import { reorderMissionsAction } from "@/app/missoes/actions";
import { MissionCard } from "./MissionCard";
import type { Mission, MissionUser } from "@/lib/missions-types";

type Props = {
  missions: Mission[];
  users: MissionUser[];
  clientOptions: string[];
  variant?: "dark" | "light";
  compact?: boolean;
  cardTone?: "default" | "meeting";
  className?: string;
  storageKey: string;
};

export function SortableMissionList({
  missions,
  users,
  clientOptions,
  variant = "dark",
  compact = false,
  cardTone = "default",
  className = "space-y-2.5",
  storageKey,
}: Props) {
  const [items, setItems] = useState(missions);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [suppressOpen, setSuppressOpen] = useState(false);
  const [, startTransition] = useTransition();

  useEffect(() => {
    setItems(applyStoredOrder(missions, storageKey));
  }, [missions, storageKey]);

  function move(from: number, to: number) {
    if (from === to || from < 0 || to < 0) return;
    const next = [...items];
    const [removed] = next.splice(from, 1);
    if (!removed) return;
    next.splice(to, 0, removed);
    setItems(next);
    saveStoredOrder(storageKey, next);

    startTransition(async () => {
      const res = await reorderMissionsAction(next.map((item, index) => ({
        id: item.id,
        sort_order: index,
      })));
      if (!res.ok) {
        console.warn("A ordem foi mantida neste navegador, mas nao persistiu no banco.", res.error);
      }
    });
  }

  return (
    <div className={className}>
      {items.map((mission, index) => (
        <div
          key={mission.id}
          draggable
          onDragStart={(event) => {
            setDraggedIndex(index);
            setDraggingId(mission.id);
            setSuppressOpen(true);
            event.dataTransfer.effectAllowed = "move";
            event.dataTransfer.setData("text/plain", mission.id);
          }}
          onDragOver={(event) => {
            event.preventDefault();
            event.dataTransfer.dropEffect = "move";
          }}
          onDrop={(event) => {
            event.preventDefault();
            if (draggedIndex === null) return;
            move(draggedIndex, index);
          }}
          onDragEnd={() => {
            setDraggedIndex(null);
            setDraggingId(null);
            window.setTimeout(() => setSuppressOpen(false), 0);
          }}
          className={`transition-opacity ${draggingId === mission.id ? "opacity-45" : "opacity-100"}`}
        >
          <MissionCard
            mission={mission}
            users={users}
            clientOptions={clientOptions}
            variant={variant}
            compact={compact}
            tone={cardTone}
            suppressOpen={suppressOpen}
          />
        </div>
      ))}
    </div>
  );
}

function applyStoredOrder(missions: Mission[], storageKey: string): Mission[] {
  if (typeof window === "undefined") return missions;
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) return missions;

  try {
    const ids = JSON.parse(raw) as string[];
    const position = new Map(ids.map((id, index) => [id, index]));
    return [...missions].sort((a, b) => {
      const aPos = position.get(a.id) ?? Number.MAX_SAFE_INTEGER;
      const bPos = position.get(b.id) ?? Number.MAX_SAFE_INTEGER;
      return aPos - bPos;
    });
  } catch {
    return missions;
  }
}

function saveStoredOrder(storageKey: string, missions: Mission[]) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(storageKey, JSON.stringify(missions.map((mission) => mission.id)));
}
