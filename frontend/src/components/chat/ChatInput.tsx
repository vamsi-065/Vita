import { Send, Mic } from 'lucide-react';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onMic: () => void;
  loading: boolean;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSend, onMic, loading, disabled }: ChatInputProps) {
  const canSend = value.trim().length > 0 && !loading && !disabled;

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-0 z-20 flex justify-center px-4 pb-4 pt-6 md:pb-6">
      <div
        className="pointer-events-auto flex w-full max-w-3xl items-center gap-2 rounded-full border border-outline-variant bg-surface px-2 py-2 shadow-lg"
        style={{ boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}
      >
        <button
          type="button"
          onClick={onMic}
          disabled={loading || disabled}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-container disabled:opacity-40"
          aria-label="Speak your message"
        >
          <Mic size={20} />
        </button>

        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && canSend) {
              e.preventDefault();
              onSend();
            }
          }}
          disabled={loading || disabled}
          placeholder="Ask your Business Assistant…"
          className="min-h-11 flex-1 bg-transparent px-2 text-base text-on-surface outline-none placeholder:text-on-surface-variant disabled:opacity-50"
        />

        <button
          type="button"
          onClick={onSend}
          disabled={!canSend}
          className="flex h-11 min-w-11 items-center justify-center gap-1.5 rounded-full bg-primary px-4 text-on-primary transition-colors disabled:bg-outline disabled:text-on-surface-variant"
          aria-label="Send message"
        >
          {loading ? (
            <span className="flex gap-1 px-1">
              <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-on-primary" />
              <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-on-primary" />
              <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-on-primary" />
            </span>
          ) : (
            <>
              <Send size={18} />
              <span className="hidden text-sm font-medium sm:inline">Send</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
