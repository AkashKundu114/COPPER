import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  GuardianChallengeModal,
  type GuardianChallengePayload,
} from "../GuardianChallengeModal";

describe("GuardianChallengeModal", () => {
  const samplePayload: GuardianChallengePayload = {
    level: 2,
    reasoning: "Executing destructive bash command may remove database files irreversibly.",
    evidence: [
      "Detected 'rm -rf /data/db'",
      "Affects primary persistent storage",
      "No recent snapshot found",
    ],
    confidence: "98.4%",
    recommendation: "Use sandboxed staging dry-run or create backup snapshot first.",
  };

  it("renders null when payload is null", () => {
    const { container } = render(
      <GuardianChallengeModal
        payload={null}
        onProceedAnyway={vi.fn()}
        onFollowRecommendation={vi.fn()}
        onDiscuss={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders modal header, reasoning, evidence list, confidence, and recommendation", () => {
    render(
      <GuardianChallengeModal
        payload={samplePayload}
        onProceedAnyway={vi.fn()}
        onFollowRecommendation={vi.fn()}
        onDiscuss={vi.fn()}
      />
    );

    expect(screen.getByText("COPPER Recommends Against This")).toBeInTheDocument();
    expect(screen.getByText("Guardian Level 2 Conflict Challenge")).toBeInTheDocument();
    expect(screen.getByText(samplePayload.reasoning)).toBeInTheDocument();

    samplePayload.evidence.forEach((ev) => {
      expect(screen.getByText(ev)).toBeInTheDocument();
    });

    expect(screen.getByText("98.4%")).toBeInTheDocument();
    expect(screen.getByText(samplePayload.recommendation)).toBeInTheDocument();
  });

  it("calls onFollowRecommendation when 'Follow Rec' is clicked", async () => {
    const user = userEvent.setup();
    const handleFollow = vi.fn();

    render(
      <GuardianChallengeModal
        payload={samplePayload}
        onProceedAnyway={vi.fn()}
        onFollowRecommendation={handleFollow}
        onDiscuss={vi.fn()}
      />
    );

    const followBtn = screen.getByRole("button", { name: /follow rec/i });
    await user.click(followBtn);

    expect(handleFollow).toHaveBeenCalledTimes(1);
  });

  it("calls onDiscuss when 'Discuss' is clicked", async () => {
    const user = userEvent.setup();
    const handleDiscuss = vi.fn();

    render(
      <GuardianChallengeModal
        payload={samplePayload}
        onProceedAnyway={vi.fn()}
        onFollowRecommendation={vi.fn()}
        onDiscuss={handleDiscuss}
      />
    );

    const discussBtn = screen.getByRole("button", { name: /discuss/i });
    await user.click(discussBtn);

    expect(handleDiscuss).toHaveBeenCalledTimes(1);
  });

  it("calls onProceedAnyway when 'Proceed Anyway' is clicked", async () => {
    const user = userEvent.setup();
    const handleProceed = vi.fn();

    render(
      <GuardianChallengeModal
        payload={samplePayload}
        onProceedAnyway={handleProceed}
        onFollowRecommendation={vi.fn()}
        onDiscuss={vi.fn()}
      />
    );

    const proceedBtn = screen.getByRole("button", { name: /proceed anyway/i });
    await user.click(proceedBtn);

    expect(handleProceed).toHaveBeenCalledTimes(1);
  });
});
