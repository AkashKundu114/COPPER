import { useEffect, useState } from "react";
import { Sun, Cloud, CloudRain, CloudLightning, MapPinOff } from "lucide-react";

interface Weather {
  temp: number;
  code: number;
}

function WeatherIcon({ code }: { code: number }) {
  if (code >= 95) return <CloudLightning size={22} className="text-zinc-100" />;
  if (code >= 51) return <CloudRain size={22} className="text-zinc-300" />;
  if (code >= 2) return <Cloud size={22} className="text-zinc-400" />;
  return <Sun size={22} className="text-white" />;
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
            `https://api.open-meteo.com/v1/forecast?latitude=${coords.latitude}&longitude=${coords.longitude}&current=temperature_2m,weathercode`,
          );
          const data = await res.json();
          setWeather({
            temp: Math.round(data.current.temperature_2m),
            code: data.current.weathercode,
          });
          setStatus("ok");
        } catch {
          setStatus("denied");
        }
      },
      () => setStatus("denied"),
      { timeout: 5000 },
    );
  }, []);

  return (
    <div className="rounded-none border border-zinc-800 bg-void-panel px-4 py-3 min-w-[150px]">
      {status === "loading" && (
        <p className="text-xs text-ink-faint font-mono">Locating…</p>
      )}
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
            <p className="font-display font-semibold text-xl text-white leading-none">
              {weather.temp}°
            </p>
            <p className="font-mono text-[10px] text-ink-faint uppercase tracking-wider mt-1">
              {label(weather.code)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
