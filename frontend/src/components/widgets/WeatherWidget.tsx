import { useEffect, useState } from "react";
import { Sun, Cloud, CloudRain, CloudLightning, MapPinOff } from "lucide-react";

interface Weather {
  temp: number;
  code: number;
}

function WeatherIcon({ code }: { code: number }) {
  if (code >= 95) return <CloudLightning size={22} className="text-copper-flare" />;
  if (code >= 51) return <CloudRain size={22} className="text-spark" />;
  if (code >= 2) return <Cloud size={22} className="text-ink-secondary" />;
  return <Sun size={22} className="text-copper-hot" />;
}

function label(code: number): string {
  if (code >= 95) return "Stormy";
  if (code >= 71) return "Snowy";
  if (code >= 51) return "Rainy";
  if (code >= 2) return "Cloudy";
  return "Clear";
}

export function WeatherWidget() {
  const [weather, setWeather] = useState<Weather | null>(null);
  const [status, setStatus] = useState<"loading" | "ok" | "denied">("loading");

  useEffect(() => {
    if (!navigator.geolocation) {
      setStatus("denied");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const res = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${coords.latitude}&longitude=${coords.longitude}&current=temperature_2m,weathercode`
          );
          const data = await res.json();
          setWeather({ temp: Math.round(data.current.temperature_2m), code: data.current.weathercode });
          setStatus("ok");
        } catch {
          setStatus("denied");
        }
      },
      () => setStatus("denied"),
      { timeout: 5000 }
    );
  }, []);

  return (
    <div className="rounded-xl border border-copper-dim/40 bg-void-panel/70 backdrop-blur-md px-4 py-3 min-w-[150px]">
      {status === "loading" && <p className="text-xs text-ink-faint font-mono">Locating…</p>}
      {status === "denied" && (
        <div className="flex items-center gap-2 text-ink-faint">
          <MapPinOff size={16} />
          <p className="text-xs font-mono">Location unavailable</p>
        </div>
      )}
      {status === "ok" && weather && (
        <div className="flex items-center gap-3">
          <WeatherIcon code={weather.code} />
          <div>
            <p className="font-display font-semibold text-xl text-ink-primary leading-none">{weather.temp}°</p>
            <p className="font-mono text-[10px] text-ink-faint uppercase tracking-wider mt-1">{label(weather.code)}</p>
          </div>
        </div>
      )}
    </div>
  );
}
