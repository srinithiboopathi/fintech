import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Lock, User as UserIcon, Shield, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { useAuthStore } from '../store/authStore';

export const Login: React.FC = () => {
  const [username, setUsername] = useState('quant_trader');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      login(
        {
          id: 'u-001',
          username: username || 'quant_trader',
          name: 'Alex Vance',
          email: `${username || 'quant_trader'}@quantlab.internal`,
          role: 'Lead Quantitative Researcher',
          tier: 'Enterprise Institutional',
        },
        'mock-jwt-session-token'
      );
      setLoading(false);
      navigate('/dashboard');
    }, 400);
  };

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col items-center justify-center p-4 relative bg-grid-pattern">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-cyan-500/10 blur-3xl pointer-events-none rounded-full" />

      <div className="w-full max-w-md space-y-6 z-10">
        {/* Brand */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-400 to-cyan-400 p-0.5 shadow-xl shadow-cyan-500/20 mb-2">
            <div className="w-full h-full bg-[#080c14] rounded-[14px] flex items-center justify-center">
              <Activity className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
          <h2 className="text-2xl font-black tracking-tight text-white">
            QUANT<span className="text-emerald-400">LAB</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono">Institutional Terminal Authentication</p>
        </div>

        {/* Login Card */}
        <Card variant="glow" className="p-6 border-cyan-500/30">
          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label="Quantitative Trader ID / Email"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              leftIcon={<UserIcon className="w-4 h-4" />}
              required
            />
            <Input
              label="Terminal Access Key / Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="w-4 h-4" />}
              required
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="glow"
                isLoading={loading}
                className="w-full py-2.5 font-bold"
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Authenticate Session
              </Button>
            </div>
          </form>

          {/* Quick Demo Credentials Info */}
          <div className="mt-5 p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex items-center gap-1 text-emerald-400 font-semibold">
              <Shield className="w-3.5 h-3.5" /> Instant Demo Access Active
            </div>
            <div>Username: <span className="text-slate-200">quant_trader</span></div>
            <div>Password: <span className="text-slate-200">password123</span></div>
          </div>
        </Card>

        <div className="text-center text-xs text-slate-500 font-mono">
          <Link to="/" className="text-slate-400 hover:text-cyan-400 transition-colors">
            ← Return to Overview
          </Link>
        </div>
      </div>
    </div>
  );
};
