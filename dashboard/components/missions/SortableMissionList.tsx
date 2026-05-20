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
  className?: string;
};

export function SortableMissionList({
  missions,
  users,
  clientOptions,
  variant = "dark",
  compact = false,
  className = "space-y-2.5",
}: Props) {
  const [items, setItems] = useState(missions);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [suppressOpen, setSuppressOpen] = useState(false);
  const [, startTransition] = useTransition();

  useEffect(() => {
    setItems(missions);
  }, [missions]);

  function move(from: number, to: number) {
    if (from === to || from < 0 || to < 0) return;
    const previous = items;
    const next = [...items];
    const [removed] = next.splice(from, 1);
    if (!removed) return;
    next.splice(to, 0, removed);
    setItems(next);

    startTransition(async () => {
      const res = await reorderMissionsAction(next.map((item, index) => ({
        id: item.id,
        sort_order: index,
      })));
      if (!res.ok) {
        setItems(previous);
        window.alert(`Nao foi possivel reordenar: ${res.error}`);
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
            suppressOpen={suppressOpen}
          />
        </div>
      ))}
    </div>
  );
}
