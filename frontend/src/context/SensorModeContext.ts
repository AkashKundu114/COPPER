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
    id: "eo",
    label: "EO TACTICAL",
    desc: "Electro-Optical Reconnaissance & Holographic HUD",
  },
  {
    id: "flir",
    label: "FLIR THERMAL",
    desc: "Forward-Looking Infrared Heat & Threat Telemetry",
  },
  {
    id: "nvg",
    label: "NVG NIGHT VISION",
    desc: "Tactical Phosphor Green Low-Light Amplification",
  },
  {
    id: "crt",
    label: "CYBER CRT",
    desc: "High-Bandwidth Terminal Scanlines & Signal Intercept",
  },
];

export const SensorModeContext = createContext<SensorModeContextType>({
  mode: "eo",
  setMode: () => {},
  cycleMode: () => {},
  modeLabel: "EO TACTICAL",
  modeDescription: "Electro-Optical Tactical Reconnaissance",
});

export const useSensorMode = () => useContext(SensorModeContext);
