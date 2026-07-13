import { useCallback, useEffect, useState } from "react";
import { NeuralBrain } from "./components/brain/NeuralBrain";
import { ChatDock } from "./components/chat/ChatDock";
import { SideDrawer } from "./components/profile/SideDrawer";
import { TopBar } from "./components/layout/TopBar";
import { useBrainSocket } from "./lib/useBrainSocket";
import { fetchAgents, fetchProfile, type AgentStats, type ProfileResponse } from "./lib/api";

export default function App() {
  const [agentStats, setAgentStats] = useState<Record<string, AgentStats>>({});
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const refresh = useCallback(() => {
    fetchAgents()
      .then((list) => setAgentStats(Object.fromEntries(list.map((a) => [a.id, a]))))
      .catch(() => {});
    fetchProfile().then(setProfile).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const { connected, thinking, activeAgent, activeEdge, pulseSeq, lines, send } = useBrainSocket(refresh);

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

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-void">
      {/* Ambient background glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse at center, rgba(184,115,51,0.07) 0%, transparent 60%)",
        }}
      />

      <TopBar profile={profile} drawerOpen={drawerOpen} onToggleDrawer={handleToggleDrawer} />

      <main className="w-full h-full flex items-center justify-center px-4">
        <NeuralBrain
          agentStats={agentStats}
          thinking={thinking}
          activeAgent={activeAgent}
          activeEdge={activeEdge}
          pulseSeq={pulseSeq}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
        />
      </main>

      <div className="fixed bottom-6 left-0 right-0 px-4 z-20">
        <ChatDock lines={lines} connected={connected} thinking={thinking} onSend={send} />
      </div>

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
