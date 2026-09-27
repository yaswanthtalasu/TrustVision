import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, AlertTriangle, CheckCircle2, Play, RefreshCw, XOctagon } from "lucide-react";

export default function InferenceIntegrity() {
  const [record, setRecord] = useState(null);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleRunInference = async () => {
    if (!selectedFile) {
      alert("Please select an image file first.");
      return;
    }
    setLoading(true);
    setVerification(null);
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      const res = await fetch("http://localhost:8000/api/inference/run", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setRecord(data);
      // Auto-verify
      handleVerify(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleVerify = async (recToVerify = record) => {
    if (!recToVerify) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/inference/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recToVerify),
      });
      const data = await res.json();
      setVerification(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleTamper = async () => {
    if (!record) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/inference/tamper-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      });
      const data = await res.json();
      setVerification(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleReplay = async () => {
    if (!record) return;
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/inference/replay-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      });
      const data = await res.json();
      setVerification(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <ShieldCheck className="w-7 h-7 text-emerald-400" />
            Inference Integrity Assurance
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Verify inference records were generated from trusted models and remain unmodified.
          </p>
        </div>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-xl max-w-2xl">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Input Image</label>
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleFileChange}
              className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-700 file:text-emerald-400 hover:file:bg-slate-600 transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Approved Model</label>
            <select disabled className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-300 opacity-80 cursor-not-allowed">
              <option>ResNet18-Clean</option>
            </select>
          </div>
          <button
            onClick={handleRunInference}
            disabled={loading || !selectedFile}
            className="mt-4 flex items-center justify-center w-full gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-3 rounded-lg font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-5 h-5" /> RUN VERIFIED INFERENCE
          </button>
        </div>
      </div>

      {!record && !loading && (
        <div className="text-slate-500 italic mt-8 p-4 border border-slate-700/50 rounded-lg bg-slate-800/30">
          No inference evidence created yet. Upload an image and run inference to generate a secure record.
        </div>
      )}

      {record && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-xl">
            <h3 className="text-lg font-bold mb-4 border-b border-slate-700 pb-2">
              Inference Record
            </h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="grid grid-cols-3"><span className="text-slate-400">Record ID</span> <span className="col-span-2">{record.record_id}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Sequence</span> <span className="col-span-2">{record.sequence_id}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Model ID</span> <span className="col-span-2">{record.model_id}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Prediction</span> <span className="col-span-2 font-bold text-blue-400">{record.prediction}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Confidence</span> <span className="col-span-2">{record.confidence}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Input SHA-256</span> <span className="col-span-2 truncate" title={record.input_hash}>{record.input_hash}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Model SHA-256</span> <span className="col-span-2 truncate" title={record.model_hash}>{record.model_hash}</span></div>
              <div className="grid grid-cols-3"><span className="text-slate-400">Signature</span> <span className="col-span-2 truncate text-xs" title={record.signature}>{record.signature}</span></div>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-3 border-t border-slate-700 pt-4">
              <button onClick={() => handleVerify(record)} className="flex-1 bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded flex items-center justify-center gap-2 transition-colors">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Verify Original
              </button>
              <button onClick={handleTamper} className="flex-1 bg-rose-600/20 text-rose-400 hover:bg-rose-600/30 px-3 py-2 rounded flex items-center justify-center gap-2 transition-colors border border-rose-500/20">
                <XOctagon className="w-4 h-4" /> Tamper Output
              </button>
              <button onClick={handleReplay} className="flex-1 bg-amber-600/20 text-amber-400 hover:bg-amber-600/30 px-3 py-2 rounded flex items-center justify-center gap-2 transition-colors border border-amber-500/20">
                <RefreshCw className="w-4 h-4" /> Replay Record
              </button>
            </div>
          </div>

          {verification && (
            <div className={`border rounded-xl p-5 shadow-xl transition-all duration-300 ${
              verification.status === 'VALID' ? 'bg-emerald-900/20 border-emerald-500/50' :
              verification.status === 'TAMPERING DETECTED' ? 'bg-rose-900/20 border-rose-500/50' :
              'bg-amber-900/20 border-amber-500/50'
            }`}>
              <h3 className="text-lg font-bold mb-4 border-b border-current pb-2 flex items-center gap-2">
                {verification.status === 'VALID' ? <ShieldCheck className="text-emerald-500 w-6 h-6" /> :
                 verification.status === 'TAMPERING DETECTED' ? <ShieldAlert className="text-rose-500 w-6 h-6" /> :
                 <AlertTriangle className="text-amber-500 w-6 h-6" />}
                Verification: {verification.status}
              </h3>
              
              <div className="grid grid-cols-2 gap-4 text-sm mb-4 font-mono">
                {Object.entries(verification.checks).map(([check, status]) => (
                  <div key={check} className="flex justify-between bg-slate-900/50 p-2.5 rounded border border-slate-700/50">
                    <span className="capitalize text-slate-300">{check.replace('_', ' ')}</span>
                    <span className={`font-bold ${status === 'PASS' ? 'text-emerald-400' : 'text-rose-400'}`}>{status}</span>
                  </div>
                ))}
              </div>

              {verification.evidence && verification.evidence.length > 0 && (
                <div className="mt-4 bg-slate-900/80 border border-slate-700 p-4 rounded-lg text-sm">
                  <div className="font-bold mb-2 text-rose-300 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> Evidence / Findings
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    {verification.evidence.map((item, idx) => (
                      <li key={idx} className="leading-relaxed">{item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
