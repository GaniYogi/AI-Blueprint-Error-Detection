import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { Dashboard } from './pages/Dashboard';
import { UploadPage } from './pages/UploadPage';
import { AnalysisResultsPage } from './pages/AnalysisResultsPage';
import { ReportsPage } from './pages/ReportsPage';
import { 
  Layers, 
  Layout, 
  UploadCloud, 
  FileText, 
  Sun, 
  Moon, 
  Menu, 
  X,
  User
} from 'lucide-react';

// Theme toggler logic
const ThemeToggle: React.FC = () => {
  const [isDark, setIsDark] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);
    if (nextDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-2 bg-primary-100 hover:bg-primary-200 dark:bg-primary-900 dark:hover:bg-primary-800 text-primary-600 dark:text-primary-400 rounded-xl transition-colors"
      title="Toggle Light/Dark Theme"
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
};

// Protected route guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-primary-950">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
};

// Layout with Sidebar and Header
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Layout },
    { name: 'Upload Blueprints', href: '/upload', icon: UploadCloud },
    { name: 'Compliance Reports', href: '/reports', icon: FileText },
  ];

  // No logout handler needed

  const getPageTitle = () => {
    const item = navigation.find(n => n.href === location.pathname);
    if (item) return item.name;
    if (location.pathname.startsWith('/results/')) return 'Blueprint Analysis Diagnostics';
    return 'BlueprintAI';
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-primary-950 text-primary-900 dark:text-primary-100 flex transition-colors duration-300">
      
      {/* Mobile Sidebar Back Drop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Panel */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-primary-900 border-r border-primary-200 dark:border-primary-800 flex flex-col justify-between transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:h-screen lg:z-auto shrink-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex flex-col flex-1">
          {/* Logo area */}
          <div className="h-16 flex items-center justify-between px-6 border-b border-primary-100 dark:border-primary-800">
            <div className="flex items-center space-x-3">
              <div className="p-1.5 bg-indigo-600 rounded-lg text-white">
                <Layers className="h-5 w-5" />
              </div>
              <span className="font-extrabold font-heading text-lg tracking-tight bg-gradient-to-r from-indigo-500 to-indigo-600 bg-clip-text text-transparent">
                BlueprintAI
              </span>
            </div>
            <button 
              className="lg:hidden p-1.5 text-primary-500 hover:bg-primary-100 dark:hover:bg-primary-800 rounded-lg"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Links */}
          <nav className="flex-1 px-4 py-6 space-y-1.5">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                    isActive 
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/15' 
                      : 'text-primary-500 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-800/60 hover:text-primary-900 dark:hover:text-primary-100'
                  }`}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer profile & logout */}
        <div className="p-4 border-t border-primary-100 dark:border-primary-800 space-y-2.5">
          {user && (
            <div className="flex items-center space-x-3 px-2 py-1.5 rounded-lg">
              <div className="p-2 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 rounded-lg">
                <User className="h-4.5 w-4.5" />
              </div>
              <div className="text-left min-w-0 flex-1">
                <p className="text-xs font-bold truncate text-primary-950 dark:text-primary-100 leading-tight">
                  {user.full_name || 'Architect User'}
                </p>
                <p className="text-[10px] truncate text-primary-400 leading-none mt-0.5">{user.email}</p>
              </div>
            </div>
          )}
          {/* Sign Out button removed */}
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto h-screen relative">
        
        {/* Top Header */}
        <header className="h-16 flex items-center justify-between px-6 bg-white dark:bg-primary-900 border-b border-primary-200 dark:border-primary-800 sticky top-0 z-30 shrink-0">
          <div className="flex items-center space-x-3">
            <button 
              className="lg:hidden p-2 text-primary-500 hover:bg-primary-100 dark:hover:bg-primary-800 rounded-xl"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>
            <h1 className="text-lg sm:text-xl font-bold font-heading">{getPageTitle()}</h1>
          </div>
          <div className="flex items-center space-x-4">
            <ThemeToggle />
          </div>
        </header>

        {/* Content Viewport */}
        <main className="p-6 sm:p-8 flex-1 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

    </div>
  );
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      
      {/* Protected Layout Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><MainLayout><Dashboard /></MainLayout></ProtectedRoute>} />
      <Route path="/upload" element={<ProtectedRoute><MainLayout><UploadPage /></MainLayout></ProtectedRoute>} />
      <Route path="/results/:id" element={<ProtectedRoute><MainLayout><AnalysisResultsPage /></MainLayout></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><MainLayout><ReportsPage /></MainLayout></ProtectedRoute>} />
      
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

function App() {
  useEffect(() => {
    const isDark = localStorage.getItem('theme') === 'dark' || 
      (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
