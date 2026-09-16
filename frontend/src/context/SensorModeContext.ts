import { createContext, useContext } from "react";

export type SensorMode = "eo" | "flir" | "nvg" | "crt";

export interface SensorModeContextType {
  mode: SensorMode;
  setMode: (mode: SensorMode) => void;
  cycleMode: () => void;
  modeLabel: string;
  modeDescription: string;
}

export const SENSOR_MODES: { id: SensorMode; label: string; desc: string }[] = [
  {
    id: "crt",
    label: "CYBER CRT",
    desc: "High-Bandwidth Terminal Scanlines & Signal Intercept",
  },
];

export const SensorModeContext = createContext<SensorModeContextType>({
  mode: "crt",
  setMode: () => {},
  cycleMode: () => {},
  modeLabel: "CYBER CRT",
  modeDescription: "High-Bandwidth Terminal Scanlines & Signal Intercept",
});

export const useSensorMode = () => useContext(SensorModeContext);
