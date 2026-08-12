



interface Ember {
  left: number;
  size: number;
  duration: number;
  delay: number;
  drift: number;
}

const EMBERS: Ember[] = Array.from({ length: 18 }, (_, i) => {
  const seed = (i * 2654435761) % 1000;
  return {
    left: (seed % 100),
    size: 1.5 + (seed % 3),
    duration: 14 + (seed % 12),
    delay: (seed % 14),
    drift: ((seed % 60) - 30),
  };
});

export function EmberParticles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {EMBERS.map((e, i) => (
        <span
          key={i}
          className="absolute bottom-0 bg-white"
          style={{
            left: `${e.left}%`,
            width: e.size,
            height: e.size,
            opacity: 0,
            boxShadow: "none",
            animation: `ember-rise ${e.duration}s linear infinite`,
            animationDelay: `${e.delay}s`,
            
            ["--drift" as string]: `${e.drift}px`,
          }}
        />
      ))}
    </div>
  );
}
