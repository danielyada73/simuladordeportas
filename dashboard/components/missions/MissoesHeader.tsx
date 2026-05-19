"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Plus, Settings as SettingsIcon, ChevronLeft, Calendar, CalendarClock, AlarmClock, CalendarDays, CalendarRange, List } from "lucide-react";
import { CreateMissionDialog } from "./CreateMissionDialog";
import { SettingsDialog } from "./SettingsDialog";
import type { MissionUser, MissionSettings } from "@/lib/missions-types";

type Props = {
  users: MissionUser[];
  settings: MissionSettings;
};

const WINDOWS = [
  { key: "today", label: "Hoje", icon: Calendar },
  { key: "tomorrow", label: "Amanhã", icon: CalendarClock },
  { key: "overdue", label: "Atrasadas", icon: AlarmClock },
  { key: "week", label: "Semana", icon: CalendarDays },
  { key: "month", label: "Mês", icon: CalendarRange },
  { key: "all", label: "Tudo", icon: List },
];

export function MissoesHeader({ users, settings }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const [showCreate, setShowCreate] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const current = params.get("window") || "today";

  function setWindow(k: string) {
    const next = new URLSearchParams(params.toString());
    next.set("window", k);
    if (k !== "custom") {
      next.delete("custom_from");
      next.delete("custom_to");
    }
    router.push(`${pathname}?${next.toString()}`);
  }

  function setCustomRange(from: string, to: string) {
    const next = new URLSearchParams(params.toString());
    next.set("window", "custom");
    if (from) next.set("custom_from", from);
    if (to) next.set("custom_to", to);
    router.push(`${pathname}?${next.toString()}`);
  }

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-camo-line/60 backdrop-blur-md bg-camo-deep/80">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center gap-4 justify-between">
          {/* Left: back + Criar Missão */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-1 text-xs uppercase tracking-[0.2em] text-camo-cyan/80 hover:text-camo-cyan transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              Painel
            </Link>
            <button
              onClick={() => setShowCreate(true)}
              className="ml-3 flex items-center gap-2 px-4 py-2 bg-camo-cyan text-camo-deep font-stencil tracking-widest text-base rounded-sm shadow-tactical hover:brightness-110 transition-all"
            >
              <Plus className="w-4 h-4" strokeWidth={3} />
              CRIAR MISSÃO
            </button>
          </div>

          {/* Center: date filter */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <div className="flex bg-camo-base/80 border border-camo-line rounded-sm p-1">
              {WINDOWS.map((w) => {
                const Icon = w.icon;
                const active = current === w.key;
                return (
                  <button
                    key={w.key}
                    onClick={() => setWindow(w.key)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 text-xs uppercase tracking-wider transition-colors ${
                      active
                        ? "bg-camo-cyan text-camo-deep font-semibold"
                        : "text-camo-cyan/70 hover:text-camo-cyan"
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    {w.label}
                  </button>
                );
              })}
            </div>
            <div className="flex items-center gap-1">
              <input
                type="date"
                defaultValue={params.get("custom_from") || ""}
                onChange={(e) => setCustomRange(e.target.value, params.get("custom_to") || "")}
                className="bg-camo-base border border-camo-line rounded-sm px-2 py-1 text-xs text-camo-cyan focus:outline-none focus:border-camo-cyan"
              />
              <span className="text-camo-cyan/40 text-xs">→</span>
              <input
                type="date"
                defaultValue={params.get("custom_to") || ""}
                onChange={(e) => setCustomRange(params.get("custom_from") || "", e.target.value)}
                className="bg-camo-base border border-camo-line rounded-sm px-2 py-1 text-xs text-camo-cyan focus:outline-none focus:border-camo-cyan"
              />
            </div>
          </div>

          {/* Right: logo + settings */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 text-camo-cyan/60 hover:text-camo-cyan transition-colors rounded-sm hover:bg-camo-mid/40"
              title="Configurações"
            >
              <SettingsIcon className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              {settings.logo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={settings.logo_url}
                  alt="Logo"
                  className="h-9 w-auto object-contain"
                />
              ) : (
                <div className="font-stencil text-2xl tracking-wider text-camo-cyan">
                  ALPHA<span className="text-camo-amber">·</span>OS
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <CreateMissionDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        users={users}
        clientOptions={settings.client_options || []}
      />
      <SettingsDialog
        open={showSettings}
        onClose={() => setShowSettings(false)}
        users={users}
        settings={settings}
      />
    </>
  );
}
