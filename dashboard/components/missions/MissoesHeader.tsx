"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Plus, Settings as SettingsIcon, ChevronLeft } from "lucide-react";
import { CreateMissionDialog } from "./CreateMissionDialog";
import { SettingsDialog } from "./SettingsDialog";
import type { MissionUser, MissionSettings } from "@/lib/missions-types";

type Props = { users: MissionUser[]; settings: MissionSettings };

const WINDOWS = [
  { key: "today", label: "Hoje" },
  { key: "tomorrow", label: "Amanhã" },
  { key: "overdue", label: "Atrasadas" },
  { key: "week", label: "Semana" },
  { key: "month", label: "Mês" },
  { key: "all", label: "Tudo" },
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
      <header className="sticky top-0 z-30 border-b border-white/[0.08] backdrop-blur-xl bg-ms-bg/88">
        <div className="max-w-[1500px] mx-auto px-6 h-16 flex items-center gap-4 justify-between">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="flex items-center gap-1.5 text-sm text-white/55 hover:text-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Painel
            </Link>
            <div className="w-px h-6 bg-white/10" />
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-2 px-4 py-2 bg-ms-blue text-black font-semibold text-sm rounded-full shadow-[0_8px_24px_-8px_rgba(0,180,252,0.5)] hover:bg-ms-blue-soft transition-all"
            >
              <Plus className="w-4 h-4" strokeWidth={3} />
              Nova missão
            </button>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2">
            <div className="flex bg-white/[0.05] border border-white/[0.08] rounded-full p-1">
              {WINDOWS.map((w) => {
                const active = current === w.key;
                return (
                  <button
                    key={w.key}
                    onClick={() => setWindow(w.key)}
                    className={`px-3.5 py-1.5 text-xs font-medium rounded-full transition-all ${
                      active
                        ? "bg-white text-black"
                        : "text-white/60 hover:text-white"
                    }`}
                  >
                    {w.label}
                  </button>
                );
              })}
            </div>
            <div className="flex items-center gap-1.5 text-xs">
              <input
                type="date"
                defaultValue={params.get("custom_from") || ""}
                onChange={(e) => setCustomRange(e.target.value, params.get("custom_to") || "")}
                className="bg-white/[0.04] border border-white/[0.06] rounded-full px-3 py-1.5 text-white/80 focus:outline-none focus:border-ms-blue"
              />
              <span className="text-white/30">→</span>
              <input
                type="date"
                defaultValue={params.get("custom_to") || ""}
                onChange={(e) => setCustomRange(params.get("custom_from") || "", e.target.value)}
                className="bg-white/[0.04] border border-white/[0.06] rounded-full px-3 py-1.5 text-white/80 focus:outline-none focus:border-ms-blue"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSettings(true)}
              className="p-2 text-white/50 hover:text-white rounded-full hover:bg-white/5 transition-colors"
              title="Configurações"
            >
              <SettingsIcon className="w-4 h-4" />
            </button>
            {settings.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={settings.logo_url} alt="Logo" className="h-8 w-auto object-contain" />
            ) : (
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-ms-blue flex items-center justify-center font-bold text-ms-bg text-sm">α</div>
                <span className="font-semibold text-white text-sm">Alpha OS</span>
              </div>
            )}
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
