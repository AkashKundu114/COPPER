import { useCallback, useEffect, useState } from "react";
import { Sidebar, type NavSection } from "./components/layout/Sidebar";
import { TopBar } from "./components/layout/TopBar";
import { CommandPalette } from "./components/common/CommandPalette";
import { GuardianChallengeModal, type GuardianChallengePayload } from "./components/chat/GuardianChallengeModal";
import { NeuralBrain } from "./components/brain/NeuralBrain";
import { ChatDock } from "./components/chat/ChatDock";
import { SpeakingBar } from "./components/chat/SpeakingBar";
import { SideDrawer } from "./components/profile/SideDrawer";
import { EmberParticles } from "./components/effects/EmberParticles";
import { useBrainSocket } from "./lib/useBrainSocket";
import { fetchAgents, fetchProfile, type AgentStats, type ProfileResponse } from "./lib/api";

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
  const [activeSection, setActiveSection] = useState<NavSection>("dashboard");
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
    connected, thinking, activeAgent, activeEdge, pulseSeq, speaking, speakingAgent, lines, send,
  } = useBrainSocket(refresh);

  const handleSelectAgent = (id: string) => {
    setSelectedAgent(id);
    setDrawerOpen(true);
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
        return <DashboardView />;
      case "chat":
        return (
          <div className="relative w-full h-full flex flex-col items-center justify-center">
            <NeuralBrain
              agentStats={agentStats}
              thinking={thinking}
              activeAgent={activeAgent}
              activeEdge={activeEdge}
              pulseSeq={pulseSeq}
              selectedAgent={selectedAgent}
              onSelectAgent={handleSelectAgent}
            />
            <div className="fixed bottom-6 left-64 right-0 px-8 z-20">
              <SpeakingBar speaking={speaking} agentId={speakingAgent} />
              <ChatDock lines={lines} connected={connected} thinking={thinking} onSend={send} />
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
    <div className="relative w-screen h-screen overflow-hidden bg-void flex">
      {}
      <EmberParticles />

      {}
      <Sidebar activeSection={activeSection} onSelectSection={setActiveSection} />

      {}
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
        <TopBar
          sectionTitle={activeSection.replace("-", " ")}
          profile={profile}
          drawerOpen={drawerOpen}
          onToggleDrawer={handleToggleDrawer}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        />

        <main className="flex-1 overflow-y-auto relative custom-scrollbar">
          {renderActiveSection()}
        </main>
      </div>

      {}
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
    </div>
  );
}
