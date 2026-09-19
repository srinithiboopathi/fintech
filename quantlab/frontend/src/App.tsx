import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';

// Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { MarketAnalysis } from './pages/MarketAnalysis';
import { CorrelationLab } from './pages/CorrelationLab';
import { StrategyBuilder } from './pages/StrategyBuilder';
import { Backtesting } from './pages/Backtesting';
import { TradeHistory } from './pages/TradeHistory';
import { RobustnessLab } from './pages/RobustnessLab';
import { MarketRegimes } from './pages/MarketRegimes';
import { ResearchReport } from './pages/ResearchReport';

const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col">
      <Navbar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <main className="flex-1 flex overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Landing & Login */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />

        {/* Protected / App Workspace */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/market-analysis" element={<MarketAnalysis />} />
          <Route path="/correlation-lab" element={<CorrelationLab />} />
          <Route path="/strategy-builder" element={<StrategyBuilder />} />
          <Route path="/backtesting" element={<Backtesting />} />
          <Route path="/trade-history" element={<TradeHistory />} />
          <Route path="/robustness-lab" element={<RobustnessLab />} />
          <Route path="/market-regimes" element={<MarketRegimes />} />
          <Route path="/research-report" element={<ResearchReport />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
