import React, { useState, useEffect } from "react";
import {
  SensorModeContext,
  SENSOR_MODES,
  type SensorMode,
} from "./SensorModeContext";

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
