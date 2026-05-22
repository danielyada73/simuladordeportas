"use client";

import type { MissionPriority } from "@/lib/missions-types";

const RESPECT_BY_PRIORITY: Record<MissionPriority, number> = {
  alta: 5,
  media: 3,
  baixa: 1,
};

export function playMissionPassed(priority: MissionPriority) {
  playAudio("/audio/audiodamissao.mp3");
  showArcadeOverlay({
    title: "MISSAO CUMPRIDA",
    subtitle: `RESPEITO +${RESPECT_BY_PRIORITY[priority]}`,
    tone: "passed",
    duration: 3800,
  });
}

export function playOverdueFailed() {
  playAudio("/audio/audiosefudeu.mp3");
  showArcadeOverlay({
    title: "SE FODEU!",
    tone: "failed",
    duration: 3200,
  });
}

function playAudio(src: string) {
  if (typeof window === "undefined") return;
  const audio = new Audio(src);
  audio.volume = 0.75;
  audio.play().catch(() => undefined);
}

function showArcadeOverlay({
  title,
  subtitle,
  tone,
  duration,
}: {
  title: string;
  subtitle?: string;
  tone: "passed" | "failed";
  duration: number;
}) {
  if (typeof window === "undefined") return;

  document.getElementById("mission-arcade-overlay")?.remove();

  const root = document.createElement("div");
  root.id = "mission-arcade-overlay";
  root.style.cssText = "position:fixed;inset:0;z-index:90;pointer-events:none;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.18);";

  const isPassed = tone === "passed";
  root.innerHTML = `
    <div class="arcade-fx ${tone}">
      <div class="arcade-title">${title}</div>
      ${subtitle ? `<div class="arcade-subtitle">${subtitle}</div>` : ""}
    </div>
    <style>
      .arcade-fx {
        transform: translateY(16px) scale(.92);
        opacity: 0;
        text-align: center;
        font-family: Impact, 'Bebas Neue', Arial Black, sans-serif;
        letter-spacing: .04em;
        animation: arcadeMissionFx ${duration}ms ease-out forwards;
      }
      .arcade-title {
        font-size: clamp(64px, 10vw, 148px);
        line-height: .82;
        -webkit-text-stroke: 5px #050505;
        text-shadow: 0 7px 0 #050505, 0 18px 35px rgba(0,0,0,.65);
      }
      .arcade-subtitle {
        margin-top: 8px;
        font-size: clamp(38px, 6vw, 86px);
        line-height: .9;
        color: #f5f5f5;
        -webkit-text-stroke: 4px #050505;
        text-shadow: 0 6px 0 #050505, 0 16px 30px rgba(0,0,0,.55);
      }
      .arcade-fx.passed .arcade-title { color: #9a7313; }
      .arcade-fx.failed .arcade-title { color: #cf2d25; }
      @keyframes arcadeMissionFx {
        0% { opacity: 0; transform: translateY(30px) scale(.86); filter: blur(2px); }
        13% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
        82% { opacity: 1; transform: translateY(0) scale(1); }
        100% { opacity: 0; transform: translateY(-18px) scale(1.02); }
      }
    </style>
  `;

  if (!isPassed) {
    root.style.background = "radial-gradient(circle at center, rgba(195,22,22,.34), rgba(0,0,0,.48) 55%, rgba(0,0,0,.68))";
  }

  document.body.appendChild(root);
  window.setTimeout(() => root.remove(), duration);
}
