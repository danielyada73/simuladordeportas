// Camuflagem azul em SVG (blobs estilizados) + grade tática + vinheta.
// Renderiza no servidor, sem JS no cliente.
export function CamoBackground() {
  return (
    <div className="fixed inset-0 -z-0 pointer-events-none" aria-hidden>
      <div className="absolute inset-0 bg-camo-deep" />
      <svg
        className="absolute inset-0 w-full h-full opacity-[0.6]"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          <pattern id="camo-blobs" x="0" y="0" width="600" height="600" patternUnits="userSpaceOnUse">
            <rect width="600" height="600" fill="#0a1428" />
            <g fill="#15264a">
              <path d="M0,80 q60,-40 120,-10 q70,40 150,5 q80,-40 160,10 q70,50 170,-10 L600,0 L0,0 Z" />
              <ellipse cx="80" cy="220" rx="110" ry="55" />
              <ellipse cx="420" cy="180" rx="140" ry="70" />
              <ellipse cx="280" cy="380" rx="160" ry="80" />
              <ellipse cx="540" cy="500" rx="130" ry="60" />
            </g>
            <g fill="#2b4570" opacity="0.65">
              <ellipse cx="170" cy="100" rx="60" ry="28" />
              <ellipse cx="500" cy="280" rx="80" ry="40" />
              <ellipse cx="100" cy="420" rx="70" ry="35" />
              <ellipse cx="380" cy="540" rx="90" ry="45" />
            </g>
            <g fill="#050b1a" opacity="0.55">
              <ellipse cx="250" cy="160" rx="50" ry="22" />
              <ellipse cx="550" cy="80" rx="60" ry="30" />
              <ellipse cx="60" cy="320" rx="55" ry="25" />
              <ellipse cx="450" cy="450" rx="60" ry="28" />
            </g>
          </pattern>
          <pattern id="tactical-grid" x="0" y="0" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M48 0 H0 V48" fill="none" stroke="#22d3ee" strokeOpacity="0.04" strokeWidth="1" />
          </pattern>
          <radialGradient id="vignette" cx="50%" cy="40%" r="80%">
            <stop offset="0%" stopColor="transparent" />
            <stop offset="100%" stopColor="#020617" stopOpacity="0.8" />
          </radialGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#camo-blobs)" />
        <rect width="100%" height="100%" fill="url(#tactical-grid)" />
        <rect width="100%" height="100%" fill="url(#vignette)" />
      </svg>
    </div>
  );
}
