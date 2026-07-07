import { Menu, X } from 'lucide-react';
import { useStore } from '../../store/useStore';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const mobileSidebarOpen = useStore((s) => s.mobileSidebarOpen);
  const setMobileSidebarOpen = useStore((s) => s.setMobileSidebarOpen);

  return (
    <div className="flex h-full overflow-hidden bg-surface">
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/30"
            onClick={() => setMobileSidebarOpen(false)}
            aria-label="Close menu"
          />
          <div className="absolute left-0 top-0 h-full animate-slide-up">
            <Sidebar mobile onClose={() => setMobileSidebarOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-outline-variant px-4 py-3 md:hidden">
          <button
            type="button"
            onClick={() => setMobileSidebarOpen(true)}
            className="flex h-10 w-10 items-center justify-center rounded-full hover:bg-surface-container"
            aria-label="Open menu"
          >
            {mobileSidebarOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
          <span className="text-base font-semibold text-on-surface">AI Business OS</span>
        </header>

        <main className="relative flex min-h-0 flex-1 flex-col">{children}</main>
      </div>
    </div>
  );
}
