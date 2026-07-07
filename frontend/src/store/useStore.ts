import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
}

interface AppState {
  chats: ChatSession[];
  activeChatId: string | null;
  tables: any[];
  activeTableData: any[];
  addMessage: (chatId: string, msg: Message) => void;
  createChat: () => string;
  setActiveChat: (id: string) => void;
  setTables: (tables: any[]) => void;
  setActiveTableData: (data: any[]) => void;
}

export const useStore = create<AppState>((set) => ({
  chats: [],
  activeChatId: null,
  tables: [],
  activeTableData: [],
  addMessage: (chatId, msg) => set((state) => ({
    chats: state.chats.map(chat => 
      chat.id === chatId ? { ...chat, messages: [...chat.messages, msg] } : chat
    )
  })),
  createChat: () => {
    const id = Date.now().toString();
    set((state) => ({
      chats: [{ id, title: `Chat ${state.chats.length + 1}`, messages: [] }, ...state.chats],
      activeChatId: id
    }));
    return id;
  },
  setActiveChat: (id) => set({ activeChatId: id }),
  setTables: (tables) => set({ tables }),
  setActiveTableData: (data) => set({ activeTableData: data })
}));
