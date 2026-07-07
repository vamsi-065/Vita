import {
  Plus,
  MessageSquare,
  PanelLeftClose,
  PanelLeft,
  LogOut,
  Bell,
  BellOff,
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { clearToken } from '../../services/api';

interface SidebarProps {
  mobile?: boolean;
  onClose?: () => void;
}

export function Sidebar({ mobile = false, onClose }: SidebarProps) {
  const {
    chats,
    activeChatId,
    sidebarCollapsed,
    alertsEnabled,
    user,
    createChat,
    setActiveChat,
    setSidebarCollapsed,
    setAlertsEnabled,
    logout,
  } = useStore();

  const collapsed = !mobile && sidebarCollapsed;

  return (
    <aside
      className={`flex h-full flex-col bg-surface-container border-outline-variant ${
        mobile ? 'w-72 border-r' : collapsed ? 'w-[68px] border-r' : 'w-72 border-r'
      }`}
    >
      <div className={`flex items-center gap-2 p-3 ${collapsed ? 'justify-center' : 'justify-between'}`}>
        {!collapsed && (
          <div className="min-w-0 flex-1 px-1">
            <p className="truncate text-sm font-semibold text-on-surface">AI Business OS</p>
            {user && (
              <p className="truncate text-xs text-on-surface-variant">{user.business_name}</p>
            )}
          </div>
        )}
        {!mobile && (
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-on-surface-variant hover:bg-surface-container-high"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <PanelLeft size={20} /> : <PanelLeftClose size={20} />}
          </button>
        )}
      </div>

      <div className="px-3 pb-2">
        <button
          type="button"
          onClick={() => {
            createChat();
            onClose?.();
          }}
          className={`flex w-full items-center gap-3 rounded-full bg-surface px-4 py-3 text-sm font-medium text-on-surface shadow-sm transition-colors hover:bg-surface-container-highest ${collapsed ? 'justify-center px-0' : ''}`}
        >
          <Plus size={18} />
          {!collapsed && <span>New conversation</span>}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1">
        {!collapsed &&
          chats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              onClick={() => {
                setActiveChat(chat.id);
                onClose?.();
              }}
              className={`mb-0.5 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors ${
                activeChatId === chat.id
                  ? 'bg-surface-container-highest text-on-surface'
                  : 'text-on-surface-variant hover:bg-surface-container-high'
              }`}
            >
              <MessageSquare size={16} className="shrink-0" />
              <span className="truncate">{chat.title}</span>
            </button>
          ))}
      </div>

      <div className="border-t border-outline-variant p-3">
        {!collapsed && (
          <div className="mb-3 flex items-center justify-between rounded-xl bg-surface px-3 py-2.5">
            <div className="flex items-center gap-2">
              {alertsEnabled ? (
                <Bell size={16} className="text-primary" />
              ) : (
                <BellOff size={16} className="text-on-surface-variant" />
              )}
              <div>
                <p className="text-xs font-medium text-on-surface">WhatsApp alerts</p>
                <p className="text-[11px] text-on-surface-variant">Stock & business updates</p>
              </div>
            </div>
            <button
              type="button"
              role="switch"
              aria-checked={alertsEnabled}
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${alertsEnabled ? 'bg-primary' : 'bg-outline'}`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${alertsEnabled ? 'translate-x-5' : ''}`}
              />
            </button>
          </div>
        )}

        <button
          type="button"
          onClick={() => {
            clearToken();
            logout();
          }}
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-on-surface-variant transition-colors hover:bg-surface-container-high ${collapsed ? 'justify-center' : ''}`}
        >
          <LogOut size={16} />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
