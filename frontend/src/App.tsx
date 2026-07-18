import { useEffect, useState } from 'react';
import { Layout } from './components/layout/Layout';
import { ToastProvider } from './context/ToastContext';
import { LoginPage } from './components/auth/LoginPage';
import { useStore } from './store/useStore';
import { supabase } from './lib/supabase';

function App() {
  const user = useStore((state) => state.user);
  const setUser = useStore((state) => state.setUser);
  const logout = useStore((state) => state.logout);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function initSession() {
      try {
        const { data } = await supabase.auth.getSession();
        if (mounted) {
          if (data.session?.user) {
            setUser({
              id: data.session.user.id,
              email: data.session.user.email || '',
              full_name: data.session.user.user_metadata?.full_name || 'User',
              business_name: data.session.user.user_metadata?.business_name || '',
              is_active: true,
              created_at: data.session.user.created_at
            });
          } else {
            logout();
          }
        }
      } catch (err) {
        console.error("Error fetching session", err);
      } finally {
        if (mounted) {
          setIsInitializing(false);
        }
      }
    }

    initSession();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return;
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email || '',
          full_name: session.user.user_metadata?.full_name || 'User',
          business_name: session.user.user_metadata?.business_name || '',
          is_active: true,
          created_at: session.user.created_at
        });
      } else {
        logout();
      }
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [setUser, logout]);

  if (isInitializing) {
    return <div className="min-h-screen bg-[#0B0B0C] flex items-center justify-center text-white">Loading...</div>;
  }

  return (
    <ToastProvider>
      {user ? <Layout /> : <LoginPage />}
    </ToastProvider>
  );
}

export default App;
