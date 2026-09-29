import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ErrorBoundary } from "../ErrorBoundary";

function ProblemChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error("Test intentional explosion");
  }
  return <div>Healthy Component</div>;
}

describe("ErrorBoundary", () => {
  it("renders children when no error occurs", () => {
    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Healthy Component")).toBeDefined();
  });

  it("renders fallback UI when child throws an error", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemChild shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByRole("alert")).toBeDefined();
    expect(screen.getByText("Application Error")).toBeDefined();
    expect(screen.getAllByText(/Test intentional explosion/).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /Reload Application/i })).toBeDefined();

    consoleError.mockRestore();
  });

  it("renders custom fallback if provided", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary fallback={<div>Custom Error View</div>}>
        <ProblemChild shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Custom Error View")).toBeDefined();

    consoleError.mockRestore();
  });
});
