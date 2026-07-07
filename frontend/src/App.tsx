
import { Sidebar } from './components/layout/Sidebar';
import { Chat } from './components/chat/Chat';
import { DatabaseTables } from './components/dashboard/DatabaseTables';
import './App.css'; // Minimal reset CSS can go here

function App() {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', fontFamily: 'system-ui, sans-serif' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Chat />
        <DatabaseTables />
      </div>
    </div>
  );
}

export default App;
