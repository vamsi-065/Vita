import { Layout } from './components/layout/Layout';
import { ToastProvider } from './context/ToastContext';
import { LoginPage } from './components/auth/LoginPage';
import { useStore } from './store/useStore';

function App() {
  const user = useStore((state) => state.user);

  return (
    <ToastProvider>
      {user ? <Layout /> : <LoginPage />}
    </ToastProvider>
  );
}

export default App;
