import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import Dashboard from "@/pages/Dashboard";
import Chat from "@/pages/Chat";
import Memory from "@/pages/Memory";
import Reminders from "@/pages/Reminders";
import Automation from "@/pages/Automation";
import Settings from "@/pages/Settings";
import AgentRegistry from "@/pages/AgentRegistry";
import SecurityCenter from "@/pages/SecurityCenter";
import Insights from "@/pages/Insights";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/memory" element={<Memory />} />
      <Route path="/reminders" element={<Reminders />} />
      <Route path="/automation" element={<Automation />} />
      <Route path="/insights" element={<Insights />} />
      <Route path="/agents" element={<AgentRegistry />} />
      <Route path="/security" element={<SecurityCenter />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  );
}
