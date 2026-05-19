import { CamoBackground } from "@/components/missions/CamoBackground";

export default function MissoesLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen relative text-text">
      <CamoBackground />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
