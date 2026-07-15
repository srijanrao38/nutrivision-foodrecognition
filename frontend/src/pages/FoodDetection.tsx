// src/pages/FoodDetection.tsx
import React, { useState } from 'react';
import { Camera, Upload, AlertCircle, Sparkles, CheckCircle2, AlertTriangle, Lightbulb } from 'lucide-react';
import api from '../api';

const FoodDetection: React.FC = () => {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image file exceeds the 5MB limit.');
        return;
      }
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!image) {
      setError('Please select an image first.');
      return;
    }

    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('image', image);

    try {
      const response = await api.post('/api/food/detect/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to detect food items. Please check if the image has foods.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Educational disclaimer */}
      <p className="text-[10px] text-slate-400 text-center mb-4">
        NutriVision AI is an educational fitness planner, not a medical platform. In case of illness, consult a doctor.
      </p>

      <div className="flex items-center space-x-3 border-b pb-4 mb-6">
        <Camera className="h-7 w-7 text-emerald-600" />
        <h1 className="text-2xl font-bold text-slate-800">Meal & Food Image Detection</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Image Upload & Preview */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-800 mb-4">Upload Food Image</h3>
            
            {error && (
              <div className="mb-4 bg-red-50 border-l-4 border-red-500 p-4 rounded flex items-start space-x-2 text-red-800 text-sm">
                <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="relative border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-8 flex flex-col items-center justify-center bg-slate-50 transition cursor-pointer">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="absolute inset-0 opacity-0 cursor-pointer"
              />
              {preview ? (
                <img src={preview} alt="Food Preview" className="max-h-64 rounded-lg object-contain" />
              ) : (
                <>
                  <Upload className="h-12 w-12 text-slate-400 mb-3" />
                  <span className="text-sm font-semibold text-slate-600">Drag & drop or click to upload</span>
                  <span className="text-xs text-slate-400 mt-1">JPEG, PNG, WEBP (Max 5MB)</span>
                </>
              )}
            </div>

            {preview && (
              <div className="mt-6 flex space-x-4">
                <button
                  onClick={handleUpload}
                  disabled={loading}
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-semibold rounded-lg shadow-md transition"
                >
                  {loading ? 'Analyzing Food Image...' : 'Run YOLOv8 Food Scan'}
                </button>
                <button
                  onClick={() => {
                    setImage(null);
                    setPreview(null);
                    setResult(null);
                    setError('');
                  }}
                  className="px-4 py-3 border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold rounded-lg transition"
                >
                  Reset
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right: Results & Health Score */}
        <div className="space-y-6">
          {loading && (
            <div className="glass-panel p-8 rounded-2xl border flex flex-col items-center justify-center min-h-[300px]">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mb-4"></div>
              <p className="text-slate-600 font-semibold">Running YOLOv8 Food Recognition...</p>
              <p className="text-xs text-slate-400 mt-1 text-center">Identifying ingredients, matching USDA database, and computing health score...</p>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Detection Summary & Macronutrients */}
              <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
                <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
                  <Sparkles className="h-5 w-5 text-emerald-600 mr-2" /> Nutrient Content Breakdown
                </h3>

                {/* Detected ingredients */}
                <div className="mb-6">
                  <p className="text-xs font-semibold text-slate-400 uppercase mb-2">Detected Ingredients</p>
                  <div className="flex flex-wrap gap-2">
                    {result.items.map((item: any, idx: number) => (
                      <span key={idx} className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full capitalize">
                        {item.quantity}x {item.name}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Macros totals */}
                <div className="grid grid-cols-4 gap-4 text-center">
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span className="block text-xs font-semibold text-slate-500">Calories</span>
                    <span className="text-lg font-bold text-slate-800">{Math.round(result.totals.calories)} kcal</span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span className="block text-xs font-semibold text-slate-500">Protein</span>
                    <span className="text-lg font-bold text-slate-800">{Math.round(result.totals.protein_g)}g</span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span className="block text-xs font-semibold text-slate-500">Carbs</span>
                    <span className="text-lg font-bold text-slate-800">{Math.round(result.totals.carbs_g)}g</span>
                  </div>
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                    <span className="block text-xs font-semibold text-slate-500">Fat</span>
                    <span className="text-lg font-bold text-slate-800">{Math.round(result.totals.fat_g)}g</span>
                  </div>
                </div>
              </div>

              {/* Meal Health Score Section */}
              <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-slate-800">Meal Health Score</h3>
                  <span className={`text-2xl font-black px-3 py-1 rounded-xl ${
                    result.health_score.score >= 80 ? 'bg-emerald-100 text-emerald-800' :
                    result.health_score.score >= 50 ? 'bg-amber-100 text-amber-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {result.health_score.score}/100
                  </span>
                </div>

                {/* Score bar */}
                <div className="w-full bg-slate-100 rounded-full h-4 mb-6">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${
                      result.health_score.score >= 80 ? 'bg-emerald-500' :
                      result.health_score.score >= 50 ? 'bg-amber-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${result.health_score.score}%` }}
                  ></div>
                </div>

                {/* Strengths & Concerns */}
                <div className="space-y-4 text-sm">
                  {result.health_score.strengths?.length > 0 && (
                    <div>
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wide flex items-center mb-1.5">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 mr-1" /> Key Nutritional Strengths
                      </span>
                      <ul className="list-disc pl-5 text-slate-700 space-y-1">
                        {result.health_score.strengths.map((str: string, i: number) => (
                          <li key={i}>{str}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.health_score.concerns?.length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                      <span className="text-xs font-bold text-slate-400 uppercase tracking-wide flex items-center mb-1.5">
                        <AlertTriangle className="h-4 w-4 text-amber-500 mr-1" /> Potential Dietary Concerns
                      </span>
                      <ul className="list-disc pl-5 text-slate-700 space-y-1">
                        {result.health_score.concerns.map((con: string, i: number) => (
                          <li key={i} className="text-amber-900">{con}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.health_score.alternatives?.length > 0 && (
                    <div className="pt-2 border-t border-slate-100 bg-emerald-50/50 p-3 rounded-lg">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wide flex items-center mb-1.5">
                        <Lightbulb className="h-4 w-4 text-emerald-600 mr-1 animate-pulse" /> Suggested Healthier Alternatives
                      </span>
                      <ul className="list-disc pl-5 text-slate-800 space-y-1">
                        {result.health_score.alternatives.map((alt: string, i: number) => (
                          <li key={i}>{alt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {!preview && !result && (
            <div className="glass-panel p-8 rounded-2xl border flex flex-col items-center justify-center min-h-[300px] text-slate-400">
              <Camera className="h-16 w-16 mb-4 stroke-1" />
              <p className="font-medium">No active scan yet.</p>
              <p className="text-xs text-center mt-1">Upload a meal image on the left, then click 'Run YOLOv8 Food Scan' to view diagnostics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FoodDetection;
