import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sidebar, type NavSection } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { CommandPalette } from "./components/common/CommandPalette";
import {
  GuardianChallengeModal,
  type GuardianChallengePayload,
} from "./components/chat/GuardianChallengeModal";
import { ChatDock } from "./components/chat/ChatDock";
import { MessageFeed } from "./components/chat/MessageFeed";
import { SideDrawer } from "./components/profile/SideDrawer";
import { useBrainSocket } from "./hooks/useBrainSocket";
import {
  fetchAgents,
  fetchProfile,
  type AgentStats,
  type ProfileResponse,
} from "./lib/api";
import { SpiderSenseToast } from "./components/alerts/SpiderSenseToast";
import { CompanionHUDView } from "./pages/CompanionHUDView";
import { BranchHeader } from "./components/chat/BranchHeader";
import { BranchCompareModal } from "./components/chat/BranchCompareModal";
import { branchingAPI, type BranchItem } from "./services/api";

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
import { BenchmarkMetricsView } from "./pages/BenchmarkMetricsView";
import { SensorModeProvider } from "./context/SensorModeProvider";
import { useSensorMode } from "./context/SensorModeContext";

function MainApp() {
  const { mode } = useSensorMode();
  const [activeSection, setActiveSection] = useState<NavSection>("dashboard");
  const [agentStats, setAgentStats] = useState<Record<string, AgentStats>>({});
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [guardianChallenge, setGuardianChallenge] =
    useState<GuardianChallengePayload | null>(null);
  const [branches, setBranches] = useState<BranchItem[]>([]);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [activeBranchId, setActiveBranchId] = useState<string>("default");

  const refresh = useCallback(() => {
    fetchAgents()
      .then((list) =>
        setAgentStats(Object.fromEntries(list.map((a) => [a.id, a]))),
      )
      .catch(() => {});
    fetchProfile()
      .then(setProfile)
      .catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const {
    connected,
    thinking,
    activeAgent,
    lines,
    send,
    sendSystemAction,
    alerts,
    dismissAlert,
    stopAudio,
    speaking,
    activeTaskGraph,
    activeComputerUse,
    clearChat,
    setSessionId,
  } = useBrainSocket(refresh);

  const refreshBranches = useCallback((targetId?: string) => {
    const sessionToFetch = targetId || activeBranchId || "default";
    branchingAPI
      .getBranches(sessionToFetch)
      .then((res) => {
        if (res.data?.branches) {
          setBranches(res.data.branches);
        }
      })
      .catch(() => {});
  }, [activeBranchId]);

  useEffect(() => {
    refreshBranches("default");
  }, [refreshBranches]);

  const handleBranchAtMessage = async (messageIndex: number, messageText: string) => {
    try {
      const title = messageText.trim().slice(0, 30) || `Branch @ #${messageIndex + 1}`;
      const res = await branchingAPI.createBranch(activeBranchId, messageIndex, title);
      const newBranch = res.data;
      if (newBranch && newBranch.branch_id) {
        setActiveBranchId(newBranch.branch_id);
        setSessionId(newBranch.branch_id);
        refreshBranches(newBranch.branch_id);
      }
    } catch (err) {
      console.error("Failed to create branch:", err);
    }
  };

  const handleSelectBranch = (branchId: string) => {
    setActiveBranchId(branchId);
    setSessionId(branchId);
    refreshBranches(branchId);
  };

  const handleMergeBranch = async (branchId: string) => {
    try {
      await branchingAPI.mergeBranch(branchId, "default");
      setActiveBranchId("default");
      setSessionId("default");
      refreshBranches("default");
    } catch (err) {
      console.error("Failed to merge branch:", err);
    }
  };

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
        return <DashboardView onNavigate={setActiveSection} />;
      case "companion":
        return (
          <CompanionHUDView
            lines={lines}
            thinking={thinking}
            speaking={speaking}
            connected={connected}
            onSend={send}
            stopAudio={stopAudio}
            clearChat={clearChat}
          />
        );
      case "chat":
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-between min-h-0">
            <div className="w-full max-w-[850px] pt-1 px-4 flex-shrink-0">
              <BranchHeader
                activeBranchId={activeBranchId}
                branches={branches}
                onSelectBranch={handleSelectBranch}
                onOpenCompare={() => setIsCompareModalOpen(true)}
                onMergeBranch={handleMergeBranch}
              />
            </div>
            <MessageFeed
              lines={lines}
              agentStats={agentStats}
              thinking={thinking}
              activeAgent={activeAgent}
              activeTaskGraph={activeTaskGraph}
              activeComputerUse={activeComputerUse}
              onBranchAtMessage={handleBranchAtMessage}
            />
            <div className="w-full max-w-[850px] px-4 pb-6 mt-auto flex-shrink-0">
              <ChatDock
                connected={connected}
                thinking={thinking}
                speaking={speaking}
                onSend={send}
                onStop={stopAudio}
                onClear={clearChat}
              />
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
      case "benchmarks":
        return <BenchmarkMetricsView />;
      case "self-improvement":
        return <SelfImprovementView />;
      case "security":
        return <SecurityCenter />;
      case "food":
        return <FoodView />;
      case "settings":
        return <SettingsView />;
      default:
        return <DashboardView onNavigate={setActiveSection} />;
    }
  };

  return (
    <div
      className={`relative w-screen h-screen overflow-hidden flex bg-bg text-text font-body transition-all duration-500 sensor-${mode}`}
    >
      {/* CRT Scanline Overlay Strip */}
      {mode === "crt" && (
        <div className="absolute inset-0 pointer-events-none scanlines-overlay z-50 opacity-60" />
      )}

      <Sidebar activeSection={activeSection} onSelectSection={setActiveSection} />
      <main className="flex-1 min-h-0 relative flex flex-col overflow-hidden bg-bg">
        <TopBar
          sectionTitle={activeSection}
          profile={profile}
          drawerOpen={drawerOpen}
          onToggleDrawer={handleToggleDrawer}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        />
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className={`flex-1 w-full min-h-0 flex flex-col ${
              activeSection === "chat" ? "overflow-hidden" : "overflow-y-auto custom-scrollbar"
            }`}
          >
            {renderActiveSection()}
          </motion.div>
        </AnimatePresence>
      </main>

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

      <BranchCompareModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        branches={branches}
        currentBranchId={activeBranchId}
        onMerged={() => {
          refreshBranches("default");
          setActiveBranchId("default");
          setSessionId("default");
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
          sendSystemAction("dismiss", { alert_id: alertId });
        }}
        onAction={(alertId, action) => {
          dismissAlert(alertId);

          if (
            action.toLowerCase().includes("help") ||
            action.toLowerCase().includes("ask")
          ) {
            setActiveSection("chat");
          } else if (action.toLowerCase().includes("snooze")) {
            const match = action.match(/(\d+)/);
            const mins = match ? parseInt(match[1]) : 15;
            let duration = mins * 60;
            if (action.toLowerCase().includes("h")) duration = mins * 3600;

            sendSystemAction("snooze", { alert_id: alertId, duration });
          }
        }}
      />
    </div>
  );
}

export default function App() {
  return (
    <SensorModeProvider>
      <MainApp />
    </SensorModeProvider>
  );
}
