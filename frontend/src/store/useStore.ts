import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatSession, Message, User } from '../types';
import { STORAGE_KEYS } from '../lib/constants';
import { api } from '../services/api';

interface AppState {
  user: User | null;
  chats: ChatSession[];
  activeChatId: string | null;
  sidebarCollapsed: boolean;
  mobileSidebarOpen: boolean;
  alertsEnabled: boolean;
  tables: string[];
  selectedTable: string | null;
  tableColumns: string[];
  tableRows: Record<string, unknown>[];
  dataRevealOpen: boolean;
  tablesLoading: boolean;
  lastTableRefresh: number;

  setUser: (user: User | null) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setMobileSidebarOpen: (open: boolean) => void;
  setAlertsEnabled: (enabled: boolean) => void;
  createChat: () => string;
  setActiveChat: (id: string) => void;
  addMessage: (chatId: string, msg: Message) => void;
  ensureActiveChat: () => string;
  refreshTables: () => Promise<void>;
  selectTable: (name: string) => Promise<void>;
  openDataReveal: () => void;
  closeDataReveal: () => void;
  toggleDataReveal: () => void;
  logout: () => void;
  clearChats: () => void;
  deleteChat: (id: string) => void;
}

function loadSidebarCollapsed(): boolean {
  return localStorage.getItem(STORAGE_KEYS.sidebarCollapsed) === 'true';
}

function loadAlertsEnabled(): boolean {
  return localStorage.getItem(STORAGE_KEYS.alertsEnabled) === 'true';
}

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
      user: null,
      chats: [],
      activeChatId: null,
      sidebarCollapsed: loadSidebarCollapsed(),
      mobileSidebarOpen: false,
      alertsEnabled: loadAlertsEnabled(),
      tables: [],
      selectedTable: null,
      tableColumns: [],
      tableRows: [],
      dataRevealOpen: false,
      tablesLoading: false,
      lastTableRefresh: 0,

      setUser: (user) => set({ user }),

      setSidebarCollapsed: (collapsed) => {
        localStorage.setItem(STORAGE_KEYS.sidebarCollapsed, String(collapsed));
        set({ sidebarCollapsed: collapsed });
      },

      setMobileSidebarOpen: (open) => set({ mobileSidebarOpen: open }),

      setAlertsEnabled: (enabled) => {
        localStorage.setItem(STORAGE_KEYS.alertsEnabled, String(enabled));
        set({ alertsEnabled: enabled });
      },

      createChat: () => {
        const id = crypto.randomUUID();
        const chat: ChatSession = {
          id,
          title: `Conversation ${get().chats.length + 1}`,
          messages: [],
          createdAt: new Date().toISOString(),
        };
        set((state) => ({
          chats: [chat, ...state.chats],
          activeChatId: id,
          mobileSidebarOpen: false,
        }));
        return id;
      },

      ensureActiveChat: () => {
        const { activeChatId, chats, createChat } = get();
        if (activeChatId && chats.some((c) => c.id === activeChatId)) {
          return activeChatId;
        }
        if (chats.length > 0) {
          set({ activeChatId: chats[0].id });
          return chats[0].id;
        }
        return createChat();
      },

      setActiveChat: (id) =>
        set({ activeChatId: id, mobileSidebarOpen: false }),

      addMessage: (chatId, msg) =>
        set((state) => ({
          chats: state.chats.map((chat) => {
            if (chat.id !== chatId) return chat;
            const isFirstUserMessage = msg.role === 'user' && chat.messages.length === 0;
            return {
              ...chat,
              title: isFirstUserMessage
                ? msg.content.slice(0, 40) + (msg.content.length > 40 ? '…' : '')
                : chat.title,
              messages: [...chat.messages, msg],
            };
          }),
        })),

      refreshTables: async () => {
        set({ tablesLoading: true });
        try {
          const data = await api.getTables();
          const names = data.tables
            .map((t) => t.name)
            .filter((n) => !['users', 'alert_rules', 'alerts', 'notification_logs'].includes(n));
          set({ tables: names, lastTableRefresh: Date.now(), tablesLoading: false });

          const { selectedTable } = get();
          if (selectedTable && names.includes(selectedTable)) {
            await get().selectTable(selectedTable);
          } else if (names.length > 0 && !selectedTable) {
            await get().selectTable(names[0]);
          }
        } catch {
          set({ tablesLoading: false });
        }
      },

      selectTable: async (name) => {
        set({ selectedTable: name, tablesLoading: true });
        try {
          const data = await api.getTable(name);
          set({
            tableColumns: data.columns.map((c) => c.name),
            tableRows: data.rows,
            tablesLoading: false,
          });
        } catch {
          set({ tableColumns: [], tableRows: [], tablesLoading: false });
        }
      },

      openDataReveal: () => set({ dataRevealOpen: true }),
      closeDataReveal: () => set({ dataRevealOpen: false }),
      toggleDataReveal: () => set((s) => ({ dataRevealOpen: !s.dataRevealOpen })),

      logout: () => {
        localStorage.removeItem(STORAGE_KEYS.token);
        set({
          user: null,
          chats: [],
          activeChatId: null,
          tables: [],
          selectedTable: null,
          tableColumns: [],
          tableRows: [],
          dataRevealOpen: false,
        });
      },
      clearChats: () => set({ chats: [], activeChatId: null }),
      deleteChat: (id) =>
        set((state) => {
          const newChats = state.chats.filter((c) => c.id !== id);
          let newActiveId = state.activeChatId;
          if (state.activeChatId === id) {
            newActiveId = newChats.length > 0 ? newChats[0].id : null;
          }
          return {
            chats: newChats,
            activeChatId: newActiveId,
          };
        }),
    }),
    {
      name: STORAGE_KEYS.chats,
      partialize: (state) => ({
        chats: state.chats,
        activeChatId: state.activeChatId,
      }),
    }
  )
);
