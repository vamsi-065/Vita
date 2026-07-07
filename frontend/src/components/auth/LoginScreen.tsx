import { useState } from 'react';
import { Building2, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { api, setToken } from '../../services/api';
import { useStore } from '../../store/useStore';
import { useToast } from '../../context/ToastContext';

type Mode = 'login' | 'signup';

export function LoginScreen() {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setUser = useStore((s) => s.setUser);
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response =
        mode === 'login'
          ? await api.login(email, password)
          : await api.signup({
              email,
              password,
              full_name: fullName,
              business_name: businessName,
            });

      setToken(response.access_token);
      setUser(response.user);
      showToast(`Welcome, ${response.user.full_name.split(' ')[0]}!`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong';
      setError(message);
      showToast(message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center bg-surface px-4 py-12">
      <div className="w-full max-w-md animate-fade-in">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-container">
            <Sparkles className="text-on-primary-container" size={28} />
          </div>
          <h1 className="text-2xl font-semibold text-on-surface">AI Business OS</h1>
          <p className="mt-2 text-base text-on-surface-variant">
            Manage your business with a simple conversation
          </p>
        </div>

        <div className="rounded-2xl border border-outline-variant bg-surface p-6 shadow-sm">
          <div className="mb-6 flex rounded-full bg-surface-container p-1">
            <button
              type="button"
              onClick={() => { setMode('login'); setError(''); }}
              className={`flex-1 rounded-full py-2.5 text-sm font-medium transition-colors ${mode === 'login' ? 'bg-surface text-on-surface shadow-sm' : 'text-on-surface-variant'}`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => { setMode('signup'); setError(''); }}
              className={`flex-1 rounded-full py-2.5 text-sm font-medium transition-colors ${mode === 'signup' ? 'bg-surface text-on-surface shadow-sm' : 'text-on-surface-variant'}`}
            >
              Create account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {mode === 'signup' && (
              <>
                <Input
                  label="Your name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Ramesh Kumar"
                  required
                  autoComplete="name"
                />
                <Input
                  label="Business name"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="Kumar General Store"
                  required
                  autoComplete="organization"
                />
              </>
            )}
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@business.com"
              required
              autoComplete="email"
            />
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
              minLength={8}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />

            {error && (
              <p className="rounded-xl bg-error-container px-4 py-3 text-sm text-error">
                {error}
              </p>
            )}

            <Button type="submit" loading={loading} className="mt-2 w-full">
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          {mode === 'signup' && (
            <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-on-surface-variant">
              <Building2 size={14} />
              Built for shop owners and small teams
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
