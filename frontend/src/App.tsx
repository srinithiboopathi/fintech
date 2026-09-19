import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { MarketAnalysisPage } from './pages/MarketAnalysisPage';
import { CorrelationLabPage } from './pages/CorrelationLabPage';
import { StrategyBuilderPage } from './pages/StrategyBuilderPage';
import { BacktestingPage } from './pages/BacktestingPage';
import { TradeHistoryPage } from './pages/TradeHistoryPage';
import { RobustnessLabPage } from './pages/RobustnessLabPage';
import { MarketRegimesPage } from './pages/MarketRegimesPage';
import { ResearchReportPage } from './pages/ResearchReportPage';
import { PortfolioAnalyticsPage } from './pages/PortfolioAnalyticsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public standalone pages */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Protected Terminal Application Shell */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/market-analysis" element={<MarketAnalysisPage />} />
            <Route path="/correlation" element={<CorrelationLabPage />} />
            <Route path="/portfolio" element={<PortfolioAnalyticsPage />} />
            <Route path="/strategy-builder" element={<StrategyBuilderPage />} />
            <Route path="/backtesting" element={<BacktestingPage />} />
            <Route path="/trade-history" element={<TradeHistoryPage />} />
            <Route path="/robustness" element={<RobustnessLabPage />} />
            <Route path="/market-regimes" element={<MarketRegimesPage />} />
            <Route path="/research-report" element={<ResearchReportPage />} />
          </Route>
        </Route>

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
