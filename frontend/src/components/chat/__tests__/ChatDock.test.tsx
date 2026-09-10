import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatDock } from "../ChatDock";

describe("ChatDock", () => {
  const defaultProps = {
    connected: true,
    thinking: false,
    speaking: false,
    onSend: vi.fn(),
    onStop: vi.fn(),
    onClear: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders input textarea, voice mic, and model selector", () => {
    render(<ChatDock {...defaultProps} />);

    expect(
      screen.getByPlaceholderText(/input command or prompt for god's eye intelligence/i)
    ).toBeInTheDocument();
    expect(screen.getByTitle(/voice intercept mic/i)).toBeInTheDocument();
    expect(screen.getByText("Adaptive Intent")).toBeInTheDocument();
  });

  it("sends message when user types text and clicks send button", async () => {
    const user = userEvent.setup();
    const handleSend = vi.fn();

    render(<ChatDock {...defaultProps} onSend={handleSend} />);

    const textarea = screen.getByPlaceholderText(
      /input command or prompt for god's eye intelligence/i
    );

    await user.type(textarea, "Analyze local GPU thermals");

    // Send button appears when draft has text
    const sendButton = screen.getByRole("button", { name: /send message/i });
    await user.click(sendButton);

    expect(handleSend).toHaveBeenCalledTimes(1);
    expect(handleSend).toHaveBeenCalledWith("Analyze local GPU thermals", "auto");
    expect(textarea).toHaveValue("");
  });

  it("sends message on Enter key without Shift", async () => {
    const user = userEvent.setup();
    const handleSend = vi.fn();

    render(<ChatDock {...defaultProps} onSend={handleSend} />);

    const textarea = screen.getByPlaceholderText(
      /input command or prompt for god's eye intelligence/i
    );

    await user.type(textarea, "Check memory status{enter}");

    expect(handleSend).toHaveBeenCalledTimes(1);
    expect(handleSend).toHaveBeenCalledWith("Check memory status", "auto");
  });

  it("does not send message on Enter key when empty or whitespace", async () => {
    const user = userEvent.setup();
    const handleSend = vi.fn();

    render(<ChatDock {...defaultProps} onSend={handleSend} />);

    const textarea = screen.getByPlaceholderText(
      /input command or prompt for god's eye intelligence/i
    );

    await user.type(textarea, "   {enter}");
    expect(handleSend).not.toHaveBeenCalled();
  });

  it("opens cognitive mode dropdown and allows selecting another mode", async () => {
    const user = userEvent.setup();
    const handleSend = vi.fn();

    render(<ChatDock {...defaultProps} onSend={handleSend} />);

    const modeButton = screen.getByText("Adaptive Intent");
    await user.click(modeButton);

    // Dropdown list appears
    expect(screen.getByText("Cognitive Intelligence Mode")).toBeInTheDocument();
    expect(screen.getByText("Deep Cognitive")).toBeInTheDocument();
    expect(screen.getByText("Software Architect")).toBeInTheDocument();

    // Select Software Architect mode
    await user.click(screen.getByText("Software Architect"));

    // Verify selected mode updated
    expect(screen.getByText("Software Architect")).toBeInTheDocument();

    // Send message with new mode
    const textarea = screen.getByPlaceholderText(
      /input command or prompt for god's eye intelligence/i
    );
    await user.type(textarea, "Refactor service layer{enter}");

    expect(handleSend).toHaveBeenCalledWith("Refactor service layer", "coding");
  });

  it("disables textarea and shows stop button when thinking is true", async () => {
    const user = userEvent.setup();
    const handleStop = vi.fn();

    render(<ChatDock {...defaultProps} thinking={true} onStop={handleStop} />);

    const textarea = screen.getByPlaceholderText(
      /neural processing active across local agents/i
    );
    expect(textarea).toBeDisabled();

    const stopButton = screen.getByTitle(/stop generation/i);
    expect(stopButton).toBeInTheDocument();

    await user.click(stopButton);
    expect(handleStop).toHaveBeenCalledTimes(1);
  });

  it("calls onClear when purge logs button is clicked", async () => {
    const user = userEvent.setup();
    const handleClear = vi.fn();

    render(<ChatDock {...defaultProps} onClear={handleClear} />);

    const purgeBtn = screen.getByTitle(/purge session memory & reset chat/i);
    await user.click(purgeBtn);

    expect(handleClear).toHaveBeenCalledTimes(1);
  });
});
