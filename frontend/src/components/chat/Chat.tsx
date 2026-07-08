import { useState, useEffect, useRef } from 'react';
import { useStore } from '../../store/useStore';
import { Send, Mic, AlertTriangle } from 'lucide-react';
import { api } from '../../services/api';

export const Chat = () => {
  const { chats, activeChatId, addMessage } = useStore();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeChat = chats.find(c => c.id === activeChatId);

  useEffect(() => {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
  }, [activeChat?.messages, loading]);

  const handleSend = async (text: string) => {
    if (!text.trim() || !activeChatId) return;
    
    setError(null);
    const userMsg = { id: Date.now().toString(), role: 'user' as const, content: text };
    addMessage(activeChatId, userMsg);
    setInput('');
    setLoading(true);

    try {
      const response = await api.post('/chat', { message: text });
      if (response && response.message) {
        addMessage(activeChatId, { 
          id: (Date.now() + 1).toString(), 
          role: 'assistant', 
          content: response.message 
        });
      } else {
        setError("Invalid response format received from AI agent.");
      }
    } catch (err) {
      setError("Failed to communicate with the AI agent. Please check your backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleMic = () => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support Speech Recognition.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      setInput(text);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.start();
  };

  if (!activeChatId) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', backgroundColor: '#121212' }}>
        Select or create a chat to begin.
      </div>
    );
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#121212', color: 'white', height: '100%', overflow: 'hidden' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column' }}>
        {activeChat && activeChat.messages.map(msg => (
          <div 
            key={msg.id} 
            style={{ 
              marginBottom: '20px', 
              padding: '15px', 
              borderRadius: '8px', 
              backgroundColor: msg.role === 'user' ? '#2a2a2a' : '#1e1e1e', 
              maxWidth: '80%', 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', 
              marginLeft: msg.role === 'user' ? 'auto' : '0' 
            }}
          >
            <strong style={{ display: 'block', marginBottom: '5px', color: msg.role === 'user' ? '#4caf50' : '#2196f3' }}>
              {msg.role === 'user' ? 'You' : 'AI Agent'}
            </strong>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{msg.content}</div>
          </div>
        ))}
        
        {loading && (
          <div style={{ color: '#888', fontStyle: 'italic', padding: '10px' }}>
            AI Agent is typing...
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#ff6b6b', padding: '10px', backgroundColor: '#2a1a1a', borderRadius: '6px', marginTop: '10px' }}>
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}
        
        <div ref={bottomRef} style={{ float: 'left', clear: 'both', paddingBottom: '30px' }} />
      </div>
      
      <div style={{ padding: '20px', borderTop: '1px solid #333', backgroundColor: '#1e1e1e' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            type="button"
            onClick={handleMic} 
            title="Speech-to-Text"
            style={{ padding: '10px', backgroundColor: '#333', border: 'none', borderRadius: '6px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <Mic size={20} />
          </button>
          
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(input);
              }
            }}
            placeholder="Type your message to the agent..."
            style={{ flex: 1, padding: '12px', backgroundColor: '#333', border: '1px solid #444', borderRadius: '6px', color: 'white', outline: 'none' }}
          />
          
          <button 
            type="button"
            onClick={() => handleSend(input)} 
            style={{ padding: '10px 20px', backgroundColor: '#4caf50', border: 'none', borderRadius: '6px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <Send size={18} /> 
            <span>Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};
