import React, { createContext, useContext, useState, useEffect } from "react";

export type SensorMode = "eo" | "flir" | "nvg" | "crt";

interface SensorModeContextType {
  mode: SensorMode;
  setMode: (mode: SensorMode) => void;
  cycleMode: () => void;
  modeLabel: string;
  modeDescription: string;
}

const SensorModeContext = createContext<SensorModeContextType>({
  mode: "eo",
  setMode: () => {},
  cycleMode: () => {},
  modeLabel: "EO TACTICAL",
  modeDescription: "Electro-Optical Tactical Reconnaissance",
});

const SENSOR_MODES: { id: SensorMode; label: string; desc: string }[] = [
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

export const SensorModeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [mode, setModeState] = useState<SensorMode>(() => {
    const saved = localStorage.getItem("copper_sensor_mode");
    return (saved as SensorMode) || "eo";
  });

  useEffect(() => {
    localStorage.setItem("copper_sensor_mode", mode);
  }, [mode]);

  const setMode = (newMode: SensorMode) => {
    setModeState(newMode);
  };

  const cycleMode = () => {
    const idx = SENSOR_MODES.findIndex((m) => m.id === mode);
    const nextIdx = (idx + 1) % SENSOR_MODES.length;
    setModeState(SENSOR_MODES[nextIdx].id);
  };

  const activeMeta =
    SENSOR_MODES.find((m) => m.id === mode) || SENSOR_MODES[0];

  return (
    <SensorModeContext.Provider
      value={{
        mode,
        setMode,
        cycleMode,
        modeLabel: activeMeta.label,
        modeDescription: activeMeta.desc,
      }}
    >
      {children}
    </SensorModeContext.Provider>
  );
};

export const useSensorMode = () => useContext(SensorModeContext);
