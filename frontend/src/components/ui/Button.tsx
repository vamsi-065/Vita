import { type ButtonHTMLAttributes } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'outline';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-primary text-on-primary hover:bg-primary/90 disabled:bg-outline disabled:text-on-surface-variant',
  secondary:
    'bg-primary-container text-on-primary-container hover:bg-primary-container/80',
  ghost:
    'bg-transparent text-on-surface hover:bg-surface-container-high',
  outline:
    'border border-outline bg-transparent text-on-surface hover:bg-surface-container',
};

export function Button({
  variant = 'primary',
  loading = false,
  disabled,
  className = '',
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled || loading}
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 text-sm font-medium transition-colors disabled:cursor-not-allowed ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="flex gap-1">
          <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-current" />
          <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-current" />
          <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-current" />
        </span>
      ) : (
        children
      )}
    </button>
  );
}
