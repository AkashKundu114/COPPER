import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar, type NavSection } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { CommandPalette } from "./components/common/CommandPalette";
import { GuardianChallengeModal, type GuardianChallengePayload } from "./components/chat/GuardianChallengeModal";
import { ChatDock } from "./components/chat/ChatDock";
import { MessageFeed } from "./components/chat/MessageFeed";
import { SideDrawer } from "./components/profile/SideDrawer";
import { useBrainSocket } from "./lib/useBrainSocket";
import { fetchAgents, fetchProfile, type AgentStats, type ProfileResponse } from "./lib/api";
import { SpiderSenseToast } from "./components/alerts/SpiderSenseToast";

import { DashboardView } from "./pages/DashboardView";
import { TodayView } from "./pages/TodayView";
import { TasksView } from "./pages/TasksView";
import { ProjectsView } from "./pages/ProjectsView";
import { MemoryView } from "./pages/MemoryView";
import { ActivityView } from "./pages/ActivityView";
import { SelfImprovementView } from "./pages/SelfImprovementView";
import { FoodView } from "./pages/FoodView";
import { SettingsView } from "./pages/SettingsView";

import { AgentRegistry } from "./pages/AgentRegistry";
import { Insights } from "./pages/Insights";
import { SecurityCenter } from "./pages/SecurityCenter";

export default function App() {
  const [activeSection, setActiveSection] = useState<NavSection>("chat");
  const [agentStats, setAgentStats] = useState<Record<string, AgentStats>>({});
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [guardianChallenge, setGuardianChallenge] = useState<GuardianChallengePayload | null>(null);

  const refresh = useCallback(() => {
    fetchAgents()
      .then((list) => setAgentStats(Object.fromEntries(list.map((a) => [a.id, a]))))
      .catch(() => {});
    fetchProfile().then(setProfile).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const {
    connected, thinking, activeAgent, lines, send, sendSystemAction, alerts, dismissAlert,
  } = useBrainSocket(refresh);

  const handleToggleDrawer = () => {
    if (drawerOpen) {
      setDrawerOpen(false);
      setSelectedAgent(null);
    } else {
      setDrawerOpen(true);
    }
  };

  const renderActiveSection = () => {
    switch (activeSection) {
      case "dashboard":
        return <DashboardView />;
      case "chat":
        return (
          <div className="relative w-full h-full flex flex-col items-center">
            <MessageFeed 
              lines={lines} 
              agentStats={agentStats} 
              thinking={thinking} 
              activeAgent={activeAgent} 
            />
            <div className="w-full max-w-4xl px-6 pb-6">
              <ChatDock connected={connected} thinking={thinking} onSend={send} />
            </div>
          </div>
        );
      case "today":
        return <TodayView />;
      case "tasks":
        return <TasksView />;
      case "projects":
        return <ProjectsView />;
      case "memory":
        return <MemoryView />;
      case "agents":
        return <AgentRegistry />;
      case "activity":
        return <ActivityView />;
      case "insights":
        return <Insights />;
      case "self-improvement":
        return <SelfImprovementView />;
      case "security":
        return <SecurityCenter />;
      case "food":
        return <FoodView />;
      case "settings":
        return <SettingsView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-bg flex text-text">
      
      <Sidebar activeSection={activeSection} onSelectSection={setActiveSection} />

      <div className="flex-1 flex flex-col h-screen overflow-hidden relative border-l border-border">
        <TopBar
          sectionTitle={activeSection.replace("-", " ")}
          profile={profile}
          drawerOpen={drawerOpen}
          onToggleDrawer={handleToggleDrawer}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        />

        <main className="flex-1 overflow-hidden relative custom-scrollbar flex flex-col bg-bg">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 10, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.99 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              className="flex-1 w-full h-full"
            >
              {renderActiveSection()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectSection={setActiveSection}
      />

      <GuardianChallengeModal
        payload={guardianChallenge}
        onFollowRecommendation={() => setGuardianChallenge(null)}
        onProceedAnyway={() => setGuardianChallenge(null)}
        onDiscuss={() => {
          setActiveSection("chat");
          setGuardianChallenge(null);
        }}
      />

      <SideDrawer
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedAgent(null);
        }}
        profile={profile}
        agentStats={agentStats}
        selectedAgent={selectedAgent}
        onProfileReset={() => {
          refresh();
          setSelectedAgent(null);
        }}
      />

      <SpiderSenseToast
        alerts={alerts}
        onDismiss={(alertId) => {
          dismissAlert(alertId);
          sendSystemAction('dismiss', { alert_id: alertId });
        }}
        onAction={(alertId, action) => {
          dismissAlert(alertId);
          
          if (action.toLowerCase().includes('help') || action.toLowerCase().includes('ask')) {
            setActiveSection('chat');
          } else if (action.toLowerCase().includes('snooze')) {
            // Extract minutes, default to 15
            const match = action.match(/(\d+)/);
            const mins = match ? parseInt(match[1]) : 15;
            let duration = mins * 60;
            if (action.toLowerCase().includes('h')) duration = mins * 3600;
            
            sendSystemAction('snooze', { alert_id: alertId, duration });
          }
        }}
      />
    </div>
  );
}

