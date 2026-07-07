import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import type { ToastMessage, ToastType } from '../types';

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const icons: Record<ToastType, typeof Info> = {
  info: Info,
  success: CheckCircle2,
  error: AlertCircle,
};

const styles: Record<ToastType, string> = {
  info: 'bg-on-surface text-surface',
  success: 'bg-success text-white',
  error: 'bg-error text-white',
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        className="fixed bottom-24 left-1/2 z-[100] flex w-full max-w-md -translate-x-1/2 flex-col gap-2 px-4 md:bottom-8"
        aria-live="polite"
      >
        {toasts.map((toast) => {
          const Icon = icons[toast.type];
          return (
            <div
              key={toast.id}
              className={`animate-fade-in flex items-center gap-3 rounded-xl px-4 py-3 shadow-lg ${styles[toast.type]}`}
            >
              <Icon size={18} className="shrink-0" />
              <p className="flex-1 text-sm leading-snug">{toast.message}</p>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="shrink-0 rounded-full p-1 opacity-70 hover:opacity-100"
                aria-label="Dismiss"
              >
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
