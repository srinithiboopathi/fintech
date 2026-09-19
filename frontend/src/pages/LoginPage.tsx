import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Lock, Mail, User as UserIcon, LogIn, UserPlus, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { authApi } from '../api';
import { useAppStore } from '../store/useAppStore';
import { extractErrorMessage } from '../lib/api';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setAuth, setDemoAuth, isAuthenticated } = useAppStore();

  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [fullName, setFullName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect to destination or dashboard
  const destination = (location.state as any)?.from?.pathname || '/dashboard';

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, navigate, destination]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic client validation
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setError('Please enter your email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }
    if (mode === 'register' && password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        const response = await authApi.login({
          email: trimmedEmail,
          password,
        });
        setAuth(response.user, response.access_token);
      } else {
        const response = await authApi.register({
          email: trimmedEmail,
          password,
          full_name: fullName.trim() || undefined,
        });
        setAuth(response.user, response.access_token);
      }
      navigate(destination, { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAccess = () => {
    setDemoAuth();
    navigate(destination, { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#06090E] text-slate-100 flex flex-col justify-center items-center px-4 font-sans relative overflow-x-hidden">
      {/* Background Matrix Grid & Glow */}
      <div className="fixed inset-0 quant-grid-bg opacity-50 pointer-events-none" />
      <div className="fixed inset-0 quant-glow pointer-events-none" />

      {/* Top back navigation */}
      <div className="absolute top-6 left-6 z-20">
        <NavLink
          to="/"
          className="inline-flex items-center space-x-2 text-xs font-mono text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Overview</span>
        </NavLink>
      </div>

      <div className="w-full max-w-md bg-[#0D111A]/95 border border-[#1E293B] rounded-xl p-8 shadow-2xl relative z-10 quant-glass">
        {/* Brand header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-xl mx-auto mb-3">
            QL
          </div>
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400 font-semibold mb-1">
            QUANTLAB
          </div>
          <h1 className="text-xl font-bold text-white font-mono tracking-tight">
            {mode === 'login' ? 'EMAIL LOGIN' : 'CREATE ACCOUNT'}
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Secure access to your financial intelligence terminal
          </p>
        </div>

        {/* Tab switcher: Sign In vs Register */}
        <div className="flex bg-[#121824] p-1 rounded-lg border border-[#1E293B] mb-6 font-mono text-xs">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            className={`flex-1 py-1.5 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              mode === 'login'
                ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError(null);
            }}
            className={`flex-1 py-1.5 rounded flex items-center justify-center space-x-1.5 transition-colors ${
              mode === 'register'
                ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Account</span>
          </button>
        </div>

        {/* Error Callout */}
        {error && (
          <div className="mb-5 bg-rose-950/30 border border-rose-800/60 rounded-lg p-3 flex items-start space-x-2.5 text-xs text-rose-300 font-mono">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
                Full Name (Optional)
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-slate-500 absolute left-3 top-2.5 pointer-events-none" />
                <Input
                  type="text"
                  placeholder="e.g. Alex Morgan"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="pl-9"
                  disabled={loading}
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5 pointer-events-none" />
              <Input
                type="email"
                placeholder="analyst@quantlab.io"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-9"
                required
                disabled={loading}
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5 pointer-events-none" />
              <Input
                type="password"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-9"
                required
                disabled={loading}
              />
            </div>
            {mode === 'register' && (
              <p className="text-[10px] text-slate-500 font-mono mt-1">
                Minimum 6 characters. Passwords are securely hashed with bcrypt.
              </p>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            disabled={loading}
            isLoading={loading}
            className="w-full justify-center space-x-2 text-xs font-mono tracking-wide mt-2"
          >
            <span>{mode === 'login' ? 'CONTINUE →' : 'CREATE ACCOUNT →'}</span>
          </Button>
        </form>

        {/* Divider */}
        <div className="relative my-6 text-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#1E293B]"></div>
          </div>
          <span className="relative bg-[#0D111A] px-3 text-[10px] font-mono text-slate-500 uppercase">
            OR DEMO MODE
          </span>
        </div>

        {/* Demo Analyst Access Button */}
        <Button
          type="button"
          variant="outline"
          size="md"
          onClick={handleDemoAccess}
          className="w-full justify-center text-xs font-mono text-slate-300 hover:text-white border-slate-700 hover:bg-[#161F2E]"
        >
          <span>ENTER AS DEMO ANALYST</span>
          <ArrowRight className="w-3.5 h-3.5 ml-1.5 text-cyan-400" />
        </Button>

        {/* Security Footer Notice */}
        <div className="mt-6 pt-5 border-t border-[#1E293B] text-center space-y-1">
          <div className="flex items-center justify-center space-x-1.5 text-[11px] font-mono text-slate-400">
            <Lock className="w-3 h-3 text-cyan-400" />
            <span>Secure Password Hashing & JWT Sessions</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono">
            FastAPI token authentication with SQLite/PostgreSQL persistence.
          </p>
        </div>
      </div>
    </div>
  );
};
