import { useNavigate } from 'react-router-dom';
import { useUIStore } from '@/store/uiStore';

export function MainLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const apiToken = useUIStore((state) => state.apiToken);

  const handleLogout = () => {
    localStorage.removeItem('apiToken');
    useUIStore.setState({ apiToken: null });
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white shadow-lg">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-2xl font-bold">bruv-mail</h1>
          <p className="text-sm text-slate-400">Inbox management</p>
        </div>

        <nav className="p-4 space-y-2">
          <button
            onClick={() => navigate('/inbox')}
            className="w-full text-left px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            📬 Inbox
          </button>
          <button
            onClick={() => navigate('/tasks')}
            className="w-full text-left px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            ✓ Tasks
          </button>
          <button
            onClick={() => navigate('/settings')}
            className="w-full text-left px-4 py-2 rounded-lg hover:bg-slate-800 transition-colors"
          >
            ⚙️ Settings
          </button>
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800 w-64">
          <button
            onClick={handleLogout}
            className="w-full py-2 px-4 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
          >
            Logout
          </button>
          {apiToken && (
            <p className="text-xs text-slate-500 mt-2 truncate">
              Token: {apiToken.substring(0, 8)}...
            </p>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
