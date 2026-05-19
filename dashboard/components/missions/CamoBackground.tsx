// Fundo SaaS premium: navy profundo com glow radial laranja sutil no topo.
// Inspiração: Phoenix/ZEUS-X dashboard.
export function CamoBackground() {
  return (
    <div className="fixed inset-0 -z-0 pointer-events-none" aria-hidden>
      <div className="absolute inset-0 bg-[#0a0d14]" />
      <div
        className="absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(ellipse 70% 50% at 50% -10%, rgba(255,90,31,0.18) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 20% 100%, rgba(34,211,238,0.08) 0%, transparent 60%)",
        }}
      />
      {/* grade fina */}
      <svg className="absolute inset-0 w-full h-full opacity-[0.15]" aria-hidden>
        <defs>
          <pattern id="g" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M40 0H0V40" fill="none" stroke="#ffffff" strokeOpacity="0.03" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#g)" />
      </svg>
    </div>
  );
}
