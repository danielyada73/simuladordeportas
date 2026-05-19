type Slice = { label: string; value: number; color: string };

export function PieChart({
  slices,
  size = 220,
  centerLabel,
  centerValue,
}: {
  slices: Slice[];
  size?: number;
  centerLabel?: string;
  centerValue?: string | number;
}) {
  const total = slices.reduce((acc, s) => acc + s.value, 0);
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 6;
  const innerR = r * 0.62;

  if (total === 0) {
    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="18" />
          <circle cx={cx} cy={cy} r={innerR} fill="rgba(255,255,255,0.02)" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white/30">
          <div className="font-stencil text-4xl leading-none">0</div>
          <div className="text-[10px] uppercase tracking-widest mt-1">Sem dados</div>
        </div>
      </div>
    );
  }

  let startAngle = -Math.PI / 2;
  const arcs = slices.map((s) => {
    const angle = (s.value / total) * Math.PI * 2;
    const endAngle = startAngle + angle;
    const x1 = cx + r * Math.cos(startAngle);
    const y1 = cy + r * Math.sin(startAngle);
    const x2 = cx + r * Math.cos(endAngle);
    const y2 = cy + r * Math.sin(endAngle);
    const xi1 = cx + innerR * Math.cos(startAngle);
    const yi1 = cy + innerR * Math.sin(startAngle);
    const xi2 = cx + innerR * Math.cos(endAngle);
    const yi2 = cy + innerR * Math.sin(endAngle);
    const largeArc = angle > Math.PI ? 1 : 0;
    const d = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${xi2} ${yi2} A ${innerR} ${innerR} 0 ${largeArc} 0 ${xi1} ${yi1} Z`;
    startAngle = endAngle;
    return { d, color: s.color, label: s.label, value: s.value };
  });

  return (
    <div className="relative inline-block">
      <svg width={size} height={size}>
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        {/* anel externo discreto */}
        <circle cx={cx} cy={cy} r={r + 4} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />
        {arcs.map((a, i) => (
          <path key={i} d={a.d} fill={a.color} opacity="0.95">
            <title>{`${a.label}: ${a.value}`}</title>
          </path>
        ))}
        {/* anel interno (efeito vidro) */}
        <circle cx={cx} cy={cy} r={innerR} fill="rgba(10,13,20,0.6)" />
        <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="font-stencil text-5xl text-white leading-none">{centerValue ?? total}</div>
        {centerLabel && <div className="text-[10px] uppercase tracking-[0.2em] text-white/40 mt-2">{centerLabel}</div>}
      </div>
    </div>
  );
}
