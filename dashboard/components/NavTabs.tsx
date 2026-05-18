"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Users, Building2 } from "lucide-react";

const TABS = [
  { href: "/", label: "Demandas", icon: Activity },
  { href: "/responsaveis", label: "Responsáveis", icon: Users },
  { href: "/clientes", label: "Clientes", icon: Building2 },
];

export function NavTabs() {
  const pathname = usePathname();
  return (
    <nav className="flex gap-1 bg-surface border border-border rounded-xl p-1">
      {TABS.map((t) => {
        const Icon = t.icon;
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm transition-all ${
              active
                ? "bg-bg text-text shadow-card"
                : "text-muted-strong hover:text-text"
            }`}
          >
            <Icon className="w-4 h-4" />
            {t.label}
          </Link>
        );
      })}
    </nav>
  );
}
