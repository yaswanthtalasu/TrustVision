import React, { useState, useEffect } from 'react';
import { FileText, Code, ExternalLink, ShieldCheck, Download } from 'lucide-react';

export default function AssuranceReport() {
  const [activeView, setActiveView] = useState('HTML');
  const [reportData, setReportData] = useState(null);

  const fetchReport = async () => {
    try {
      const res = await fetch('/api/reports/C3');
      if (res.ok) {
        const json = await res.json();
        setReportData(json);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchReport();
  }, []);

  return (
    <div className="space-y-8">
      <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Cryptographic Assurance Report</h1>
          <p className="text-slate-400 text-sm mt-1">Standalone HTML assurance report and machine-readable JSON manifest artifacts.</p>
        </div>

        <div className="flex bg-slate-900 p-1 rounded-xl border border-slate-700">
          <button
            onClick={() => setActiveView('HTML')}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center gap-2 transition-all ${
              activeView === 'HTML' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" /> Formatted HTML
          </button>
          <button
            onClick={() => setActiveView('JSON')}
            className={`px-4 py-2 text-xs font-bold rounded-lg flex items-center gap-2 transition-all ${
              activeView === 'JSON' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Code className="w-4 h-4" /> Raw JSON Report
          </button>
        </div>
      </div>

      {activeView === 'HTML' ? (
        <div className="bg-white rounded-2xl overflow-hidden shadow-2xl border border-slate-700 min-h-[650px]">
          <iframe
            src="/api/reports/view/html"
            className="w-full h-[700px] border-none"
            title="TrustVision HTML Report"
          />
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl font-mono text-xs text-slate-300 overflow-x-auto max-h-[700px]">
          <pre>{JSON.stringify(reportData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
