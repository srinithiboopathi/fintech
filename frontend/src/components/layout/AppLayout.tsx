import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  return (
    <div className="min-h-screen bg-[#06090E] text-slate-100 flex font-sans overflow-x-hidden relative">
      {/* Subtle Background Pattern */}
      <div className="fixed inset-0 quant-grid-bg opacity-30 pointer-events-none" />

      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        <TopBar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

        <main className="flex-1 p-4 md:p-6 lg:p-7 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        <footer className="border-t border-[#1E293B] bg-[#0A0E17] px-6 py-2.5 text-center text-xs text-slate-500 font-mono">
          QUANTLAB v0.1.0 • Multi-Asset Financial Intelligence & Backtesting System
        </footer>
      </div>
    </div>
  );
};
