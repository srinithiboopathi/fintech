import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Shield, ShieldCheck, ArrowLeft, ArrowRight, Lock, KeyRound } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const handleContinueWithMaid = () => {
    // In Phase 1: Frontend entry point directs to dashboard. Full MAID integration will be wired in Phase 14.
    navigate('/dashboard');
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
          <span>Return to Homepage</span>
        </NavLink>
      </div>

      <div className="w-full max-w-md bg-[#0D111A]/95 border border-[#1E293B] rounded-xl p-8 shadow-2xl relative z-10 quant-glass">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-xl mx-auto mb-3">
            QL
          </div>
          <div className="text-xs font-mono uppercase tracking-[0.2em] text-cyan-400 font-semibold mb-1">
            QUANTLAB
          </div>
          <h1 className="text-xl font-bold text-white font-mono tracking-tight">MAID LOGIN</h1>
          <p className="text-xs text-slate-400 mt-1">Multi-Asset Financial Intelligence Terminal Access</p>
        </div>

        {/* MAID Institutional Access Panel */}
        <div className="bg-[#121824] border border-[#1E293B] rounded-lg p-4 mb-6 space-y-2.5">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-cyan-950/80 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold font-mono text-slate-200">MAID Identity Gateway</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                  Phase 14 Prep
                </span>
              </div>
              <span className="text-[11px] text-slate-400 font-mono">Institutional Cryptographic Identity</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Secure single-sign-on protocol configured for quantitative researchers and portfolio operators.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          <Button
            variant="primary"
            size="lg"
            onClick={handleContinueWithMaid}
            className="w-full justify-center space-x-2 text-xs font-mono tracking-wide"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>CONTINUE WITH MAID</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>

          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/dashboard')}
            className="w-full justify-center text-xs font-mono text-slate-400 hover:text-slate-200"
          >
            <KeyRound className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
            <span>Enter Terminal as Guest Analyst</span>
          </Button>
        </div>

        {/* Security Footer Notice */}
        <div className="mt-8 pt-6 border-t border-[#1E293B] text-center space-y-1.5">
          <div className="flex items-center justify-center space-x-1.5 text-[11px] font-mono text-slate-500">
            <Lock className="w-3 h-3 text-cyan-400" />
            <span>Institutional Cryptographic Security</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono">
            Session tokens managed via secure headers and FastAPI middleware.
          </p>
        </div>
      </div>
    </div>
  );
};
