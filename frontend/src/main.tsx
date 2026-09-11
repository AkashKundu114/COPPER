import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { QuickBar } from "./components/ambient/QuickBar";

const isQuickBar = window.location.hash === "#/quick-bar";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {isQuickBar ? <QuickBar /> : <App />}
  </StrictMode>,
);
