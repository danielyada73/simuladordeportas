import Link from "next/link";
import { Sparkles } from "lucide-react";
import { DemoBanner } from "@/components/DemoBanner";
import { NavTabs } from "@/components/NavTabs";

export default function PanelLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-grid">
      <DemoBanner />
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-bg/80 border-b border-border">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between gap-6">
          <Link href="/" className="flex items-center gap-3">
            <div className="relative w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-accent-soft flex items-center justify-center font-bold text-bg shadow-elevated">
              α
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-low ring-2 ring-bg" />
            </div>
            <div>
              <div className="font-semibold leading-tight text-[15px]">Alpha OS</div>
              <div className="text-[11px] text-muted leading-tight uppercase tracking-wider">Painel da Agência</div>
            </div>
          </Link>

          <NavTabs />

          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-muted-strong">
              <Sparkles className="w-3.5 h-3.5 text-accent" />
              <span>3 membros</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-medium to-accent flex items-center justify-center text-xs font-semibold">
              DA
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-[1600px] w-full mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
