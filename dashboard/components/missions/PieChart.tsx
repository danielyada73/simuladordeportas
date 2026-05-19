type Slice = { label: string; value: number; color: string };

export function PieChart({
  slices,
  size = 180,
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
  const r = size / 2 - 8;
  const innerR = r * 0.6;

  if (total === 0) {
    return (
      <div className="flex flex-col items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1d3a6f" strokeWidth="14" />
        </svg>
        <div className="absolute font-stencil text-camo-cyan/50 text-sm tracking-wider">SEM DADOS</div>
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
      <svg width={size} height={size} className="drop-shadow-[0_0_18px_rgba(34,211,238,0.15)]">
        {arcs.map((a, i) => (
          <path key={i} d={a.d} fill={a.color} stroke="#050b1a" strokeWidth="1.5">
            <title>{`${a.label}: ${a.value}`}</title>
          </path>
        ))}
        <circle cx={cx} cy={cy} r={innerR - 1} fill="none" stroke="#22d3ee" strokeOpacity="0.2" strokeWidth="1" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="font-stencil text-4xl tracking-wider text-camo-cyan leading-none">{centerValue ?? total}</div>
        {centerLabel && <div className="text-[10px] uppercase tracking-widest text-camo-cyan/60 mt-1">{centerLabel}</div>}
      </div>
    </div>
  );
}
