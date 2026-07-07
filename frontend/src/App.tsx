import { Layout } from './components/layout/Layout';
import { ToastProvider } from './context/ToastContext';

function App() {
  return (
    <ToastProvider>
      <Layout />
    </ToastProvider>
  );
}

export default App;
