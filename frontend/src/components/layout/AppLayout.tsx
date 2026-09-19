import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-100 flex font-sans overflow-x-hidden">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>

        <footer className="border-t border-[#232E42] bg-[#0E131C] px-6 py-3 text-center text-xs text-slate-500 font-mono">
          QUANTLAB v0.1.0 • Multi-Asset Financial Intelligence & Backtesting System
        </footer>
      </div>
    </div>
  );
};
