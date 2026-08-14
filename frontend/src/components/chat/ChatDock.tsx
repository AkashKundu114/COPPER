import { useState } from "react";
import { Paperclip, ArrowUp } from "lucide-react";

interface Props {
  connected: boolean;
  thinking: boolean;
  onSend: (message: string) => void;
}

export function ChatDock({ connected, thinking, onSend }: Props) {
  const [draft, setDraft] = useState("");

  const submit = () => {
    const msg = draft.trim();
    if (!msg || thinking) return;
    onSend(msg);
    setDraft("");
  };

  return (
    <div className="w-full flex items-end gap-2 bg-bg-panel border border-border rounded-2xl px-3 py-2.5 shadow-sm focus-within:border-accent transition-colors">
      <button 
        className="p-2 text-text-muted hover:text-text rounded-full transition-colors flex-shrink-0"
        title="Attach file (coming soon)"
      >
        <Paperclip size={18} />
      </button>

      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder={thinking ? "C.O.P.P.E.R. is thinking..." : "Message C.O.P.P.E.R..."}
        className="flex-1 bg-transparent outline-none text-[15px] text-text placeholder:text-text-muted resize-none max-h-32 min-h-[24px] py-1.5 custom-scrollbar"
        rows={draft.split("\n").length > 1 ? Math.min(draft.split("\n").length, 5) : 1}
      />

      <button
        onClick={submit}
        disabled={!draft.trim() || thinking}
        className="p-2 ml-1 rounded-full bg-text text-bg hover:bg-accent disabled:opacity-30 disabled:hover:bg-text transition-colors flex-shrink-0"
        title={connected ? "Send message" : "Reconnecting..."}
      >
        <ArrowUp size={18} strokeWidth={3} />
      </button>
    </div>
  );
}
