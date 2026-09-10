import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NeuralBrain, type NeuralBrainProps } from "../components/brain/NeuralBrain";
import { ChatDock } from "../components/chat/ChatDock";
import { MessageFeed } from "../components/chat/MessageFeed";
import { CommandPalette } from "../components/common/CommandPalette";
import { GuardianChallengeModal } from "../components/chat/GuardianChallengeModal";
import { ScreenReaderProvider, useAnnounce } from "../components/common/ScreenReaderAnnouncer";
import { Sidebar } from "../components/layout/Sidebar";
import { TopBar } from "../components/layout/TopBar";
import { AGENTS } from "../constants/agents";

// Mock helper component to test useAnnounce
function TestAnnouncerComponent({ message, politeness }: { message: string; politeness?: "polite" | "assertive" }) {
  const { announce } = useAnnounce();
  return (
    <button onClick={() => announce(message, politeness)}>
      Trigger Announcement
    </button>
  );
}

describe("Accessibility (a11y) Audit Suite", () => {
  describe("Screen Reader Announcer & Live Regions", () => {
    it("renders live regions with correct aria-live and role attributes", () => {
      render(
        <ScreenReaderProvider>
          <div>App Content</div>
        </ScreenReaderProvider>
      );

      const politeRegion = document.getElementById("sr-polite-announcements");
      expect(politeRegion).toHaveAttribute("aria-live", "polite");
      expect(politeRegion).toHaveAttribute("role", "status");
      expect(politeRegion).toHaveAttribute("aria-atomic", "true");

      const assertiveRegion = document.getElementById("sr-assertive-announcements");
      expect(assertiveRegion).toHaveAttribute("aria-live", "assertive");
      expect(assertiveRegion).toHaveAttribute("role", "alert");
      expect(assertiveRegion).toHaveAttribute("aria-atomic", "true");
    });

    it("announces messages into live region when triggered", async () => {
      const user = userEvent.setup();
      render(
        <ScreenReaderProvider>
          <TestAnnouncerComponent message="Test status update" politeness="polite" />
        </ScreenReaderProvider>
      );

      const btn = screen.getByRole("button", { name: /trigger announcement/i });
      await user.click(btn);

      const politeRegion = document.getElementById("sr-polite-announcements");
      await waitFor(() => {
        expect(politeRegion).toHaveTextContent("Test status update");
      });
    });
  });

  describe("Neural Brain Visualization a11y", () => {
    const defaultProps: NeuralBrainProps = {
      agentStats: {
        CHRONOS: {
          id: "CHRONOS",
          name: "Chronos",
          tier: "MODEL_1_CORE",
          tier_label: "Core Reasoning & Planning",
          color: "#10b981",
          domain: "Architecture & Planning",
          blurb: "Breaks big asks into phased roadmaps.",
          times_invoked: 15,
          familiarity_score: 0.8,
          familiarity_tier: "Trusted Partner",
          glow: 0.75,
          last_active: "Just now",
        },
      },
      thinking: true,
      activeAgent: "CHRONOS",
      activeEdge: null,
      pulseSeq: 0,
      selectedAgent: "CHRONOS",
      onSelectAgent: vi.fn(),
    };

    it("has accessible region role and accessible label", () => {
      render(<NeuralBrain {...defaultProps} />);
      const region = screen.getByRole("region", { name: /copper neural brain visualization/i });
      expect(region).toBeInTheDocument();
    });

    it("provides visually hidden screen reader alternative directory of all agents", () => {
      render(<NeuralBrain {...defaultProps} />);
      expect(screen.getByRole("heading", { name: /agent neural network overview/i, level: 2 })).toBeInTheDocument();
      expect(screen.getByText(/COPPER Core Engine Status: Thinking and reasoning active/i)).toBeInTheDocument();

      // Ensure screen reader directory buttons exist for each agent
      const firstAgent = AGENTS[0];
      const srButton = screen.getByRole("button", { name: new RegExp(`Select ${firstAgent.name}:`, "i") });
      expect(srButton).toBeInTheDocument();
    });

    it("renders core with role='group' and live thinking status label", () => {
      render(<NeuralBrain {...defaultProps} />);
      const core = screen.getByTestId("copper-core");
      expect(core).toHaveAttribute("role", "group");
      expect(core).toHaveAttribute("aria-label", expect.stringContaining("COPPER Core Engine: Active Reasoning"));
    });

    it("has accessible agent buttons with aria-pressed, aria-label, and keyboard support", () => {
      const handleSelect = vi.fn();
      render(<NeuralBrain {...defaultProps} onSelectAgent={handleSelect} />);

      // The SVG interactive node circle
      const chronosSvgButton = screen.getByRole("button", { name: /^Chronos,/i });
      expect(chronosSvgButton).toHaveAttribute("aria-label");
      expect(chronosSvgButton).toHaveAttribute("tabindex", "0");
      expect(chronosSvgButton).toHaveAttribute("aria-pressed", "true");

      fireEvent.keyDown(chronosSvgButton, { key: "Enter" });
      expect(handleSelect).toHaveBeenCalledWith("CHRONOS");
    });
  });

  describe("Chat Interface a11y", () => {
    it("renders ChatDock with accessible input, plus, mic, and mode dropdown controls", async () => {
      const user = userEvent.setup();
      const handleSend = vi.fn();
      render(
        <ChatDock
          connected={true}
          thinking={false}
          onSend={handleSend}
        />
      );

      // Chat input textarea
      const textarea = screen.getByRole("textbox", { name: /message input for copper intelligence/i });
      expect(textarea).toBeInTheDocument();

      // Plus attach button
      const attachBtn = screen.getByRole("button", { name: /attach reconnaissance documents/i });
      expect(attachBtn).toBeInTheDocument();

      // Voice record button
      const micBtn = screen.getByRole("button", { name: /start voice recording/i });
      expect(micBtn).toBeInTheDocument();

      // Cognitive mode dropdown button
      const modeBtn = screen.getByRole("button", { name: /cognitive intelligence mode:/i });
      expect(modeBtn).toHaveAttribute("aria-haspopup", "listbox");
      expect(modeBtn).toHaveAttribute("aria-expanded", "false");

      // Open dropdown
      await user.click(modeBtn);
      expect(modeBtn).toHaveAttribute("aria-expanded", "true");

      const listbox = screen.getByRole("listbox", { name: /cognitive intelligence modes/i });
      expect(listbox).toBeInTheDocument();

      const options = screen.getAllByRole("option");
      expect(options.length).toBe(5);

      // Select another mode
      await user.click(options[1]);
      expect(modeBtn).toHaveAttribute("aria-expanded", "false");
    });

    it("supports keyboard Escape key to close Cognitive Mode dropdown", async () => {
      const user = userEvent.setup();
      render(
        <ChatDock
          connected={true}
          thinking={false}
          onSend={vi.fn()}
        />
      );

      const modeBtn = screen.getByRole("button", { name: /cognitive intelligence mode:/i });
      await user.click(modeBtn);
      expect(modeBtn).toHaveAttribute("aria-expanded", "true");

      fireEvent.keyDown(window, { key: "Escape" });
      expect(modeBtn).toHaveAttribute("aria-expanded", "false");
    });

    it("renders MessageFeed with role='log' and message articles", () => {
      const lines = [
        { id: "1", text: "Hello COPPER", agent: "YOU", timestamp: Date.now() },
        { id: "2", text: "Greetings, Operator. Neural mesh ready.", agent: "CHRONOS", timestamp: Date.now() },
      ];

      render(
        <MessageFeed
          lines={lines}
          agentStats={{}}
          thinking={false}
          activeAgent={null}
        />
      );

      const log = screen.getByRole("log", { name: /conversation message history/i });
      expect(log).toBeInTheDocument();

      const articles = screen.getAllByRole("article");
      expect(articles.length).toBe(2);
      expect(articles[0]).toHaveAttribute("aria-label", "Message from Operator");
      expect(articles[1]).toHaveAttribute("aria-label", "Response from CHRONOS");
    });
  });

  describe("Command Palette Keyboard Navigation & Roles", () => {
    it("has role='dialog', combobox, listbox, and supports keyboard arrow navigation and Escape", () => {
      const handleClose = vi.fn();
      const handleSelectSection = vi.fn();

      render(
        <CommandPalette
          open={true}
          onClose={handleClose}
          onSelectSection={handleSelectSection}
        />
      );

      const dialog = screen.getByRole("dialog", { name: /command palette/i });
      expect(dialog).toHaveAttribute("aria-modal", "true");

      const combobox = screen.getByRole("combobox");
      expect(combobox).toBeInTheDocument();

      const listbox = screen.getByRole("listbox", { name: /command suggestions/i });
      expect(listbox).toBeInTheDocument();

      const options = screen.getAllByRole("option");
      expect(options[0]).toHaveAttribute("aria-selected", "true");

      // Arrow Down moves active option
      fireEvent.keyDown(combobox, { key: "ArrowDown" });
      expect(options[1]).toHaveAttribute("aria-selected", "true");

      // Enter selects active option
      fireEvent.keyDown(combobox, { key: "Enter" });
      expect(handleSelectSection).toHaveBeenCalled();
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe("Guardian Challenge Modal a11y", () => {
    it("has role='alertdialog' and supports Escape dismissal", () => {
      const handleFollowRec = vi.fn();
      const payload = {
        level: 2,
        reasoning: "Potential safety constraint violation",
        evidence: ["Policy conflict #41"],
        confidence: "95%",
        recommendation: "Review parameters before executing",
      };

      render(
        <GuardianChallengeModal
          payload={payload}
          onFollowRecommendation={handleFollowRec}
          onDiscuss={vi.fn()}
          onProceedAnyway={vi.fn()}
        />
      );

      const alertdialog = screen.getByRole("alertdialog");
      expect(alertdialog).toHaveAttribute("aria-modal", "true");

      fireEvent.keyDown(window, { key: "Escape" });
      expect(handleFollowRec).toHaveBeenCalled();
    });
  });

  describe("Landmarks & Navigation a11y", () => {
    it("renders Sidebar with landmark navigation and aria-current on active item", () => {
      render(
        <Sidebar
          activeSection="dashboard"
          onSelectSection={vi.fn()}
        />
      );

      const navAside = screen.getByRole("complementary", { name: /main navigation/i });
      expect(navAside).toBeInTheDocument();

      const activeBtn = screen.getByRole("button", { name: /dashboard section, current page/i });
      expect(activeBtn).toHaveAttribute("aria-current", "page");
    });

    it("renders TopBar with role='banner' and radiogroup for sensor modes", () => {
      render(
        <TopBar
          sectionTitle="dashboard"
          profile={null}
          drawerOpen={false}
          onToggleDrawer={vi.fn()}
          onOpenCommandPalette={vi.fn()}
        />
      );

      const banner = screen.getByRole("banner", { name: /top bar controls and status/i });
      expect(banner).toBeInTheDocument();

      const radiogroup = screen.getByRole("radiogroup", { name: /sensor display mode/i });
      expect(radiogroup).toBeInTheDocument();

      const radioOptions = screen.getAllByRole("radio");
      expect(radioOptions.length).toBe(4);
    });
  });
});
