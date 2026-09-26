import React, { useState } from 'react';
import { Database, Download, RefreshCw, CheckCircle2, AlertCircle, HardDrive, UploadCloud, Trash2 } from 'lucide-react';

export default function DataIntake({ setActiveTab }) {
  const [downloading, setDownloading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [seed, setSeed] = useState(42);
  const [samplesPerContrib, setSamplesPerContrib] = useState(2000);
  const [uploading, setUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadContributorId, setUploadContributorId] = useState('CUSTOM_1');
  const [uploadDescription, setUploadDescription] = useState('Manual Upload');
  const [log, setLog] = useState([]);

  const addLog = (msg, type = 'info') => {
    setLog(prev => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  const handleDownload = async () => {
    setDownloading(true);
    addLog("Initiating official CIFAR-10 dataset download & clean reference extraction...");
    try {
      const res = await fetch('/api/datasets/download', { method: 'POST' });
      const json = await res.json();
      if (res.ok) {
        addLog(`SUCCESS: ${json.message}`, 'success');
      } else {
        addLog(`ERROR: ${json.detail}`, 'error');
      }
    } catch (err) {
      addLog(`FAILED: ${err.message}`, 'error');
    } finally {
      setDownloading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    addLog(`Generating simulated contributor datasets C1, C2, C3 (risky), C4 with seed=${seed}...`);
    try {
      const res = await fetch(`/api/contributors/generate?seed=${seed}&samples_per_contributor=${samplesPerContrib}`, { method: 'POST' });
      const json = await res.json();
      if (res.ok) {
        addLog(`SUCCESS: ${json.message}`, 'success');
        addLog(`Cryptographic root hash C1: ${json.crypto_root_hashes.C1?.slice(0, 16)}...`, 'info');
        addLog(`Cryptographic root hash C3: ${json.crypto_root_hashes.C3?.slice(0, 16)}...`, 'info');
      } else {
        addLog(`ERROR: ${json.detail}`, 'error');
      }
    } catch (err) {
      addLog(`FAILED: ${err.message}`, 'error');
    } finally {
      setGenerating(false);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) {
      addLog("ERROR: Please select a ZIP file to upload first.", 'error');
      return;
    }
    setUploading(true);
    addLog(`Uploading manual contributor ${uploadContributorId}...`);
    
    const formData = new FormData();
    formData.append('contributor_id', uploadContributorId);
    formData.append('description', uploadDescription);
    formData.append('file', uploadFile);

    try {
      const res = await fetch('/api/contributors/upload', {
        method: 'POST',
        body: formData,
      });
      const json = await res.json();
      if (res.ok) {
        addLog(`SUCCESS: ${json.message}`, 'success');
        addLog(`Cryptographic root hash ${uploadContributorId}: ${json.crypto_root_hash?.slice(0, 16)}...`, 'info');
      } else {
        addLog(`ERROR: ${json.detail}`, 'error');
      }
    } catch (err) {
      addLog(`FAILED: ${err.message}`, 'error');
    } finally {
      setUploading(false);
      setUploadFile(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50">
        <h1 className="text-2xl font-bold text-white tracking-tight">Data Intake & Contributor Simulation</h1>
        <p className="text-slate-400 text-sm mt-1">Download clean CIFAR-10 baseline dataset and generate deterministic contributor dataset submissions ($C_1, C_2, C_3, C_4$).</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1 Card */}
        <div className="bg-slate-800/60 border border-slate-700/80 p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">1. CIFAR-10 Reference Dataset</h2>
              <p className="text-xs text-slate-400">Download official 50,000 RGB 32x32 dataset for clean baseline reference.</p>
            </div>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl text-xs space-y-2 text-slate-300 font-mono">
            <div>Baseline: 50,000 training images</div>
            <div>Classes: 10 (airplane, auto, bird, cat, deer, dog, frog, horse, ship, truck)</div>
            <div>Storage Location: data/reference/cifar10/</div>
          </div>

          <button
            onClick={handleDownload}
            disabled={downloading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all shadow-lg shadow-blue-600/20 flex items-center justify-center gap-2"
          >
            {downloading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <HardDrive className="w-4 h-4" />}
            {downloading ? 'Downloading Dataset...' : 'Download / Verify Reference Dataset'}
          </button>
        </div>

        {/* Step 2 Card */}
        <div className="bg-slate-800/60 border border-slate-700/80 p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">2. Generate Contributors (C1–C4)</h2>
              <p className="text-xs text-slate-400">Synthesize $C_1, C_2, C_4$ (Clean) and $C_3$ (Controlled Manipulations).</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Random Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">Samples Per Contributor</label>
              <input
                type="number"
                value={samplesPerContrib}
                onChange={(e) => setSamplesPerContrib(Number(e.target.value))}
                className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full py-3 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all shadow-lg shadow-purple-600/20 flex items-center justify-center gap-2"
          >
            {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            {generating ? 'Generating Contributors...' : 'Generate Contributor Datasets'}
          </button>
        </div>

        {/* Step 3 Card */}
        <div className="bg-slate-800/60 border border-slate-700/80 p-6 rounded-2xl space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">3. Manual Dataset Upload</h2>
              <p className="text-xs text-slate-400">Upload a custom contributor dataset ZIP.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-400">Contributor ID</label>
              <input
                type="text"
                value={uploadContributorId}
                onChange={(e) => setUploadContributorId(e.target.value)}
                className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-400">Dataset ZIP</label>
              <input
                type="file"
                accept=".zip"
                onChange={(e) => setUploadFile(e.target.files[0])}
                className="w-full mt-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-500/20 file:text-emerald-400 hover:file:bg-emerald-500/30 transition-all cursor-pointer"
              />
            </div>
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading || !uploadFile}
            className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl transition-all shadow-lg shadow-emerald-600/20 flex items-center justify-center gap-2 mt-2"
          >
            {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
            {uploading ? 'Uploading...' : 'Upload Contributor Dataset'}
          </button>
        </div>
      </div>

      {/* Execution Console */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl font-mono text-xs space-y-2">
        <div className="flex justify-between items-center text-slate-400 pb-2 border-b border-slate-800">
          <span className="font-semibold uppercase tracking-wider">Execution Console Log</span>
          <span>Offline Ready</span>
        </div>
        <div className="h-44 overflow-y-auto space-y-1.5 pt-2">
          {log.length === 0 ? (
            <div className="text-slate-600 italic">No events logged yet. Click an action above to execute.</div>
          ) : (
            log.map((item, idx) => (
              <div key={idx} className={`flex items-start gap-2 ${
                item.type === 'success' ? 'text-emerald-400' : item.type === 'error' ? 'text-rose-400' : 'text-slate-300'
              }`}>
                <span className="text-slate-500">[{item.time}]</span>
                <span>{item.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
