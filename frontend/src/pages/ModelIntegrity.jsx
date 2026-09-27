import React, { useState } from 'react';
import { Upload, FileKey, Shield, AlertTriangle, CheckCircle, Download, ExternalLink, Activity, Cpu, BarChart } from 'lucide-react';

export default function ModelIntegrity() {
  const [modelFile, setModelFile] = useState(null);
  const [hashFile, setHashFile] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [fullResult, setFullResult] = useState(null);
  const [error, setError] = useState(null);

  const handleVerify = async () => {
    if (!modelFile || !hashFile) {
      setError("Please upload both the model artifact and the SHA-256 hash file.");
      return;
    }
    setError(null);
    setIsVerifying(true);
    setFullResult(null);

    const formData = new FormData();
    formData.append('model_file', modelFile);
    formData.append('hash_file', hashFile);

    try {
      const response = await fetch('http://localhost:8000/api/model-integrity/verify-full', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok) {
        if (data.status === 'INVALID_INPUT' || data.detail) {
            setError(data.detail || "Invalid input: The hash file may be malformed or empty.");
        } else {
            setError("An error occurred during verification.");
        }
      } else {
        setFullResult(data);
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
          <h1 className="text-2xl font-bold text-white mb-2">Model Integrity Assurance</h1>
          <p className="text-slate-400">
            Verify externally supplied model artifacts using cryptographic integrity evidence and assess their behavior against a trusted reference test suite.
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
                {modelFile ? `${(modelFile.size / 1024 / 1024).toFixed(2)} MB` : "Supported: .pth"}
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
              Verifying model...
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              RUN COMPREHENSIVE MODEL INTEGRITY CHECK
            </>
          )}
        </button>
      </div>

      {fullResult && (
        <div className="space-y-6 animate-fadeIn">
          {/* OVERALL DISPOSITION */}
          <div className={`p-6 rounded-xl border flex items-center justify-between shadow-lg ${
            fullResult.overall_disposition === 'ACCEPT' ? 'bg-green-900/20 border-green-500/50' : 
            fullResult.overall_disposition === 'REVIEW' ? 'bg-orange-900/20 border-orange-500/50' : 
            'bg-red-900/20 border-red-500/50'
          }`}>
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${
                fullResult.overall_disposition === 'ACCEPT' ? 'bg-green-500/20 text-green-400' : 
                fullResult.overall_disposition === 'REVIEW' ? 'bg-orange-500/20 text-orange-400' : 
                'bg-red-500/20 text-red-400'
              }`}>
                {fullResult.overall_disposition === 'ACCEPT' ? <CheckCircle className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
              </div>
              <div>
                <h2 className={`text-2xl font-bold ${
                  fullResult.overall_disposition === 'ACCEPT' ? 'text-green-400' : 
                  fullResult.overall_disposition === 'REVIEW' ? 'text-orange-400' : 
                  'text-red-400'
                }`}>
                  OVERALL: {fullResult.overall_disposition}
                </h2>
                <p className="text-slate-300 font-medium">
                  {fullResult.overall_disposition === 'ACCEPT' ? "Model artifact and behavior verified successfully." : 
                   fullResult.overall_disposition === 'REVIEW' ? "Deviations detected. Manual review required." :
                   "Model rejected or quarantined."}
                </p>
              </div>
            </div>
            <div className="text-right text-sm text-slate-400">
              <p>Model: {fullResult.model_filename}</p>
              <p>ID: {fullResult.verification_id}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* CHECK 1: Artifact Integrity */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-purple-400" />
                  CHECK 1: Artifact Integrity
                </h3>
                <span className={`px-3 py-1 rounded font-bold text-sm ${
                  fullResult.artifact.status === 'PASS' ? 'bg-green-900/30 text-green-400 border border-green-500/30' : 'bg-red-900/30 text-red-400 border border-red-500/30'
                }`}>
                  {fullResult.artifact.status}
                </span>
              </div>
              
              <div className="space-y-4 flex-1">
                <div>
                  <p className="text-sm text-slate-400 font-medium mb-1">Company-provided SHA-256</p>
                  <div className="bg-slate-900 p-3 rounded border border-slate-700 font-mono text-slate-300 text-xs break-all">
                    {fullResult.artifact.claimed_hash}
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-slate-400 font-medium mb-1">TrustVision-computed SHA-256</p>
                  <div className={`p-3 rounded border font-mono text-xs break-all ${
                    fullResult.artifact.match ? 'bg-green-900/20 border-green-500/30 text-green-300' : 'bg-red-900/20 border-red-500/30 text-red-300'
                  }`}>
                    {fullResult.artifact.computed_hash}
                  </div>
                </div>
              </div>
            </div>

            {/* CHECK 2: Behavioral Integrity */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 shadow-md flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-400" />
                  CHECK 2: Behavioral Integrity
                </h3>
                {fullResult.behavioral ? (
                  <span className={`px-3 py-1 rounded font-bold text-sm ${
                    fullResult.behavioral.status === 'PASS' ? 'bg-green-900/30 text-green-400 border border-green-500/30' : 'bg-orange-900/30 text-orange-400 border border-orange-500/30'
                  }`}>
                    {fullResult.behavioral.status}
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded font-bold text-sm bg-slate-700 text-slate-400 border border-slate-600">
                    SKIPPED / FAILED
                  </span>
                )}
              </div>
              
              <div className="flex-1">
                {fullResult.behavioral ? (
                  <div className="space-y-4 text-sm">
                    <p className="text-slate-400">Reference: <span className="text-slate-300">{fullResult.behavioral.reference_model}</span></p>
                    
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-900 p-3 rounded border border-slate-700">
                            <p className="text-slate-400 mb-1">Normal Test Agreement</p>
                            <p className="text-xl font-bold text-slate-200">
                                {(fullResult.behavioral.normal_test.agreement * 100).toFixed(1)}%
                            </p>
                        </div>
                        <div className="bg-slate-900 p-3 rounded border border-slate-700">
                            <p className="text-slate-400 mb-1">Trigger Deviation</p>
                            <p className={`text-xl font-bold ${fullResult.behavioral.trigger_test.deviation_rate >= 0.2 ? 'text-orange-400' : 'text-slate-200'}`}>
                                {(fullResult.behavioral.trigger_test.deviation_rate * 100).toFixed(1)}%
                            </p>
                        </div>
                    </div>
                    
                    <div className="mt-4">
                        <p className="text-slate-400 font-medium mb-1">Evidence Summary:</p>
                        <ul className="list-disc pl-5 text-slate-300 space-y-1">
                            {fullResult.behavioral.evidence.map((ev, i) => <li key={i}>{ev}</li>)}
                        </ul>
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500">
                    <p>Behavioral analysis was not completed successfully.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex justify-center gap-4 pt-4 border-t border-slate-700">
            <a 
              href={`http://localhost:8000/api/model-integrity/report/${fullResult.verification_id}`}
              target="_blank" rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
            >
              <Download className="w-4 h-4" /> Download JSON Report
            </a>
            <a 
              href={`http://localhost:8000/api/model-integrity/report/${fullResult.verification_id}/html`}
              target="_blank" rel="noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-slate-200 transition"
            >
              <ExternalLink className="w-4 h-4" /> Open Full HTML Report
            </a>
          </div>

        </div>
      )}
    </div>
  );
}
