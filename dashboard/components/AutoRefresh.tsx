"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function AutoRefresh({ intervalMs = 60000 }: { intervalMs?: number }) {
  const router = useRouter();
  const [secondsLeft, setSecondsLeft] = useState(Math.floor(intervalMs / 1000));

  useEffect(() => {
    setSecondsLeft(Math.floor(intervalMs / 1000));
    const tick = setInterval(() => {
      setSecondsLeft((s) => (s <= 1 ? Math.floor(intervalMs / 1000) : s - 1));
    }, 1000);
    const refresh = setInterval(() => router.refresh(), intervalMs);
    return () => {
      clearInterval(tick);
      clearInterval(refresh);
    };
  }, [intervalMs, router]);

  return (
    <button
      onClick={() => router.refresh()}
      className="group flex items-center gap-2 text-xs text-muted-strong hover:text-text px-3 py-1.5 rounded-lg border border-border hover:border-border-strong transition-colors"
    >
      <RefreshCw className="w-3.5 h-3.5 group-hover:rotate-180 transition-transform duration-500" />
      <span className="numeric">{secondsLeft}s</span>
    </button>
  );
}
