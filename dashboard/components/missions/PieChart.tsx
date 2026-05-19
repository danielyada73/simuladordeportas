type Slice = { label: string; value: number; color: string };

export function PieChart({
  slices,
  size = 240,
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
  const r = size / 2 - 4;
  const stroke = 20;
  const circumference = 2 * Math.PI * (r - stroke / 2);

  if (total === 0) {
    return (
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={cx} cy={cy} r={r - stroke / 2} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={stroke} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white/30">
          <div className="font-stencil text-6xl leading-none">0</div>
          <div className="text-xs uppercase tracking-widest mt-2">Sem dados</div>
        </div>
      </div>
    );
  }

  let offset = 0;
  return (
    <div className="relative inline-block">
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        {/* track */}
        <circle cx={cx} cy={cy} r={r - stroke / 2} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth={stroke} />
        {slices.map((s, i) => {
          const len = (s.value / total) * circumference;
          const arc = (
            <circle
              key={i}
              cx={cx}
              cy={cy}
              r={r - stroke / 2}
              fill="none"
              stroke={s.color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${len} ${circumference - len}`}
              strokeDashoffset={-offset}
            >
              <title>{`${s.label}: ${s.value}`}</title>
            </circle>
          );
          offset += len;
          return arc;
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="font-stencil text-7xl text-white leading-none tracking-wide">{centerValue ?? total}</div>
        {centerLabel && (
          <div className="text-[11px] uppercase tracking-[0.25em] text-white/45 mt-2.5">{centerLabel}</div>
        )}
      </div>
    </div>
  );
}
