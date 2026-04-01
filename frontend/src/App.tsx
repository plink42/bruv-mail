import { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { LoginPage } from '@/pages/LoginPage';
import { InboxPage } from '@/pages/InboxPage';
import { TasksPage } from '@/pages/TasksPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { MainLayout } from '@/components/MainLayout';
import { useUIStore } from '@/store/uiStore';

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const apiToken = useUIStore((state) => state.apiToken);
  const storedToken = localStorage.getItem('apiToken');
  const token = apiToken || storedToken;

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  useUIStore.setState({ apiToken: token });

  return <MainLayout>{children}</MainLayout>;
}

function AppRoutes() {
  const apiToken = useUIStore((state) => state.apiToken);
  const storedToken = localStorage.getItem('apiToken');
  const token = apiToken || storedToken;

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/inbox"
        element={
          <ProtectedRoute>
            <Suspense fallback={<div className="flex items-center justify-center h-screen">Loading...</div>}>
              <InboxPage />
            </Suspense>
          </ProtectedRoute>
        }
      />
      <Route
        path="/tasks"
        element={
          <ProtectedRoute>
            <div className="p-6">
              <h1 className="text-2xl font-bold">Tasks</h1>
              <p className="text-slate-600 mt-2">Coming in Phase 3</p>
            </div>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <div className="p-6">
              <h1 className="text-2xl font-bold">Settings</h1>
              <p className="text-slate-600 mt-2">Coming in Phase 4</p>
            </div>
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to={token ? '/inbox' : '/login'} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
