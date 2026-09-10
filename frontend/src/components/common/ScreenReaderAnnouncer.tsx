import React, { createContext, useContext, useState, useCallback, type ReactNode } from "react";

type Politeness = "polite" | "assertive";

interface ScreenReaderContextType {
  announce: (message: string, politeness?: Politeness) => void;
}

const ScreenReaderContext = createContext<ScreenReaderContextType>({
  announce: () => {},
});

export const useAnnounce = () => useContext(ScreenReaderContext);

interface ProviderProps {
  children: ReactNode;
}

export const ScreenReaderProvider: React.FC<ProviderProps> = ({ children }) => {
  const [politeMessage, setPoliteMessage] = useState("");
  const [assertiveMessage, setAssertiveMessage] = useState("");

  const announce = useCallback((message: string, politeness: Politeness = "polite") => {
    if (!message) return;
    if (politeness === "assertive") {
      setAssertiveMessage("");
      setTimeout(() => setAssertiveMessage(message), 50);
    } else {
      setPoliteMessage("");
      setTimeout(() => setPoliteMessage(message), 50);
    }
  }, []);

  return (
    <ScreenReaderContext.Provider value={{ announce }}>
      {children}
      {/* Visually hidden live regions for screen reader announcements */}
      <div className="sr-only" aria-live="polite" aria-atomic="true" role="status" id="sr-polite-announcements">
        {politeMessage}
      </div>
      <div className="sr-only" aria-live="assertive" aria-atomic="true" role="alert" id="sr-assertive-announcements">
        {assertiveMessage}
      </div>
    </ScreenReaderContext.Provider>
  );
};
