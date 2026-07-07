interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
}

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 md:max-w-[70%] ${
          isUser
            ? 'rounded-br-md bg-user-bubble text-on-surface'
            : 'rounded-bl-md bg-ai-bubble text-on-surface'
        }`}
      >
        {!isUser && (
          <p className="mb-1 text-xs font-medium text-primary">Business Assistant</p>
        )}
        <p className="whitespace-pre-wrap text-base leading-relaxed">{content}</p>
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="flex items-center gap-2 rounded-2xl rounded-bl-md bg-ai-bubble px-4 py-3">
        <span className="text-xs font-medium text-primary">Business Assistant</span>
        <span className="flex gap-1 py-1">
          <span className="animate-pulse-dot h-2 w-2 rounded-full bg-primary" />
          <span className="animate-pulse-dot h-2 w-2 rounded-full bg-primary" />
          <span className="animate-pulse-dot h-2 w-2 rounded-full bg-primary" />
        </span>
      </div>
    </div>
  );
}
