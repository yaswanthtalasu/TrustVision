import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import DataIntake from './pages/DataIntake';
import ContributorAnalysis from './pages/ContributorAnalysis';
import Findings from './pages/Findings';
import AssuranceReport from './pages/AssuranceReport';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedContributor, setSelectContributor] = useState('C3');

  return (
    <div className="min-h-screen flex flex-col bg-slate-900 text-slate-100">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        {activeTab === 'dashboard' && <Dashboard setActiveTab={setActiveTab} setSelectContributor={setSelectContributor} />}
        {activeTab === 'intake' && <DataIntake setActiveTab={setActiveTab} />}
        {activeTab === 'analysis' && <ContributorAnalysis setActiveTab={setActiveTab} setSelectContributor={setSelectContributor} />}
        {activeTab === 'findings' && <Findings selectedContributor={selectedContributor} />}
        {activeTab === 'report' && <AssuranceReport />}
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        TrustVision &bull; Multi-Contributor Computer-Vision Data Integrity Assurance Engine
      </footer>
    </div>
  );
}
