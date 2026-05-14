import { BrowserRouter } from "react-router-dom";
import { useLocation } from "react-router-dom";
import { AppRoutes } from "@/routes";
import { Sidebar } from "@/components/common/Sidebar";
import { Navbar } from "@/components/common/Navbar";
import { NotificationPanel } from "@/components/system/NotificationPanel";
import { useSettingsStore } from "@/store/settingsStore";

function Shell() {
  const { pathname } = useLocation();
  const { enableScanline } = useSettingsStore();
  const isHome = pathname === "/";

  if (isHome) {
    return (
      <div className="h-screen overflow-hidden">
        {enableScanline && <div className="scanline" />}
        <AppRoutes />
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden">
      {enableScanline && <div className="scanline" />}
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-hidden">
          <AppRoutes />
        </main>
      </div>
      <NotificationPanel />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
