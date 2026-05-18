import { TriangleAlert } from "lucide-react";
import { DEMO_MODE } from "@/lib/api";

export function DemoBanner() {
  if (!DEMO_MODE) return null;
  return (
    <div className="bg-accent/10 border-b border-accent/30 text-accent">
      <div className="max-w-[1600px] mx-auto px-6 py-2 flex items-center gap-2 text-xs">
        <TriangleAlert className="w-3.5 h-3.5" />
        <span className="font-medium">MODO DEMONSTRAÇÃO</span>
        <span className="text-accent/70">— dados fictícios. Defina DEMO_MODE=false e configure API_BASE_URL pra ler do Monday real.</span>
      </div>
    </div>
  );
}
