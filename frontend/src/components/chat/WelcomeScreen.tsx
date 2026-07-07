import { Sparkles } from 'lucide-react';
import { SUGGESTION_CHIPS } from '../../lib/constants';

interface WelcomeScreenProps {
  userName?: string;
  onSuggestion: (text: string) => void;
}

export function WelcomeScreen({ userName, onSuggestion }: WelcomeScreenProps) {
  const greeting = userName ? `Hello, ${userName}` : 'Hello';

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 pb-32 pt-8">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary-container to-secondary-container">
        <Sparkles className="text-on-primary-container" size={28} />
      </div>
      <h2 className="mb-2 text-center text-2xl font-normal text-on-surface md:text-3xl">
        {greeting}, how can I help your business today?
      </h2>
      <p className="mb-8 max-w-md text-center text-base text-on-surface-variant">
        Ask me to manage inventory, create tables, or draft documents — just type naturally.
      </p>
      <div className="flex max-w-xl flex-wrap justify-center gap-2">
        {SUGGESTION_CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => onSuggestion(chip)}
            className="rounded-full border border-outline-variant bg-surface px-4 py-2.5 text-sm text-on-surface transition-colors hover:bg-surface-container-high"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
}
