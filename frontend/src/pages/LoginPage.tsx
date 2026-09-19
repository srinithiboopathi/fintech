import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Shield, ShieldCheck, ArrowLeft, ArrowRight, Lock } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const handleContinueWithMaid = () => {
    // In Phase 1: Frontend entry point directs to dashboard. Full MAID integration will be wired in Phase 14.
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-100 flex flex-col justify-center items-center px-4 font-sans relative">
      {/* Background Matrix Grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#161F2E15_1px,transparent_1px),linear-gradient(to_bottom,#161F2E15_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

      {/* Top back navigation */}
      <div className="absolute top-6 left-6 z-20">
        <NavLink to="/" className="inline-flex items-center space-x-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Homepage</span>
        </NavLink>
      </div>

      <div className="w-full max-w-md bg-[#111722] border border-[#232E42] rounded-xl p-8 shadow-2xl relative z-10">
        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-mono font-bold text-xl mx-auto mb-3">
            QL
          </div>
          <h1 className="text-xl font-bold text-white font-mono tracking-wide">QUANTLAB</h1>
          <p className="text-xs text-slate-400 mt-1">Multi-Asset Financial Intelligence Terminal</p>
        </div>

        {/* MAID Authentication Banner */}
        <div className="bg-[#161F2E] border border-[#232E42] rounded-lg p-4 mb-6">
          <div className="flex items-center space-x-3 mb-2">
            <div className="w-8 h-8 rounded bg-cyan-950 border border-cyan-700/60 flex items-center justify-center text-cyan-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold font-mono text-slate-200">MAID Identity Gateway</span>
                <Badge variant="cyan" size="xs">Phase 14 Prep</Badge>
              </div>
              <span className="text-[11px] text-slate-400">Decentralized / Institutional Identity Access</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Secure single-sign-on protocol configured for quantitative researchers and institutional portfolio operators.
          </p>
        </div>

        {/* Action Button */}
        <div className="space-y-3">
          <Button
            variant="primary"
            size="lg"
            onClick={handleContinueWithMaid}
            className="w-full justify-center space-x-2 text-xs font-mono"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Continue with MAID</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Button>

          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/dashboard')}
            className="w-full justify-center text-xs font-mono text-slate-400"
          >
            <span>Enter Terminal as Guest Analyst</span>
          </Button>
        </div>

        {/* Security & Integrity Notice */}
        <div className="mt-8 pt-6 border-t border-[#232E42] text-center space-y-2">
          <div className="flex items-center justify-center space-x-1.5 text-[11px] font-mono text-slate-500">
            <Lock className="w-3 h-3 text-emerald-400" />
            <span>End-to-End Cryptographic Security</span>
          </div>
          <p className="text-[10px] text-slate-500">
            Session tokens are managed via secure HTTPS headers and FastAPI backend middleware.
          </p>
        </div>
      </div>
    </div>
  );
};
