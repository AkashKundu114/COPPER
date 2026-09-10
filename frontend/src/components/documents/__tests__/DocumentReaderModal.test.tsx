import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentReaderModal } from "../DocumentReaderModal";
import type { ParsedDocument } from "../../../lib/api";

describe("DocumentReaderModal", () => {
  const sampleDocument: ParsedDocument = {
    filename: "system_architecture.md",
    extension: "md",
    category: "Technical Architecture",
    size_bytes: 4096,
    size_formatted: "4.0 KB",
    page_count: 1,
    line_count: 5,
    word_count: 42,
    char_count: 260,
    estimated_tokens: 65,
    indexed_chunks: 3,
    pages: [
      {
        page_number: 1,
        text: "# C.O.P.P.E.R. Architecture\nAutonomous 30-agent coordination\nGuardian safety protocol\nEpistemic memory engine\nForge sandbox execution",
        word_count: 42,
        char_count: 260,
      },
    ],
    full_text:
      "# C.O.P.P.E.R. Architecture\nAutonomous 30-agent coordination\nGuardian safety protocol\nEpistemic memory engine\nForge sandbox execution",
    preview_text: "# C.O.P.P.E.R. Architecture...",
    status: "success",
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders document header metadata and badges", () => {
    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={vi.fn()}
        onAskAI={vi.fn()}
      />
    );

    expect(screen.getByTitle("system_architecture.md")).toBeInTheDocument();
    expect(screen.getByText("md")).toBeInTheDocument();
    expect(screen.getByText(/AI Indexed \(3 chunks\)/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Technical Architecture · 4.0 KB · 42 words · ~65 tokens/i)
    ).toBeInTheDocument();
  });

  it("switches tabs between Interactive Reader, Search in Doc, Doc Analytics, and Raw Text", async () => {
    const user = userEvent.setup();
    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={vi.fn()}
        onAskAI={vi.fn()}
      />
    );

    // Initial tab: Interactive Reader
    expect(screen.getByText(/5 total lines/i)).toBeInTheDocument();

    // Switch to Search in Doc
    await user.click(screen.getByRole("button", { name: /search in doc/i }));
    expect(
      screen.getByPlaceholderText(/search keywords or phrases in document/i)
    ).toBeInTheDocument();

    // Switch to Doc Analytics
    await user.click(screen.getByRole("button", { name: /doc analytics/i }));
    expect(screen.getByText("Document Metadata & AI Ingestion")).toBeInTheDocument();
    expect(screen.getByText("CHROMA RAG INDEX")).toBeInTheDocument();
    expect(screen.getByText("Ready (3 chunks)")).toBeInTheDocument();

    // Switch to Raw Text
    await user.click(screen.getByRole("button", { name: /raw text/i }));
    expect(screen.getByText(/Autonomous 30-agent coordination/i)).toBeInTheDocument();
  });

  it("filters search matches when typing in search tab", async () => {
    const user = userEvent.setup();
    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={vi.fn()}
        onAskAI={vi.fn()}
      />
    );

    await user.click(screen.getByRole("button", { name: /search in doc/i }));
    const searchInput = screen.getByPlaceholderText(/search keywords or phrases in document/i);

    await user.type(searchInput, "Guardian");

    expect(screen.getByText(/Found/i)).toBeInTheDocument();
    expect(screen.getByText("L3")).toBeInTheDocument();
    expect(screen.getByText("Guardian safety protocol")).toBeInTheDocument();
  });

  it("triggers onAskAI and onClose when 'Analyze with AI' is clicked", async () => {
    const user = userEvent.setup();
    const handleAskAI = vi.fn();
    const handleClose = vi.fn();

    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={handleClose}
        onAskAI={handleAskAI}
      />
    );

    const askAiBtn = screen.getByTitle(/ask c.o.p.p.e.r. to summarize this document/i);
    await user.click(askAiBtn);

    expect(handleAskAI).toHaveBeenCalledTimes(1);
    expect(handleAskAI).toHaveBeenCalledWith(
      expect.stringContaining("system_architecture.md")
    );
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("copies document text to clipboard when copy button is clicked", async () => {
    const user = userEvent.setup();
    const writeSpy = vi.spyOn(navigator.clipboard, "writeText");

    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={vi.fn()}
        onAskAI={vi.fn()}
      />
    );

    const copyBtn = screen.getByTitle(/copy document text/i);
    await user.click(copyBtn);

    expect(writeSpy).toHaveBeenCalledWith(sampleDocument.full_text);
  });

  it("closes modal on Close Reader button click and Escape key", async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();

    render(
      <DocumentReaderModal
        document={sampleDocument}
        onClose={handleClose}
        onAskAI={vi.fn()}
      />
    );

    const closeBtn = screen.getByText("Close Reader");
    await user.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);

    // Escape key
    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(2);
  });
});
