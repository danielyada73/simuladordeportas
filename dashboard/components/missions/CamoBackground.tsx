// Background minimal: preto solido + glow radial azul muito sutil.
export function CamoBackground() {
  return (
    <div className="fixed inset-0 -z-0 pointer-events-none" aria-hidden>
      <div className="absolute inset-0 bg-ms-bg" />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 40% at 50% -10%, rgba(0,180,252,0.10) 0%, transparent 60%)",
        }}
      />
    </div>
  );
}
