import React, { useState, useEffect } from 'react';
import { ShieldAlert, ShieldCheck, AlertTriangle, Layers, FileSearch, CheckCircle2, XCircle, AlertCircle, Trash2 } from 'lucide-react';

export default function Dashboard({ setActiveTab, setSelectContributor }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/reports/C3');
      if (res.ok) {
        const report = await res.json();
        setData(report);
      }
    } catch (err) {
      console.error("Error fetching report data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleDelete = async (e, cid) => {
    e.stopPropagation();
    if (!window.confirm(`Are you sure you want to delete contributor ${cid}?`)) return;
    
    try {
      setLoading(true);
      await fetch(`/api/contributors/${cid}`, { method: 'DELETE' });
      await fetch(`/api/analyze/all`, { method: 'POST' });
      fetchDashboardData();
    } catch (err) {
      console.error("Error deleting contributor:", err);
      setLoading(false);
    }
  };

  const getBadge = (decision) => {
    if (decision === 'ACCEPT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> ACCEPT
        </span>
      );
    } else if (decision === 'REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle className="w-3.5 h-3.5" /> REVIEW
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
          <XCircle className="w-3.5 h-3.5" /> QUARANTINE
        </span>
      );
    }
  };

  const summary = data?.summary || {
    total_contributors_analyzed: 4,
    accept_count: 3,
    review_count: 0,
    quarantine_count: 1
  };

  const contributors = data?.contributors || [
    { contributor_id: 'C1', decision: 'ACCEPT', risk_score: 0.0, total_samples: 2000, primary_risk_reasons: ['No significant integrity risk evidence observed.'] },
    { contributor_id: 'C2', decision: 'ACCEPT', risk_score: 0.0, total_samples: 2000, primary_risk_reasons: ['No significant integrity risk evidence observed.'] },
    { contributor_id: 'C3', decision: 'QUARANTINE', risk_score: 68.5, total_samples: 2280, primary_risk_reasons: ['Synthetic pattern triggers detected.', 'Excessive exact duplicate flooding.', 'High visual label inconsistency ratio.', 'Significant class distribution shift detected.'] },
    { contributor_id: 'C4', decision: 'ACCEPT', risk_score: 0.0, total_samples: 2000, primary_risk_reasons: ['No significant integrity risk evidence observed.'] }
  ];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex justify-between items-center bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Data Integrity Assurance Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Realtime evidence aggregation and contributor decision monitoring for CIFAR-10 computer vision pipeline.</p>
        </div>
        <button
          onClick={() => { setActiveTab('analysis'); }}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold text-sm transition-all shadow-lg shadow-blue-600/20 flex items-center gap-2"
        >
          <FileSearch className="w-4 h-4" /> Run Integrity Analysis
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-slate-800/60 border border-slate-700/60 p-5 rounded-2xl">
          <div className="flex justify-between items-center text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>Contributors Analyzed</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white mt-3">{summary.total_contributors_analyzed}</div>
          <div className="text-xs text-slate-500 mt-1">Multi-contributor dataset submissions</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/60 p-5 rounded-2xl border-l-4 border-l-emerald-500">
          <div className="flex justify-between items-center text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>ACCEPT Status</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 mt-3">{summary.accept_count}</div>
          <div className="text-xs text-slate-500 mt-1">Passed all 5 detector baseline thresholds</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/60 p-5 rounded-2xl border-l-4 border-l-amber-500">
          <div className="flex justify-between items-center text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>REVIEW Status</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400 mt-3">{summary.review_count}</div>
          <div className="text-xs text-slate-500 mt-1">Moderate anomalies requiring analyst audit</div>
        </div>

        <div className="bg-slate-800/60 border border-slate-700/60 p-5 rounded-2xl border-l-4 border-l-rose-500">
          <div className="flex justify-between items-center text-slate-400 text-xs font-semibold uppercase tracking-wider">
            <span>QUARANTINE Status</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400 mt-3">{summary.quarantine_count}</div>
          <div className="text-xs text-slate-500 mt-1">Multiple high-severity integrity indicators</div>
        </div>
      </div>

      {/* Contributor Grid */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-white">Contributor Pipeline Evaluation</h2>
          <span className="text-xs text-slate-400">Click any contributor card to inspect detector evidence</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {contributors.map((c) => (
            <div
              key={c.contributor_id}
              onClick={() => {
                if (setSelectContributor) setSelectContributor(c.contributor_id);
                setActiveTab('findings');
              }}
              className="bg-slate-800/60 border border-slate-700/80 hover:border-blue-500/50 p-6 rounded-2xl transition-all cursor-pointer group"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-extrabold text-white group-hover:text-blue-400 transition-colors">
                      {c.contributor_id}
                    </span>
                    {getBadge(c.decision)}
                    <button onClick={(e) => handleDelete(e, c.contributor_id)} className="p-1 hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 rounded transition-colors ml-1 z-10" title="Delete Contributor">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    {c.contributor_id === 'C3' ? 'Controlled Manipulated Dataset' : 'Clean Reference Contributor'} &bull; {c.total_samples || 2000} samples
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Risk Score</div>
                  <div className={`text-xl font-bold mt-0.5 ${c.risk_score > 30 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {c.risk_score} <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-700/60 space-y-1.5">
                <div className="text-xs font-semibold text-slate-300">Observed Evidence Summary:</div>
                {c.primary_risk_reasons?.map((reason, idx) => (
                  <div key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${c.decision === 'QUARANTINE' ? 'bg-rose-400' : 'bg-emerald-400'}`} />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
