
import { useStore } from '../../store/useStore';
import { PlusCircle, MessageSquare } from 'lucide-react';

export const Sidebar = () => {
  const { chats, activeChatId, createChat, setActiveChat } = useStore();

  return (
    <div style={{ width: '250px', backgroundColor: '#1e1e1e', color: 'white', display: 'flex', flexDirection: 'column', height: '100%', borderRight: '1px solid #333' }}>
      <div style={{ padding: '20px' }}>
        <button 
          onClick={createChat}
          style={{ width: '100%', padding: '10px', display: 'flex', alignItems: 'center', gap: '10px', backgroundColor: '#2a2a2a', border: '1px solid #444', borderRadius: '6px', color: 'white', cursor: 'pointer' }}
        >
          <PlusCircle size={18} /> New Chat
        </button>
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 10px' }}>
        {chats.map(chat => (
          <div 
            key={chat.id} 
            onClick={() => setActiveChat(chat.id)}
            style={{ padding: '10px', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', borderRadius: '6px', backgroundColor: activeChatId === chat.id ? '#333' : 'transparent', marginBottom: '5px' }}
          >
            <MessageSquare size={16} />
            <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{chat.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
