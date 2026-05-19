// Fundo tático: navy profundo + linhas topográficas + grade fina + grain.
// Sem blobs cartoon. Inspiração: HUD militar / briefing room.
export function CamoBackground() {
  return (
    <div className="fixed inset-0 -z-0 pointer-events-none" aria-hidden>
      {/* Base com gradient sutil */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, #0d1b36 0%, #050b1a 60%, #02060f 100%)",
        }}
      />

      <svg
        className="absolute inset-0 w-full h-full"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          {/* Grade tática fina */}
          <pattern id="tac-grid" x="0" y="0" width="64" height="64" patternUnits="userSpaceOnUse">
            <path d="M64 0 H0 V64" fill="none" stroke="#22d3ee" strokeOpacity="0.035" strokeWidth="1" />
          </pattern>
          {/* Sub-grade mais densa */}
          <pattern id="tac-grid-fine" x="0" y="0" width="16" height="16" patternUnits="userSpaceOnUse">
            <path d="M16 0 H0 V16" fill="none" stroke="#22d3ee" strokeOpacity="0.012" strokeWidth="0.5" />
          </pattern>
          {/* Linhas topográficas (curvas suaves no fundo) */}
          <pattern id="topo" x="0" y="0" width="800" height="600" patternUnits="userSpaceOnUse">
            <g fill="none" stroke="#22d3ee" strokeOpacity="0.06" strokeWidth="0.7">
              <path d="M 0 480 Q 200 440 400 470 T 800 460" />
              <path d="M 0 500 Q 200 470 400 495 T 800 488" />
              <path d="M 0 520 Q 200 495 400 515 T 800 510" />
              <path d="M 0 540 Q 200 520 400 535 T 800 530" />
              <path d="M 0 80 Q 150 110 350 95 T 800 100" />
              <path d="M 0 60 Q 150 90 350 75 T 800 80" />
              <path d="M 0 40 Q 150 70 350 55 T 800 60" />
            </g>
          </pattern>
          {/* Noise / grain bem leve */}
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" />
            <feColorMatrix
              values="0 0 0 0 0
                      0 0 0 0 0
                      0 0 0 0 0
                      0 0 0 0.04 0"
            />
          </filter>
          <radialGradient id="vignette" cx="50%" cy="50%" r="80%">
            <stop offset="40%" stopColor="transparent" />
            <stop offset="100%" stopColor="#01040c" stopOpacity="0.85" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#topo)" />
        <rect width="100%" height="100%" fill="url(#tac-grid)" />
        <rect width="100%" height="100%" fill="url(#tac-grid-fine)" />
        <rect width="100%" height="100%" filter="url(#grain)" />
        <rect width="100%" height="100%" fill="url(#vignette)" />
      </svg>
    </div>
  );
}
