import React, { useState, useEffect } from 'react';
import { Search, Filter, ShieldAlert, Image as ImageIcon, Tag, Eye } from 'lucide-react';

export default function Findings({ selectedContributor = 'C3' }) {
  const [contributor, setContributor] = useState(selectedContributor);
  const [evidenceData, setEvidenceData] = useState(null);
  const [activeDetectorFilter, setActiveDetectorFilter] = useState('ALL');

  const fetchEvidence = async (cid) => {
    try {
      const res = await fetch(`/api/results/${cid}`);
      if (res.ok) {
        const json = await res.json();
        setEvidenceData(json);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchEvidence(contributor);
  }, [contributor]);

  const allEvents = evidenceData?.evidence?.all_sample_evidence || [];
  const filteredEvents = activeDetectorFilter === 'ALL'
    ? allEvents
    : allEvents.filter(e => e.detector === activeDetectorFilter);

  return (
    <div className="space-y-8">
      <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sample-Level Evidence Browser</h1>
          <p className="text-slate-400 text-sm mt-1">Audit granular sample-level evidence events extracted by detectors.</p>
        </div>

        <div className="flex bg-slate-900 p-1.5 rounded-xl border border-slate-700">
          {['C1', 'C2', 'C3', 'C4'].map((cid) => (
            <button
              key={cid}
              onClick={() => setContributor(cid)}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${
                contributor === cid ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {cid}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-slate-700/60 pb-3 overflow-x-auto">
        {[
          { id: 'ALL', label: 'All Evidence Events' },
          { id: 'controlled_trigger', label: 'Synthetic Patch Triggers' },
          { id: 'exact_duplicate', label: 'Exact Duplicates' },
          { id: 'label_anomaly', label: 'Label Anomalies' },
          { id: 'near_duplicate', label: 'Near-Duplicates' },
          { id: 'distribution_shift', label: 'Class Distribution Shift' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveDetectorFilter(tab.id)}
            className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
              activeDetectorFilter === tab.id
                ? 'bg-slate-800 text-blue-400 border border-blue-500/40'
                : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Evidence Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredEvents.length === 0 ? (
          <div className="col-span-2 py-16 text-center text-slate-500 italic bg-slate-800/20 rounded-2xl border border-dashed border-slate-700">
            No evidence events matching filter for contributor {contributor}.
          </div>
        ) : (
          filteredEvents.map((item, idx) => (
            <div key={idx} className="bg-slate-800/60 border border-slate-700/80 p-5 rounded-2xl space-y-3">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono bg-slate-900 border border-slate-700 px-2.5 py-1 rounded-md text-blue-400">
                    {item.sample_id}
                  </span>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                    item.severity === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                    item.severity === 'HIGH' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                    'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  }`}>
                    {item.severity}
                  </span>
                </div>

                <span className="text-xs text-slate-400 uppercase font-mono">{item.detector}</span>
              </div>

              <div className="text-xs text-slate-200 font-medium">{item.description}</div>

              {/* Raw Evidence Payload */}
              <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-xs font-mono text-slate-400 space-y-1">
                {Object.entries(item.evidence || {}).map(([key, val]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-slate-500">{key}:</span>
                    <span className="text-slate-200">{typeof val === 'object' ? JSON.stringify(val) : String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
