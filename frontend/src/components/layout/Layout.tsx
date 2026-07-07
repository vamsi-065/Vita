import { useState, useEffect, useRef } from 'react';
import { Menu, Send, Sun, Moon, Mic, Plus, MessageSquare, Package, Paperclip, Trash2 } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { useStore } from '../../store/useStore';
import { MessageBubble, TypingIndicator } from '../chat/MessageBubble';
import { api } from '../../services/api';
import { useToast } from '../../context/ToastContext';

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { chats, activeChatId, ensureActiveChat, addMessage, createChat, setActiveChat, refreshTables, clearChats, deleteChat } = useStore();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const [inventory, setInventory] = useState<any[]>([]);
  const [addedItems, setAddedItems] = useState<any[]>([]);
  const [inventoryUpdated, setInventoryUpdated] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [columns, setColumns] = useState<any[]>([]);

  const recognitionRef = useRef<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { showToast } = useToast();

  const activeChat = chats.find((c) => c.id === activeChatId);
  const messages = activeChat?.messages || [];
  const hasMessages = messages.length > 0;
  
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const toggleTheme = () => setIsDark(!isDark);

  useEffect(() => {
    ensureActiveChat();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const refreshInventory = async () => {
    try {
      const data = await api.getTable('inventory');
      if (data) {
        if (data.rows) setInventory(data.rows);
        if (data.columns) setColumns(data.columns);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    refreshInventory();
  }, []);

  useEffect(() => {
    if (drawerOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [drawerOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setDrawerOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, []);


  const handleSend = async (customText?: string) => {
    const textToSend = customText !== undefined ? customText : input;
    if (!textToSend.trim() || loading) return;

    setInput('');
    setLoading(true);

    const chatId = ensureActiveChat();
    
    const userMsg = {
      id: crypto.randomUUID(),
      role: 'user' as const,
      content: textToSend
    };
    addMessage(chatId, userMsg);

    try {
      const response = await api.sendChat(textToSend);
      if (response && response.message) {
        addMessage(chatId, {
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: response.message
        });

        if (response.data_payload) {
          const { added_items, total_inventory } = response.data_payload;
          if (total_inventory) {
            setInventory(total_inventory);
          }
          await refreshInventory();
          if (added_items && added_items.length > 0) {
            setAddedItems(added_items);
            setInventoryUpdated(true);
          }
        }
        await refreshTables();
      }
    } catch (err) {
      console.error(err);
      const errMsg = err instanceof Error ? err.message : "Sorry, I couldn't reach the server. Please check your backend connection.";
      addMessage(chatId, {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: errMsg
      });
    } finally {
      setLoading(false);
    }
  };

  const startSpeechRecognition = () => {
    // @ts-ignore
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      showToast("Your browser does not support Speech Recognition. Try using Google Chrome.", "error");
      return;
    }

    const recognition = new SpeechRecognition() as any;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      if (text) {
        setInput(text);
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      showToast(`Speech recognition error: ${event.error}`, "error");
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  const handlePlusClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    const chatId = ensureActiveChat();

    const userMsg = {
      id: crypto.randomUUID(),
      role: 'user' as const,
      content: `Uploaded list: ${file.name}`
    };
    addMessage(chatId, userMsg);

    try {
      const response = await api.uploadFile(file);
      if (response && response.message) {
        addMessage(chatId, {
          id: crypto.randomUUID(),
          role: 'assistant' as const,
          content: response.message
        });

        if (response.data_payload) {
          const { added_items, total_inventory } = response.data_payload;
          if (total_inventory) {
            setInventory(total_inventory);
          }
          await refreshInventory();
          if (added_items && added_items.length > 0) {
            setAddedItems(added_items);
            setInventoryUpdated(true);
          }
        }
        await refreshTables();
      }
    } catch (err) {
      console.error(err);
      addMessage(chatId, {
        id: crypto.randomUUID(),
        role: 'assistant' as const,
        content: `Failed to process list. Reason: ${err instanceof Error ? err.message : 'Connection error'}`
      });
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const toggleSpeechRecognition = () => {
    if (isListening) {
      stopSpeechRecognition();
    } else {
      startSpeechRecognition();
    }
  };

  const handleCleanDatabase = async () => {
    if (!window.confirm("Are you sure you want to clean the database? This deletes all items in inventory.")) return;
    try {
      await api.cleanDatabase();
      showToast("Database cleaned successfully!", "success");
      await refreshInventory();
      await refreshTables();
    } catch (err) {
      console.error(err);
      showToast("Failed to clean database.", "error");
    }
  };

  return (
    <div className="flex h-screen w-full bg-[var(--color-surface-chat)] text-[var(--color-text-main)] font-sans transition-colors duration-200">
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/20 dark:bg-black/55 z-40 md:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside 
        className={`fixed inset-y-0 left-0 z-50 w-[280px] bg-[var(--color-surface-sidebar)] border-r border-[var(--color-border-main)] transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 flex flex-col ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 border-b border-[var(--color-border-main)] flex items-center justify-between">
          <h2 className="text-lg font-semibold bg-gradient-to-r from-[var(--color-ai-gradient-start)] to-[var(--color-ai-gradient-end)] bg-clip-text text-transparent">
            Vita
          </h2>
          <button 
            className="md:hidden text-[var(--color-text-meta)] hover:text-[var(--color-text-main)]"
            onClick={() => setSidebarOpen(false)}
          >
            ✕
          </button>
        </div>

        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
          <button
            type="button"
            onClick={() => createChat()}
            className="flex w-full items-center justify-center gap-2 rounded-full border border-[var(--color-border-main)] bg-[var(--color-surface-chat)] px-4 py-2.5 text-sm font-medium text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <Plus size={16} />
            <span>New conversation</span>
          </button>
          
          <div className="flex-1 overflow-y-auto flex flex-col gap-1">
            {chats.map((chat) => (
              <div 
                key={chat.id}
                className={`group flex items-center justify-between gap-1 rounded-xl px-3 py-2.5 text-sm transition-colors ${
                  activeChatId === chat.id
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-[var(--color-text-main)] font-medium'
                    : 'text-[var(--color-text-meta)] hover:bg-gray-50 dark:hover:bg-zinc-900 hover:text-[var(--color-text-main)]'
                }`}
              >
                <button
                  type="button"
                  onClick={() => setActiveChat(chat.id)}
                  className="flex flex-1 items-center gap-3 text-left min-w-0 cursor-pointer"
                >
                  <MessageSquare size={16} className="shrink-0" />
                  <span className="truncate">{chat.title}</span>
                </button>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (window.confirm(`Delete conversation "${chat.title}"?`)) {
                      deleteChat(chat.id);
                    }
                  }}
                  title="Delete conversation"
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-[var(--color-text-meta)] hover:text-red-500 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-all cursor-pointer"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
        {chats.length > 0 && (
          <div className="px-4 pb-2 border-t border-[var(--color-border-main)] pt-2">
            <button
              type="button"
              onClick={() => {
                if (window.confirm("Are you sure you want to delete all conversations?")) {
                  clearChats();
                }
              }}
              className="flex w-full items-center justify-center gap-2 rounded-full border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20 px-4 py-2 text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-950/40 transition-colors cursor-pointer"
            >
              Clear all conversations
            </button>
          </div>
        )}

        <div className="p-4 border-t border-[var(--color-border-main)] flex items-center justify-between">
          <span className="text-sm font-medium text-[var(--color-text-meta)]">
            {isDark ? 'Dark Mode' : 'Light Mode'}
          </span>
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-[var(--color-surface-chat)] border border-[var(--color-border-main)] text-[var(--color-text-meta)] hover:text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800 transition-all cursor-pointer"
            aria-label="Toggle Theme"
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
      </aside>

      <main className="chat-layout flex flex-col relative min-w-0">
        <header className="flex h-16 items-center justify-between border-b border-[var(--color-border-main)] bg-[var(--color-surface-chat)] px-6">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="md:hidden p-2 -ml-2 rounded-md hover:bg-gray-100 dark:hover:bg-zinc-800 text-[var(--color-text-main)] focus:outline-none"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-lg font-medium text-[var(--color-text-main)]">Vita</h1>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={toggleTheme}
              className="p-2 rounded-lg text-[var(--color-text-meta)] hover:text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              aria-label="Toggle Theme"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            <button
              onClick={() => {
                setDrawerOpen(!drawerOpen);
                setInventoryUpdated(false);
              }}
              className="relative p-2 rounded-lg text-[var(--color-text-meta)] hover:text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
              aria-label="Toggle Inventory View"
            >
              <Package className={`w-5 h-5 ${inventoryUpdated ? 'animate-bounce text-indigo-500' : ''}`} />
              {inventoryUpdated && (
                <span className="absolute top-1.5 right-1.5 flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
              )}
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-4 md:p-8 pb-32">
          {!hasMessages ? (
            <EmptyState />
          ) : (
            <div className="max-w-3xl mx-auto flex flex-col gap-4">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
              ))}
              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-[var(--color-surface-chat)] via-[var(--color-surface-chat)] to-transparent">
          <div className="max-w-3xl mx-auto relative group">
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              className="hidden" 
              accept="image/*,.pdf,.csv,.xlsx,.xls,.txt"
              disabled={loading}
            />

            <button 
              type="button"
              onClick={handlePlusClick}
              disabled={loading}
              title="Add item list directly (Upload receipt/invoice)"
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full text-[var(--color-text-meta)] hover:text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Paperclip className="w-5 h-5" />
            </button>

            <button 
              type="button"
              onClick={toggleSpeechRecognition}
              disabled={loading}
              title={isListening ? "Stop listening" : "Speak to Vita"}
              className={`absolute left-12 top-1/2 -translate-y-1/2 p-2 rounded-full transition-all duration-300 ${
                isListening 
                  ? 'bg-red-500 text-white shadow-[0_0_12px_rgba(239,68,68,0.5)] animate-pulse' 
                  : 'text-[var(--color-text-meta)] hover:text-[var(--color-text-main)] hover:bg-gray-100 dark:hover:bg-zinc-800'
              } cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <Mic className="w-5 h-5" />
            </button>

            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && input.trim()) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
              placeholder={isListening ? "Listening... Speak now..." : "Message Vita..."}
              className="w-full pl-22 pr-12 py-4 rounded-full bg-[var(--color-surface-chat)] border border-[var(--color-border-main)] shadow-[0_4px_20px_-4px_rgba(0,0,0,0.08)] dark:shadow-[0_4px_20px_-4px_rgba(0,0,0,0.5)] focus:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-zinc-800 focus:border-[var(--color-ai-gradient-start)] transition-all text-[var(--color-text-main)] placeholder-gray-400 disabled:opacity-50"
            />

            <button 
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-full bg-gradient-to-r from-[var(--color-ai-gradient-start)] via-[var(--color-ai-gradient-mid)] to-[var(--color-ai-gradient-end)] text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <Send className={`w-4 h-4 ${loading ? 'animate-pulse' : ''}`} />
            </button>
          </div>
        </div>
      </main>

      {drawerOpen && (
        <div className="backdrop" onClick={() => setDrawerOpen(false)} />
      )}

      <div className={`database-drawer border-l border-[var(--color-border-main)] bg-[var(--color-surface-sidebar)] shadow-2xl flex flex-col ${drawerOpen ? 'open' : ''}`}>
          <div className="flex h-16 items-center justify-between border-b border-[var(--color-border-main)] px-6">
            <h2 className="text-md font-semibold text-[var(--color-text-main)]">Live Inventory Viewer</h2>
            <div className="flex items-center gap-2">
              {inventory.length > 0 && (
                <button
                  type="button"
                  onClick={handleCleanDatabase}
                  className="px-3 py-1.5 rounded-full border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20 text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-950/40 transition-colors cursor-pointer"
                >
                  Clean DB
                </button>
              )}
              <button 
                onClick={() => setDrawerOpen(false)}
                className="rounded-full p-2 text-[var(--color-text-meta)] hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-6">
            {inventory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-[var(--color-text-meta)]">
                <Package className="w-12 h-12 mb-2 stroke-1" />
                <p className="text-sm">No items in inventory.</p>
              </div>
            ) : (
              <div className="overflow-hidden rounded-xl border border-[var(--color-border-main)]">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-zinc-900 border-b border-[var(--color-border-main)]">
                      {columns.map((col) => (
                        <th key={col.name} className="px-4 py-3 font-semibold text-[var(--color-text-main)] capitalize">
                          {col.name.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {inventory.map((item, idx) => {
                      const isNew = addedItems.some((added) => added.item_name === item.item_name);
                      return (
                        <tr 
                          key={item.id || idx} 
                          className={`border-b border-[var(--color-border-main)] transition-colors duration-500 last:border-b-0 ${
                            isNew 
                              ? 'bg-green-50/70 dark:bg-green-950/20 text-green-950 dark:text-green-300 font-medium' 
                              : 'text-[var(--color-text-main)]'
                          }`}
                        >
                          {columns.map((col) => {
                            const value = item[col.name];
                            return (
                              <td key={col.name} className="px-4 py-3">
                                {col.name === 'status' ? (
                                  <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                                    value === 'In Stock' 
                                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
                                      : 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                                  }`}>
                                    {value !== undefined ? String(value) : ''}
                                  </span>
                                ) : (
                                  value !== undefined ? String(value) : ''
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
    </div>
  );
}
