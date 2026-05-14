import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Cloud, Sun, CloudRain } from "lucide-react";

interface Weather {
  temp: number;
  condition: string;
  city: string;
  humidity: number;
}

function WeatherIcon({ condition }: { condition: string }) {
  const c = condition.toLowerCase();
  if (c.includes("rain")) return <CloudRain size={32} className="text-blue-400" />;
  if (c.includes("cloud")) return <Cloud size={32} className="text-gray-400" />;
  return <Sun size={32} className="text-yellow-400" />;
}

export function WeatherWidget() {
  const [weather, setWeather] = useState<Weather | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    // Open-Meteo free API – no key needed
    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const res = await fetch(
            `https://api.open-meteo.com/v1/forecast?latitude=${coords.latitude}&longitude=${coords.longitude}&current=temperature_2m,relative_humidity_2m,weathercode`
          );
          const data = await res.json();
          const cur = data.current;
          const code = cur.weathercode;
          const condition = code === 0 ? "Clear" : code < 50 ? "Cloudy" : code < 70 ? "Rainy" : "Stormy";
          setWeather({
            temp: Math.round(cur.temperature_2m),
            condition,
            city: "Local",
            humidity: cur.relative_humidity_2m,
          });
        } catch { setError(true); }
      },
      () => setError(true)
    );
  }, []);

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sun size={16} className="text-yellow-400" />
        <span className="text-sm font-medium text-gray-400">Weather</span>
      </div>
      {error && <p className="text-xs text-gray-600 text-center py-3">Location unavailable</p>}
      {!weather && !error && <p className="text-xs text-gray-600 text-center py-3">Loading...</p>}
      {weather && (
        <div className="flex items-center gap-4">
          <WeatherIcon condition={weather.condition} />
          <div>
            <p className="text-2xl font-bold text-white">{weather.temp}°C</p>
            <p className="text-xs text-gray-400">{weather.condition}</p>
            <p className="text-xs text-gray-600">Humidity: {weather.humidity}%</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
