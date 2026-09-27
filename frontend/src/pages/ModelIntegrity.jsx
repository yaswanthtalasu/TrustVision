import React, { useState } from 'react';
import { Upload, FileKey, Shield, AlertTriangle, CheckCircle, Download, ExternalLink, Activity, Cpu, BarChart } from 'lucide-react';

export default function ModelIntegrity() {
  // Check 1 States
  const [modelFile, setModelFile] = useState(null);
  const [hashFile, setHashFile] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Check 2 States
  const [behavioralModelFile, setBehavioralModelFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [behavioralResult, setBehavioralResult] = useState(null);
  const [behavioralError, setBehavioralError] = useState(null);

  const handleBehavioralVerify = async () => {
    if (!behavioralModelFile) {
      setBehavioralError("Please select the model artifact to analyze.");
      return;
    }
    setBehavioralError(null);
    setIsAnalyzing(true);
    setBehavioralResult(null);

    const formData = new FormData();
    formData.append('model_file', behavioralModelFile);

    try {
      const response = await fetch('http://localhost:8000/api/model-integrity/behavioral-analysis', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        setBehavioralError(data.detail || "An error occurred during behavioral analysis.");
      } else {
        setBehavioralResult(data);
      }
    } catch (err) {
      setBehavioralError("Failed to connect to the backend server.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleVerify = async () => {
    if (!modelFile || !hashFile) {
      setError("Please upload both the model artifact and the SHA-256 hash file.");
      return;
    }
    setError(null);
    setIsVerifying(true);
    setResult(null);

    const formData = new FormData();
    formData.append('model_file', modelFile);
    formData.append('hash_file', hashFile);

    try {
      const response = await fetch('http://localhost:8000/api/model-integrity/verify', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (data.status === 'INVALID_INPUT') {
            setError("Invalid input: The hash file may be malformed or empty.");
        } else {
            setError(data.detail || "An error occurred during verification.");
        }
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Failed to connect to the backend server. Make sure it is running.");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex items-start space-x-4 shadow-lg">
        <div className="p-3 bg-purple-500/20 text-purple-400 rounded-lg">
          <Shield className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Model Integrity (Scenario 1)</h1>
          <p className="text-slate-400">
            Verify externally supplied model artifacts using cryptographic integrity evidence. 
            This checks if the received artifact matches the Company-provided SHA-256 fingerprint.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-blue-400" />
            1. Model Artifact
          </h3>
          <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center bg-slate-900/50 hover:bg-slate-800/80 transition-colors">
            <input 
              type="file" 
              className="hidden" 
              id="modelUpload"
              onChange={(e) => setModelFile(e.target.files[0])}
            />
            <label htmlFor="modelUpload" className="cursor-pointer flex flex-col items-center">
              <div className="w-12 h-12 bg-blue-500/10 text-blue-400 rounded-full flex items-center justify-center mb-4">
                <Upload className="w-6 h-6" />
              </div>
              <span className="text-slate-300 font-medium mb-1">
                {modelFile ? modelFile.name : "Drop model file here"}
              </span>
              <span className="text-slate-500 text-sm">
                {modelFile ? `${(modelFile.size / 1024 / 1024).toFixed(2)} MB` : "Supported: .pth / .pt / .onnx"}
              </span>
              {!modelFile && (
                <span className="mt-4 px-4 py-2 bg-slate-700 text-sm text-white rounded hover:bg-slate-600 transition">
                  Browse Files
                </span>
              )}
            </label>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
          <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <FileKey className="w-5 h-5 text-purple-400" />
            2. Company SHA-256
          </h3>
          <div className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center bg-slate-900/50 hover:bg-slate-800/80 transition-colors">
            <input 
              type="file" 
              className="hidden" 
              id="hashUpload"
              accept=".txt,.sha256"
              onChange={(e) => setHashFile(e.target.files[0])}
            />
            <label htmlFor="hashUpload" className="cursor-pointer flex flex-col items-center">
              <div className="w-12 h-12 bg-purple-500/10 text-purple-400 rounded-full flex items-center justify-center mb-4">
                <FileKey className="w-6 h-6" />
              </div>
              <span className="text-slate-300 font-medium mb-1">
                {hashFile ? hashFile.name : "Drop .sha256 file here"}
              </span>
              <span className="text-slate-500 text-sm">
                {hashFile ? `${(hashFile.size / 1024).toFixed(2)} KB` : "Supported: .sha256 / .txt"}
              </span>
              {!hashFile && (
                <span className="mt-4 px-4 py-2 bg-slate-700 text-sm text-white rounded hover:bg-slate-600 transition">
                  Browse Files
                </span>
              )}
            </label>
          </div>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center py-4">
        {error && (
          <div className="mb-4 w-full p-4 bg-red-900/30 border border-red-500/50 text-red-300 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <p>{error}</p>
          </div>
        )}
        <button 
          onClick={handleVerify}
          disabled={isVerifying || !modelFile || !hashFile}
          className={`px-8 py-3 rounded-lg font-bold text-lg shadow-lg transition-all flex items-center gap-2 ${
            isVerifying || !modelFile || !hashFile
              ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/20'
          }`}
        >
          {isVerifying ? (
            <>
              <div className="animate-spin w-5 h-5 border-2 border-white/20 border-t-white rounded-full"></div>
              Verifying model artifact...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              VERIFY MODEL INTEGRITY
            </>
          )}
        </button>
      </div>

      {result && (
        <div className="space-y-6 animate-fadeIn">
          <div className={`p-6 rounded-xl border flex items-center justify-between shadow-lg ${
            result.match ? 'bg-green-900/20 border-green-500/50' : 'bg-orange-900/20 border-orange-500/50'
          }`}>
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${
                result.match ? 'bg-green-500/20 text-green-400' : 'bg-orange-500/20 text-orange-400'
              }`}>
                {result.match ? <CheckCircle className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
              </div>
              <div>
                <h2 className={`text-2xl font-bold ${result.match ? 'text-green-400' : 'text-orange-400'}`}>
                  STATUS: {result.status}
                </h2>
                <p className="text-slate-300 font-medium">
                  {result.match ? "✓ Hash Match — Integrity Verified" : "! Hash Mismatch — Further Review Required"}
                </p>
              </div>
            </div>
            
            <div className="text-right text-sm text-slate-400">
              <p>Algorithm: {result.hash_algorithm}</p>
              <p>Model: {result.model_filename}</p>
              <p>ID: {result.verification_id}</p>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
            <h3 className="text-lg font-semibold text-slate-200 mb-4">Cryptographic Evidence</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm text-slate-400 font-medium mb-1">Company-provided SHA-256</p>
                <div className="bg-slate-900 p-3 rounded border border-slate-700 font-mono text-slate-300 break-all select-all">
                  {result.claimed_hash}
                </div>
              </div>
              
              <div>
                <p className="text-sm text-slate-400 font-medium mb-1">TrustVision-computed SHA-256</p>
                <div className={`p-3 rounded border font-mono break-all select-all ${
                  result.match ? 'bg-green-900/30 border-green-500/30 text-green-300' : 'bg-red-900/30 border-red-500/30 text-red-300'
                }`}>
                  {result.computed_hash}
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex flex-wrap gap-4">
              <a 
                href={`http://localhost:8000/api/model-integrity/report/${result.verification_id}`}
                target="_blank" rel="noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
              >
                <Download className="w-4 h-4" /> Download JSON
              </a>
              <a 
                href={`http://localhost:8000/api/model-integrity/report/${result.verification_id}/html`}
                target="_blank" rel="noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
              >
                <ExternalLink className="w-4 h-4" /> Open HTML Report
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Check 2: Behavioral Integrity */}
      <div className="mt-12 pt-12 border-t border-slate-700 space-y-6 animate-fadeIn">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 flex items-start space-x-4 shadow-lg">
          <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-lg">
            <Activity className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">Behavioral Integrity (Check 2)</h1>
            <p className="text-slate-400">
              Verify if the submitted model behaves consistently with the trusted behavioral reference under controlled normal and trigger tests.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
            <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              Reference Model
            </h3>
            <div className="bg-slate-900/50 rounded-lg p-6 border border-slate-700">
              <p className="text-sm text-slate-400 mb-2">Loaded from secure offline storage:</p>
              <ul className="text-slate-300 space-y-2 text-sm font-medium">
                <li><span className="text-slate-500">Name:</span> Trusted Reference ResNet-18</li>
                <li><span className="text-slate-500">Task:</span> CIFAR-10 classification</li>
                <li><span className="text-slate-500">Framework:</span> PyTorch (Local Inference)</li>
              </ul>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
            <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-400" />
              Submitted Company Model
            </h3>
            <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center bg-slate-900/50 hover:bg-slate-800/80 transition-colors h-full flex flex-col justify-center">
              <input 
                type="file" 
                className="hidden" 
                id="behavioralModelUpload"
                onChange={(e) => setBehavioralModelFile(e.target.files[0])}
              />
              <label htmlFor="behavioralModelUpload" className="cursor-pointer flex flex-col items-center">
                <span className="text-slate-300 font-medium mb-1">
                  {behavioralModelFile ? behavioralModelFile.name : "Select model for behavioral analysis"}
                </span>
                {!behavioralModelFile && (
                  <span className="mt-2 px-4 py-2 bg-slate-700 text-sm text-white rounded hover:bg-slate-600 transition">
                    Browse Files
                  </span>
                )}
              </label>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center py-4">
          {behavioralError && (
            <div className="mb-4 w-full p-4 bg-red-900/30 border border-red-500/50 text-red-300 rounded-lg flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <p>{behavioralError}</p>
            </div>
          )}
          <button 
            onClick={handleBehavioralVerify}
            disabled={isAnalyzing || !behavioralModelFile}
            className={`px-8 py-3 rounded-lg font-bold text-lg shadow-lg transition-all flex items-center gap-2 ${
              isAnalyzing || !behavioralModelFile
                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
            }`}
          >
            {isAnalyzing ? (
              <>
                <div className="animate-spin w-5 h-5 border-2 border-white/20 border-t-white rounded-full"></div>
                Running local behavioral inference...
              </>
            ) : (
              <>
                <Activity className="w-5 h-5" />
                RUN BEHAVIORAL ANALYSIS
              </>
            )}
          </button>
        </div>

        {behavioralResult && (
          <div className="space-y-6 animate-fadeIn">
            <div className={`p-6 rounded-xl border flex items-center justify-between shadow-lg ${
              behavioralResult.status === 'PASS' ? 'bg-green-900/20 border-green-500/50' : 'bg-orange-900/20 border-orange-500/50'
            }`}>
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${
                  behavioralResult.status === 'PASS' ? 'bg-green-500/20 text-green-400' : 'bg-orange-500/20 text-orange-400'
                }`}>
                  {behavioralResult.status === 'PASS' ? <CheckCircle className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
                </div>
                <div>
                  <h2 className={`text-2xl font-bold ${behavioralResult.status === 'PASS' ? 'text-green-400' : 'text-orange-400'}`}>
                    STATUS: {behavioralResult.status}
                  </h2>
                  <p className="text-slate-300 font-medium">
                    {behavioralResult.status === 'PASS' 
                      ? "✓ Behavioral consistency within acceptable bounds" 
                      : "! Behavioral deviation detected — Further Review Required"}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <BarChart className="w-5 h-5 text-blue-400" />
                  Normal Test Set ({behavioralResult.normal_test.samples} samples)
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-slate-700 pb-2">
                    <span className="text-slate-400">Prediction Agreement</span>
                    <span className="text-slate-200 font-bold">{(behavioralResult.normal_test.agreement * 100).toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-slate-700 pb-2">
                    <span className="text-slate-400">Prediction Disagreement</span>
                    <span className="text-slate-200">{(behavioralResult.normal_test.disagreement * 100).toFixed(2)}%</span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-slate-400">Mean Confidence Delta</span>
                    <span className="text-slate-200">{behavioralResult.normal_test.mean_confidence_difference}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
                <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                  Trigger Test Set ({behavioralResult.trigger_test.samples} samples)
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-slate-700 pb-2">
                    <span className="text-slate-400">Behavioral Deviations</span>
                    <span className="text-slate-200 font-bold">{Math.round(behavioralResult.trigger_test.deviation_rate * behavioralResult.trigger_test.samples)}</span>
                  </div>
                  <div className="flex justify-between pb-2">
                    <span className="text-slate-400">Deviation Rate</span>
                    <span className={`font-bold ${behavioralResult.trigger_test.deviation_rate >= 0.20 ? 'text-red-400' : 'text-green-400'}`}>
                      {(behavioralResult.trigger_test.deviation_rate * 100).toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md">
               <h3 className="text-lg font-semibold text-slate-200 mb-4">Forensic Evidence & Reports</h3>
               <ul className="list-disc pl-5 space-y-1 text-slate-300 text-sm mb-6">
                 {behavioralResult.evidence.map((ev, i) => <li key={i}>{ev}</li>)}
               </ul>
               <div className="flex flex-wrap gap-4">
                <a 
                  href={`http://localhost:8000/api/model-integrity/report/${behavioralResult.analysis_id}`}
                  target="_blank" rel="noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
                >
                  <Download className="w-4 h-4" /> Download JSON
                </a>
                <a 
                  href={`http://localhost:8000/api/model-integrity/report/${behavioralResult.analysis_id}/html`}
                  target="_blank" rel="noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
                >
                  <ExternalLink className="w-4 h-4" /> Open HTML Report
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
