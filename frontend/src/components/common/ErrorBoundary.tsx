import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Copy, Check } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  copied: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    copied: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, copied: false };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary caught an unhandled error]:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, copied: false });
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleCopy = async () => {
    if (!this.state.error) return;
    try {
      await navigator.clipboard.writeText(
        `Error: ${this.state.error.message}\n\nStack:\n${this.state.error.stack || "N/A"}`
      );
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    } catch {
      // Fallback if clipboard API is unavailable
    }
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          aria-live="assertive"
          className="min-h-screen w-full bg-[#020617] text-white flex items-center justify-center p-6 select-none"
        >
          <div className="max-w-lg w-full bg-surface-elevated backdrop-blur-xl border border-rose-500/30 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-rose-300">Application Error</h1>
                <p className="text-xs text-text-secondary">A component encountered an unhandled exception.</p>
              </div>
            </div>

            {this.state.error && (
              <div className="bg-black/40 border border-border-subtle rounded-xl p-3 text-xs font-mono text-text-secondary max-h-40 overflow-y-auto break-words space-y-1">
                <div className="text-rose-400 font-semibold">{this.state.error.name}: {this.state.error.message}</div>
                {this.state.error.stack && (
                  <pre className="text-[10px] text-text-tertiary whitespace-pre-wrap font-mono">
                    {this.state.error.stack.split("\n").slice(0, 4).join("\n")}
                  </pre>
                )}
              </div>
            )}

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={this.handleReload}
                className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 active:bg-cyan-700 text-white text-sm font-medium rounded-xl transition-colors cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" />
                Reload Application
              </button>
              <button
                type="button"
                onClick={this.handleReset}
                className="px-4 py-2.5 bg-surface-active hover:bg-surface-spotlight text-text text-sm font-medium rounded-xl transition-colors cursor-pointer"
              >
                Try Again
              </button>
              <button
                type="button"
                onClick={this.handleCopy}
                aria-label="Copy error stack"
                title="Copy error details"
                className="p-2.5 bg-surface-active hover:bg-surface-spotlight text-text-secondary hover:text-white rounded-xl transition-colors cursor-pointer"
              >
                {this.state.copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
