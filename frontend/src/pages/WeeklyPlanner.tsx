// src/pages/WeeklyPlanner.tsx
import React, { useState, useEffect } from 'react';
import { Calendar, Sparkles, AlertTriangle, ArrowRight, Printer, CheckCircle, XCircle } from 'lucide-react';
import api from '../api';

const WeeklyPlanner: React.FC = () => {
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLatestPlan();
  }, []);

  const fetchLatestPlan = async () => {
    try {
      const response = await api.get('/api/recommendations/history/');
      if (response.data && response.data.length > 0) {
        setRecommendation(response.data[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setFetching(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/api/recommendations/generate/');
      setRecommendation(response.data);
    } catch (err: any) {
      setError('Failed to generate meal plan. Make sure profile details are filled out.');
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  const plan = recommendation?.plan_data;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 printable-area">
      {/* Educational disclaimer */}
      <p className="text-[10px] text-slate-400 text-center mb-4 non-printable">
        NutriVision AI is an educational fitness planner, not a medical platform. In case of illness, consult a doctor.
      </p>

      <div className="flex items-center justify-between border-b pb-4 mb-6 non-printable">
        <div className="flex items-center space-x-3">
          <Calendar className="h-7 w-7 text-emerald-600" />
          <h1 className="text-2xl font-bold text-slate-800">7-Day Weekly Meal Planner</h1>
        </div>
        
        {plan && (
          <button
            onClick={() => window.print()}
            className="flex items-center bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition shadow-md"
          >
            <Printer className="h-4 w-4 mr-2" /> Print Plan
          </button>
        )}
      </div>

      {!plan ? (
        <div className="glass-panel max-w-2xl mx-auto p-8 rounded-2xl border text-center shadow-lg">
          <Sparkles className="h-16 w-16 text-emerald-600 mx-auto mb-4 animate-pulse" />
          <h2 className="text-xl font-bold text-slate-800 mb-2">Build Your Personalized 7-Day Meal Plan</h2>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            NutriVision AI reads your physical biomarkers, dietary preferences, and any uploaded laboratory medical reports to draft a structured 7-day meal calendar complete with calorie targets and customized macronutrients.
          </p>
          
          {error && (
            <div className="mb-4 bg-red-50 text-red-700 p-3 rounded-lg text-xs border border-red-200">
              {error}
            </div>
          )}

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-3 px-8 rounded-xl shadow-md transition disabled:opacity-50"
          >
            {loading ? 'Assembling Recommendations...' : 'Generate Meal Plan'}
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          
          {/* Top Plan stats & details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Target macros cards */}
            <div className="lg:col-span-2 glass-panel p-6 rounded-2xl shadow border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
                <Sparkles className="h-5 w-5 text-emerald-600 mr-1.5" /> Target Daily Intake Metrics
              </h3>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Calories</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.calories} kcal</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Protein</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.protein_g}g</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Carbs</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.carbs_g}g</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Fat</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.fat_g}g</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Fiber</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.fiber_g}g</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-center">
                  <span className="block text-[10px] font-semibold text-slate-400 uppercase">Water</span>
                  <span className="text-base font-extrabold text-slate-800">{plan.targets?.water_l}L</span>
                </div>
              </div>
            </div>

            {/* Medical Adjustments alert */}
            <div className="p-6 rounded-2xl shadow border border-slate-800 bg-slate-900 text-white">
              <h3 className="text-base font-bold text-white mb-3 flex items-center">
                <AlertTriangle className="h-5 w-5 text-amber-400 mr-2" /> Medical Customizations
              </h3>
              {plan.medical_adjustments?.length > 0 ? (
                <ul className="text-xs space-y-2 text-slate-300">
                  {plan.medical_adjustments.map((adj: string, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-amber-400 mr-1.5">•</span>
                      <span>{adj}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400">No active medical report parameters applied. Calories set to basic requirements.</p>
              )}
            </div>

          </div>

          {/* 7-Day Meal Schedule Grid */}
          <div className="glass-panel p-6 rounded-2xl shadow border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center">
              <Calendar className="h-5 w-5 text-emerald-600 mr-2" /> Weekly Meal Plan Calendar
            </h3>
            
            <div className="space-y-6">
              {plan.weekly_plan?.map((day: any, i: number) => (
                <div key={i} className="border-b last:border-0 pb-6 last:pb-0">
                  <h4 className="text-base font-extrabold text-slate-900 mb-3 bg-emerald-50 text-emerald-800 px-3 py-1 rounded inline-block">
                    {day.day}
                  </h4>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-slate-50 border rounded-xl hover:bg-slate-100/70 transition">
                      <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Breakfast</span>
                      <p className="text-xs font-semibold text-slate-800 leading-relaxed">{day.breakfast}</p>
                    </div>
                    <div className="p-3 bg-slate-50 border rounded-xl hover:bg-slate-100/70 transition">
                      <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Lunch</span>
                      <p className="text-xs font-semibold text-slate-800 leading-relaxed">{day.lunch}</p>
                    </div>
                    <div className="p-3 bg-slate-50 border rounded-xl hover:bg-slate-100/70 transition">
                      <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Dinner</span>
                      <p className="text-xs font-semibold text-slate-800 leading-relaxed">{day.dinner}</p>
                    </div>
                    <div className="p-3 bg-slate-50 border rounded-xl hover:bg-slate-100/70 transition">
                      <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Snack</span>
                      <p className="text-xs font-semibold text-slate-800 leading-relaxed">{day.snack}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Foods list suggestions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 non-printable">
            
            {/* Foods to eat */}
            <div className="glass-panel p-6 rounded-2xl shadow border border-slate-200">
              <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center">
                <CheckCircle className="h-5 w-5 text-emerald-600 mr-2" /> Recommended Foods to Incorporate
              </h3>
              <ul className="grid grid-cols-2 gap-2 text-xs font-semibold text-slate-700">
                {plan.foods_to_eat?.map((food: string, idx: number) => (
                  <li key={idx} className="flex items-center space-x-1.5 p-2 bg-emerald-50/50 rounded-lg border border-emerald-100">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    <span>{food}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Foods to avoid */}
            <div className="glass-panel p-6 rounded-2xl shadow border border-slate-200">
              <h3 className="text-base font-bold text-slate-800 mb-4 flex items-center">
                <XCircle className="h-5 w-5 text-red-500 mr-2" /> Foods to Avoid or Limit
              </h3>
              <ul className="grid grid-cols-2 gap-2 text-xs font-semibold text-slate-700">
                {plan.foods_to_avoid?.map((food: string, idx: number) => (
                  <li key={idx} className="flex items-center space-x-1.5 p-2 bg-red-50/50 rounded-lg border border-red-100">
                    <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                    <span>{food}</span>
                  </li>
                ))}
              </ul>
            </div>

          </div>

          {/* Re-generate option */}
          <div className="text-center pt-4 non-printable">
            {error && (
              <div className="max-w-md mx-auto mb-4 bg-red-50 text-red-700 p-3 rounded-lg text-xs border border-red-200">
                {error}
              </div>
            )}
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="border border-emerald-600 hover:bg-emerald-50 text-emerald-700 font-semibold py-2.5 px-6 rounded-lg transition text-xs"
            >
              {loading ? 'Re-planning...' : 'Re-generate 7-Day Plan'}
            </button>
          </div>

        </div>
      )}
    </div>
  );
};

export default WeeklyPlanner;
