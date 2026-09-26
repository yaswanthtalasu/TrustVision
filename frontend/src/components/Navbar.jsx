import React from 'react';
import { ShieldCheck, Database, Search, FileText, LayoutDashboard, Cpu, Lock } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'intake', label: 'Data Intake', icon: Database },
    { id: 'analysis', label: 'Contributor Analysis', icon: Cpu },
    { id: 'findings', label: 'Findings Browser', icon: Search },
    { id: 'report', label: 'Assurance Report', icon: FileText },
    { id: 'model_integrity', label: 'Model Integrity', icon: Lock },
  ];

  return (
    <header className="bg-slate-800/80 backdrop-blur-md border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="p-2 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="font-bold text-lg text-white tracking-wide flex items-center gap-2">
              TrustVision <span className="text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-mono">v1.0</span>
            </div>
            <div className="text-xs text-slate-400">Data Integrity Assurance System</div>
          </div>
        </div>

        <nav className="flex space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
