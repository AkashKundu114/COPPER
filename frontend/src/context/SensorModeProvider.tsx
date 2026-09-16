import React, { useState, useEffect } from "react";
import {
  SensorModeContext,
  SENSOR_MODES,
  type SensorMode,
} from "./SensorModeContext";

export const SensorModeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [mode, setModeState] = useState<SensorMode>("crt");

  useEffect(() => {
    localStorage.setItem("copper_sensor_mode", "crt");
  }, [mode]);

  const setMode = (newMode: SensorMode) => {
    setModeState(newMode || "crt");
  };

  const cycleMode = () => {
    setModeState("crt");
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
