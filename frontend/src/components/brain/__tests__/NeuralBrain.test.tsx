import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NeuralBrain, type NeuralBrainProps } from "../NeuralBrain";
import { AGENTS } from "../../../constants/agents";

describe("NeuralBrain", () => {
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
        times_invoked: 12,
        familiarity_score: 0.8,
        familiarity_tier: "Trusted Partner",
        glow: 0.75,
        last_active: "Just now",
      },
    },
    thinking: false,
    activeAgent: null,
    activeEdge: null,
    pulseSeq: 0,
    selectedAgent: null,
    onSelectAgent: vi.fn(),
  };

  it("renders SVG with role='img' and accessible aria-label", () => {
    render(<NeuralBrain {...defaultProps} />);

    const svg = screen.getByRole("img", {
      name: /copper neural map of active agents, orbiting like a solar system/i,
    });
    expect(svg).toBeInTheDocument();
  });

  it("renders the central COPPER core text and container", () => {
    render(<NeuralBrain {...defaultProps} />);

    expect(screen.getByTestId("copper-core")).toBeInTheDocument();
    expect(screen.getByText("COPPER")).toBeInTheDocument();
  });

  it("renders agent nodes and their labels", () => {
    render(<NeuralBrain {...defaultProps} />);

    // Test a sample of agents across tiers
    const sampleAgents = [AGENTS[0], AGENTS[5], AGENTS[10]];
    sampleAgents.forEach((agent) => {
      expect(screen.getByTestId(`agent-group-${agent.id}`)).toBeInTheDocument();
      expect(screen.getByText(agent.name)).toBeInTheDocument();
    });
  });

  it("fires onSelectAgent when an agent node circle is clicked", async () => {
    const user = userEvent.setup();
    const handleSelectAgent = vi.fn();

    render(<NeuralBrain {...defaultProps} onSelectAgent={handleSelectAgent} />);

    const targetAgent = AGENTS[0];
    const agentButton = screen.getByRole("button", {
      name: new RegExp(`^${targetAgent.name},`),
    });

    await user.click(agentButton);
    expect(handleSelectAgent).toHaveBeenCalledWith(targetAgent.id);
  });

  it("fires onSelectAgent when Enter or Space is pressed on an agent node", () => {
    const handleSelectAgent = vi.fn();

    render(<NeuralBrain {...defaultProps} onSelectAgent={handleSelectAgent} />);

    const targetAgent = AGENTS[1];
    const agentButton = screen.getByRole("button", {
      name: new RegExp(`^${targetAgent.name},`),
    });

    fireEvent.keyDown(agentButton, { key: "Enter" });
    expect(handleSelectAgent).toHaveBeenCalledWith(targetAgent.id);

    fireEvent.keyDown(agentButton, { key: " " });
    expect(handleSelectAgent).toHaveBeenCalledWith(targetAgent.id);
  });

  it("renders active edge pulse line when activeEdge matches an agent", () => {
    const targetAgent = AGENTS[2];
    render(
      <NeuralBrain
        {...defaultProps}
        activeEdge={{ from: "COPPER", to: targetAgent.id }}
        pulseSeq={1}
      />
    );

    expect(
      screen.getByTestId(`edge-pulse-${targetAgent.id}`)
    ).toBeInTheDocument();
  });

  it("applies core pulse animation class when thinking is true", () => {
    const { rerender } = render(<NeuralBrain {...defaultProps} thinking={false} />);
    const coreGroup = screen.getByTestId("copper-core");
    expect(coreGroup.querySelector(".animate-core-pulse")).toBeNull();

    rerender(<NeuralBrain {...defaultProps} thinking={true} />);
    expect(coreGroup.querySelector(".animate-core-pulse")).not.toBeNull();
  });
});
