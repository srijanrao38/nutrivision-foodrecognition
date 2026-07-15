// src/pages/MedicalUpload.tsx
import React, { useState, useEffect } from 'react';
import { FileText, Upload, AlertCircle, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import api from '../api';

const MedicalUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get('/api/medical/history/');
      setHistory(response.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (selected.size > 5 * 1024 * 1024) {
        setError('File exceeds the 5MB size limit.');
        return;
      }
      setFile(selected);
      setError('');
      setResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a PDF or image file first.');
      return;
    }

    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post('/api/medical/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data.report);
      fetchHistory();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to extract biomarkers. Ensure the document is readable.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (name: string, value: number) => {
    if (!value) return 'text-slate-400';
    
    // Normal ranges
    const thresholds: { [key: string]: { min?: number, max?: number } } = {
      blood_sugar: { max: 100 },
      hba1c: { max: 5.7 },
      cholesterol: { max: 200 },
      ldl: { max: 100 },
      hdl: { min: 40 },
      vitamin_d: { min: 30 },
      vitamin_b12: { min: 200 },
      iron: { min: 50, max: 170 },
      hemoglobin: { min: 12.0, max: 17.5 },
      bmi: { min: 18.5, max: 24.9 }
    };

    const range = thresholds[name];
    if (!range) return 'text-slate-800';

    if (range.max !== undefined && value > range.max) return 'text-red-600 bg-red-50 border-red-200';
    if (range.min !== undefined && value < range.min) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-emerald-600 bg-emerald-50 border-emerald-200';
  };

  const biomarkerLabels: { [key: string]: { label: string, unit: string, ref: string } } = {
    blood_sugar: { label: 'Fasting Blood Sugar', unit: 'mg/dL', ref: '< 100' },
    hba1c: { label: 'HbA1c (Glycated Hemoglobin)', unit: '%', ref: '< 5.7%' },
    cholesterol: { label: 'Total Cholesterol', unit: 'mg/dL', ref: '< 200' },
    ldl: { label: 'LDL (Bad Cholesterol)', unit: 'mg/dL', ref: '< 100' },
    hdl: { label: 'HDL (Good Cholesterol)', unit: 'mg/dL', ref: '> 40 (M) / > 50 (F)' },
    vitamin_d: { label: 'Vitamin D (25-Hydroxy)', unit: 'ng/mL', ref: '> 30' },
    vitamin_b12: { label: 'Vitamin B12', unit: 'pg/mL', ref: '> 200' },
    iron: { label: 'Serum Iron', unit: 'µg/dL', ref: '50 - 170' },
    hemoglobin: { label: 'Hemoglobin', unit: 'g/dL', ref: '12.0 - 17.5' },
    bmi: { label: 'BMI (Body Mass Index)', unit: 'kg/m²', ref: '18.5 - 24.9' },
    weight: { label: 'Weight', unit: 'kg', ref: 'N/A' },
    height: { label: 'Height', unit: 'cm', ref: 'N/A' },
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Disclaimer banner */}
      <p className="text-[10px] text-slate-400 text-center mb-4">
        NutriVision AI is an educational fitness planner, not a medical platform. In case of illness, consult a doctor.
      </p>

      <div className="flex items-center space-x-3 border-b pb-4 mb-6">
        <FileText className="h-7 w-7 text-emerald-600" />
        <h1 className="text-2xl font-bold text-slate-800">Laboratory Medical Reports</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Upload zone & History list */}
        <div className="space-y-6 lg:col-span-1">
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Upload Labs (PDF / Image)</h3>
            
            {error && (
              <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded flex items-start space-x-2 text-red-800 text-sm">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="relative border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-6 flex flex-col items-center justify-center bg-slate-50 transition cursor-pointer">
              <input
                type="file"
                accept=".pdf, image/*"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              <Upload className="h-10 w-10 text-slate-400 mb-2" />
              {file ? (
                <span className="text-sm font-semibold text-emerald-600 text-center break-all">{file.name}</span>
              ) : (
                <>
                  <span className="text-xs font-semibold text-slate-600 text-center">Select laboratory report file</span>
                  <span className="text-[10px] text-slate-400 mt-1">PDF, JPG, PNG (Max 5MB)</span>
                </>
              )}
            </div>

            {file && (
              <div className="mt-4 flex space-x-2">
                <button
                  onClick={handleUpload}
                  disabled={loading}
                  className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold text-sm rounded-lg shadow transition"
                >
                  {loading ? 'Processing OCR & AI...' : 'Scan Lab Report'}
                </button>
                <button
                  onClick={() => setFile(null)}
                  className="px-3 py-2.5 border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold text-sm rounded-lg transition"
                >
                  Clear
                </button>
              </div>
            )}
          </div>

          {/* Past Reports List */}
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center">
              <Clock className="h-4 w-4 mr-1 text-slate-400" /> Historical Reports
            </h3>
            
            {history.length > 0 ? (
              <div className="space-y-3">
                {history.map((h, i) => (
                  <div
                    key={h.id || i}
                    onClick={() => setResult(h)}
                    className="p-3 bg-slate-50 hover:bg-emerald-50 border rounded-xl cursor-pointer transition flex items-center justify-between"
                  >
                    <div>
                      <p className="text-xs font-semibold text-slate-700">Lab Scanned</p>
                      <p className="text-[10px] text-slate-400">{new Date(h.uploaded_at).toLocaleString()}</p>
                    </div>
                    <span className="bg-slate-200 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      View
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 py-4 text-center">No reports scanned yet.</p>
            )}
          </div>
        </div>

        {/* Right Col: Biomarkers extraction display */}
        <div className="lg:col-span-2 space-y-6">
          {loading && (
            <div className="glass-panel p-8 rounded-2xl border flex flex-col items-center justify-center min-h-[350px]">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
              <p className="text-slate-700 font-bold">Processing Document OCR & Parser...</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm text-center">Reading laboratory parameters, conducting regex validations, and applying safety overrides...</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Summary and Fallback text */}
              <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
                <h3 className="text-lg font-bold text-slate-800 mb-3">AI Medical Report Interpretation</h3>
                <p className="text-sm text-slate-650 leading-relaxed bg-slate-50 p-4 rounded-xl border">
                  {result.summary || "Biomarkers parsed successfully. Reference metrics computed relative to standard values below."}
                </p>
              </div>

              {/* Biomarker Grid */}
              <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
                <h3 className="text-lg font-bold text-slate-800 mb-4">Scanned Laboratory Variables</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(biomarkerLabels).map(([key, details]) => {
                    const val = result[key];
                    if (val === null || val === undefined) return null;
                    
                    const statusClass = getStatusColor(key, val);
                    const isHealthy = statusClass.includes('emerald');
                    const isWarning = statusClass.includes('red') || statusClass.includes('amber');
                    
                    return (
                      <div key={key} className="flex items-center justify-between p-3 border rounded-xl bg-slate-50/50 hover:bg-slate-50 transition">
                        <div>
                          <p className="text-xs font-semibold text-slate-500">{details.label}</p>
                          <p className="text-sm font-extrabold text-slate-800 mt-0.5">
                            {val} <span className="text-xs font-normal text-slate-400">{details.unit}</span>
                          </p>
                        </div>
                        
                        <div className="text-right">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border inline-block ${statusClass}`}>
                            {isHealthy ? 'Normal' : isWarning ? 'Check Value' : 'Recorded'}
                          </span>
                          <p className="text-[10px] text-slate-400 mt-1">Ref: {details.ref}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {!loading && !result && (
            <div className="glass-panel p-8 rounded-2xl border flex flex-col items-center justify-center min-h-[350px] text-slate-400">
              <FileText className="h-16 w-16 mb-4 stroke-1" />
              <p className="font-semibold">No active report loaded.</p>
              <p className="text-xs text-center mt-1 max-w-sm">Please select and run a laboratory scan on the left, or select a report from the historical logs list.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default MedicalUpload;
