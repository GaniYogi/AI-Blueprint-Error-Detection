import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Layers, 
  ShieldCheck, 
  FileSearch, 
  AlertTriangle, 
  ChevronRight, 
  Scale, 
  X, 
  Lock, 
  Mail, 
  User as UserIcon, 
  Zap, 
  AlertCircle,
  RefreshCw
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, isAuthenticated } = useAuth();

  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openModal = (mode: 'signin' | 'signup') => {
    setAuthMode(mode);
    setError(null);
    setShowAuthModal(true);
  };

  const handleFillDemo = () => {
    setEmail('architect@blueprint.ai');
    setPassword('blueprint_default_pass_2026');
    setFullName('Architect User');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (authMode === 'signin') {
        await login(email, password);
      } else {
        await register(email, password, fullName || 'New User');
      }
      setShowAuthModal(false);
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Auth error:', err);
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError('Authentication failed. Please verify email and password.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-primary-950 text-primary-900 dark:text-primary-100 transition-colors duration-300">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass-panel shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-600 rounded-lg text-white">
              <Layers className="h-6 w-6" />
            </div>
            <span className="text-xl font-bold tracking-tight font-heading bg-gradient-to-r from-indigo-500 to-indigo-600 bg-clip-text text-transparent">
              BlueprintAI
            </span>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <Link 
                to="/dashboard" 
                className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-all shadow-md shadow-indigo-600/20"
              >
                Go to Workspace
              </Link>
            ) : (
              <>
                <button 
                  onClick={() => openModal('signin')} 
                  className="px-4 py-2 text-sm font-semibold text-primary-600 dark:text-primary-300 hover:text-indigo-600 transition-colors"
                >
                  Sign In
                </button>
                <button 
                  onClick={() => openModal('signup')} 
                  className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-all shadow-md shadow-indigo-600/20"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6 text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-100 dark:border-indigo-900 rounded-full text-sm text-indigo-600 dark:text-indigo-400">
              <ShieldCheck className="h-4 w-4" />
              <span className="font-medium">Next-Generation Blueprint Analysis</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight tracking-tight">
              Detect Construction Errors <br />
              <span className="bg-gradient-to-r from-indigo-500 via-indigo-600 to-emerald-500 bg-clip-text text-transparent">
                Before Breaking Ground
              </span>
            </h1>
            <p className="text-lg text-primary-600 dark:text-primary-400 max-w-xl">
              An AI-powered computer vision platform that automatically audits architectural blueprints, extracts annotations via OCR, identifies drawing violations, and runs residential building code compliance checks.
            </p>
            <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
              <button 
                onClick={() => openModal('signin')}
                className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl transition-all shadow-lg shadow-indigo-600/30 group"
              >
                Start Free Analysis
                <ChevronRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </button>
              <a href="#features" className="inline-flex items-center justify-center px-6 py-3 text-base font-semibold border border-primary-200 dark:border-primary-800 hover:bg-primary-100 dark:hover:bg-primary-900/40 rounded-xl transition-colors">
                Explore Features
              </a>
            </div>
          </div>

          {/* Interactive Hero Image Visualizer Mock */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-tr from-indigo-500 to-emerald-500 opacity-20 blur-3xl rounded-full"></div>
            <div className="relative glass-panel rounded-2xl shadow-2xl p-4 border border-primary-200/50 dark:border-primary-800/30 overflow-hidden">
              <div className="flex items-center justify-between border-b border-primary-100 dark:border-primary-800 pb-3 mb-3">
                <div className="flex items-center space-x-2">
                  <span className="h-3 w-3 rounded-full bg-rose-500"></span>
                  <span className="h-3 w-3 rounded-full bg-amber-500"></span>
                  <span className="h-3 w-3 rounded-full bg-emerald-500"></span>
                  <span className="text-xs text-primary-500 ml-2">blueprint_layout_rev1.png</span>
                </div>
                <div className="px-2 py-0.5 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold rounded">
                  92.5% Compliant
                </div>
              </div>
              <div className="relative bg-slate-900 border border-primary-800 rounded-lg aspect-[4/3] flex items-center justify-center overflow-hidden">
                {/* Blueprint lines Grid */}
                <div className="absolute inset-0 grid grid-cols-12 gap-1 opacity-20 pointer-events-none">
                  {Array.from({ length: 48 }).map((_, i) => (
                    <div key={i} className="border-[0.5px] border-indigo-400/40 h-full w-full"></div>
                  ))}
                </div>
                
                {/* Visualizer Objects */}
                <div className="absolute border border-indigo-500 bg-indigo-500/10 text-indigo-400 text-[9px] font-bold px-1.5 py-0.5 rounded left-[10%] top-[10%] w-[45%] h-[40%]">
                  Living Room
                  <span className="absolute bottom-1 right-1 font-mono text-[7px] text-indigo-300">16' x 14'</span>
                </div>
                <div className="absolute border border-indigo-500 bg-indigo-500/10 text-indigo-400 text-[9px] font-bold px-1.5 py-0.5 rounded left-[60%] top-[10%] w-[30%] h-[30%]">
                  Bedroom 1
                  <span className="absolute bottom-1 right-1 font-mono text-[7px] text-indigo-300">12' x 11'</span>
                </div>
                
                {/* Warning Overlay */}
                <div className="absolute border border-rose-500 bg-rose-500/15 text-rose-500 text-[9px] font-bold px-1.5 py-0.5 rounded left-[10%] top-[60%] w-[35%] h-[30%] animate-pulse">
                  <span className="flex items-center space-x-1">
                    <AlertTriangle className="h-3 w-3 text-rose-500" />
                    <span>Disconnected Kitchen</span>
                  </span>
                  <span className="absolute bottom-1 left-1.5 font-normal text-[7px] text-rose-400 leading-tight block">No interior door connecting room</span>
                </div>

                <div className="absolute border border-amber-500 bg-amber-500/10 text-amber-500 text-[9px] font-bold px-1.5 py-0.5 rounded left-[50%] top-[60%] w-[40%] h-[25%]">
                  Bedroom 2 (Vulnerable)
                  <span className="absolute bottom-1 right-1 font-mono text-[7px] text-amber-300">8' x 8' (Min 70 sq ft)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-20 bg-white dark:bg-primary-900/30 border-y border-primary-200/50 dark:border-primary-800/30">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-4">
            <h2 className="text-3xl font-bold font-heading">Automated Blueprint Diagnostics</h2>
            <p className="text-primary-600 dark:text-primary-400">
              Our AI engine leverages object detection and OCR algorithms to map blueprints and run checks against standard building codes.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="p-6 glass-card rounded-xl border border-primary-200/40 dark:border-primary-800/20 text-left space-y-4 hover:shadow-lg transition-shadow">
              <div className="p-3 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 w-fit rounded-lg">
                <FileSearch className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Blueprint Analysis Engine</h3>
              <p className="text-sm text-primary-600 dark:text-primary-400 leading-relaxed">
                Automatically identifies walls, doors, windows, staircases, and rooms with high spatial precision.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 glass-card rounded-xl border border-primary-200/40 dark:border-primary-800/20 text-left space-y-4 hover:shadow-lg transition-shadow">
              <div className="p-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 w-fit rounded-lg">
                <Scale className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Rule Engine Compliance</h3>
              <p className="text-sm text-primary-600 dark:text-primary-400 leading-relaxed">
                Validates layouts against adjustable building code thresholds, assessing bedroom sizes, corridors, and doors.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 glass-card rounded-xl border border-primary-200/40 dark:border-primary-800/20 text-left space-y-4 hover:shadow-lg transition-shadow">
              <div className="p-3 bg-rose-500/10 text-rose-600 dark:text-rose-400 w-fit rounded-lg">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold">Error Detection</h3>
              <p className="text-sm text-primary-600 dark:text-primary-400 leading-relaxed">
                Highlights disconnected rooms, wall overlaps, missing annotations, and structural conflicts interactively.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 bg-slate-900 text-slate-400 border-t border-slate-800 text-sm">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between">
          <div className="flex items-center space-x-2 text-white font-bold mb-4 sm:mb-0">
            <Layers className="h-5 w-5 text-indigo-500" />
            <span>BlueprintAI</span>
          </div>
          <div>
            &copy; {new Date().getFullYear()} BlueprintAI Systems Inc. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Authentication Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-md bg-white dark:bg-primary-900 rounded-2xl border border-primary-200 dark:border-primary-800 shadow-2xl overflow-hidden p-6 sm:p-8 space-y-6 text-left">
            
            {/* Close Button */}
            <button 
              onClick={() => setShowAuthModal(false)}
              className="absolute top-4 right-4 p-2 text-primary-400 hover:text-primary-600 dark:hover:text-primary-200 rounded-lg hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Modal Header */}
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 bg-indigo-600 rounded-md text-white">
                  <Layers className="h-5 w-5" />
                </div>
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-indigo-500 to-indigo-600 bg-clip-text text-transparent">
                  BlueprintAI
                </span>
              </div>
              <h3 className="text-2xl font-extrabold tracking-tight pt-2">
                {authMode === 'signin' ? 'Sign In to Workspace' : 'Create Architect Account'}
              </h3>
              <p className="text-xs text-primary-500">
                {authMode === 'signin' ? 'Enter your credentials to access saved blueprints' : 'Register to upload, analyze, and manage blueprint diagnostics'}
              </p>
            </div>

            {/* Tabs */}
            <div className="flex bg-primary-100 dark:bg-primary-950 p-1 rounded-xl text-xs font-bold">
              <button
                type="button"
                onClick={() => { setAuthMode('signin'); setError(null); }}
                className={`flex-1 py-2 rounded-lg transition-all ${
                  authMode === 'signin' 
                    ? 'bg-white dark:bg-primary-800 text-indigo-600 dark:text-white shadow-sm' 
                    : 'text-primary-500 hover:text-primary-900 dark:hover:text-primary-100'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setAuthMode('signup'); setError(null); }}
                className={`flex-1 py-2 rounded-lg transition-all ${
                  authMode === 'signup' 
                    ? 'bg-white dark:bg-primary-800 text-indigo-600 dark:text-white shadow-sm' 
                    : 'text-primary-500 hover:text-primary-900 dark:hover:text-primary-100'
                }`}
              >
                Create Account
              </button>
            </div>

            {/* Demo Credentials Quick Fill Button */}
            <button
              type="button"
              onClick={handleFillDemo}
              className="w-full py-2 px-3 bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-200 dark:border-indigo-800/80 rounded-xl text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 flex items-center justify-center space-x-1.5 transition-colors"
            >
              <Zap className="h-4 w-4 text-indigo-500 shrink-0" />
              <span>Auto-Fill Demo Credentials (architect@blueprint.ai)</span>
            </button>

            {/* Error Display */}
            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl flex items-center space-x-2 text-rose-600 dark:text-rose-400 text-xs">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {authMode === 'signup' && (
                <div className="space-y-1">
                  <label className="text-xs font-bold text-primary-700 dark:text-primary-300">Full Name</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-3 h-4 w-4 text-primary-400" />
                    <input
                      type="text"
                      required
                      placeholder="Jane Architect"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full pl-9 pr-4 py-2.5 bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-800 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>
              )}

              <div className="space-y-1">
                <label className="text-xs font-bold text-primary-700 dark:text-primary-300">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-primary-400" />
                  <input
                    type="email"
                    required
                    placeholder="architect@blueprint.ai"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-800 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-primary-700 dark:text-primary-300">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-primary-400" />
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 bg-primary-50 dark:bg-primary-950 border border-primary-200 dark:border-primary-800 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-600/25 flex items-center justify-center space-x-2 transition-all disabled:opacity-50 mt-2"
              >
                {submitting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>{authMode === 'signin' ? 'Sign In to Workspace' : 'Create & Launch Account'}</span>
                )}
              </button>
            </form>

          </div>
        </div>
      )}
    </div>
  );
};
