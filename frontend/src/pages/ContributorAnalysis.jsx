import React, { useState } from 'react';
import { Cpu, Play, CheckCircle2, ShieldCheck, AlertTriangle, XCircle, RefreshCw } from 'lucide-react';

export default function ContributorAnalysis({ setActiveTab, setSelectContributor }) {
  const [selected, setSelected] = useState('C3');
  const [analyzing, setAnalyzing] = useState(false);
  const [resData, setResData] = useState(null);

  const detectors = [
    { id: 'exact_duplicate', name: 'Exact Duplicate Detector', desc: 'SHA-256 byte hash matching for duplicate flooding' },
    { id: 'near_duplicate', name: 'Near-Duplicate Detector', desc: 'pHash perceptual hashing & visual augmentation similarity' },
    { id: 'label_anomaly', name: 'Label Anomaly Detector', desc: 'Deep embedding centroid similarity & visual-label mismatch' },
    { id: 'distribution_shift', name: 'Distribution / OOD Detector', desc: 'Chi-Square class proportion & embedding drift analysis' },
    { id: 'controlled_trigger', name: 'Controlled Trigger Detector', desc: 'Synthetic patch pattern & color spatial frequency analysis' },
  ];

  const handleRunAnalysis = async (cid) => {
    setAnalyzing(true);
    setResData(null);
    try {
      const res = await fetch(`/api/analyze/${cid}`, { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        setResData(json.evaluation);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAnalyzeAll = async () => {
    setAnalyzing(true);
    try {
      const res = await fetch('/api/analyze/all', { method: 'POST' });
      if (res.ok) {
        const json = await res.json();
        const found = json.evaluations.find(e => e.contributor_id === selected);
        setResData(found || json.evaluations[2]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50">
        <h1 className="text-2xl font-bold text-white tracking-tight">Data Integrity Analysis Engine</h1>
        <p className="text-slate-400 text-sm mt-1">Execute all 5 core integrity detectors independently on submitted contributor datasets.</p>
      </div>

      <div className="flex gap-4">
        {['C1', 'C2', 'C3', 'C4'].map((cid) => (
          <button
            key={cid}
            onClick={() => { setSelected(cid); handleRunAnalysis(cid); }}
            className={`flex-1 py-4 px-6 rounded-2xl border transition-all text-left ${
              selected === cid
                ? 'bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10'
                : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:border-slate-600'
            }`}
          >
            <div className="text-xs uppercase font-bold text-slate-500">Contributor</div>
            <div className="text-2xl font-extrabold text-white mt-1">{cid}</div>
            <div className="text-xs text-slate-400 mt-1">
              {cid === 'C3' ? 'Controlled Manipulated' : 'Clean Submission'}
            </div>
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => handleRunAnalysis(selected)}
          disabled={analyzing}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-blue-600/20 flex items-center gap-2 text-sm"
        >
          {analyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
          Analyze {selected} Dataset
        </button>

        <button
          onClick={handleAnalyzeAll}
          disabled={analyzing}
          className="px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white font-semibold rounded-xl border border-slate-600 flex items-center gap-2 text-sm"
        >
          <Cpu className="w-4 h-4" /> Run Full Pipeline Analysis (C1–C4)
        </button>
      </div>

      {/* Detector Suite Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/60 border border-slate-700/80 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-bold text-white mb-4">5 Data Integrity Detectors</h2>
          <div className="space-y-3">
            {detectors.map((d) => (
              <div key={d.id} className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-sm font-semibold text-white">{d.name}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{d.desc}</div>
                </div>
                <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full font-mono">
                  ACTIVE
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Results Box */}
        <div className="bg-slate-800/60 border border-slate-700/80 p-6 rounded-2xl space-y-4">
          <h2 className="text-lg font-bold text-white mb-4">Aggregated Contributor Risk Evaluation</h2>
          
          {resData ? (
            <div className="space-y-5">
              <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 flex justify-between items-center">
                <div>
                  <div className="text-xs text-slate-400">Decision State</div>
                  <div className="text-2xl font-black mt-1 text-white">{resData.decision}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">Risk Score</div>
                  <div className="text-2xl font-black mt-1 text-blue-400">{resData.risk_score} / 100</div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-xs font-semibold text-slate-300">Observed Integrity Risk Reasons:</div>
                {resData.primary_risk_reasons?.map((reason, idx) => (
                  <div key={idx} className="bg-slate-900/40 p-3 rounded-lg border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400 mt-1 flex-shrink-0" />
                    <span>{reason}</span>
                  </div>
                ))}
              </div>

              <button
                onClick={() => {
                  if (setSelectContributor) setSelectContributor(selected);
                  setActiveTab('findings');
                }}
                className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl text-xs transition-all shadow-lg shadow-blue-600/20"
              >
                Inspect Sample-Level Evidence in Findings Browser &rarr;
              </button>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm italic border border-dashed border-slate-700 rounded-xl">
              Click 'Analyze Dataset' above to execute detectors on {selected}.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
