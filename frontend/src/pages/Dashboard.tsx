// src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Activity, Apple, Flame, Sparkles, TrendingUp, AlertTriangle, ChevronRight, FileText } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import api from '../api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [profileRes, logsRes, reportsRes] = await Promise.all([
        api.get('/api/profile/'),
        api.get('/api/food/log/'),
        api.get('/api/medical/history/')
      ]);
      setProfile(profileRes.data);
      setLogs(logsRes.data);
      setReports(reportsRes.data);
    } catch (err) {
      console.error("Error loading dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  // Calculate todays logs
  const todayStr = new Date().toISOString().split('T')[0];
  const todaysLogs = logs.filter(log => {
    const logDate = new Date(log.detected_at || log.date).toISOString().split('T')[0];
    return logDate === todayStr;
  });

  const totals = todaysLogs.reduce((acc, curr) => ({
    calories: acc.calories + curr.calories,
    protein: acc.protein + curr.protein_g,
    carbs: acc.carbs + curr.carbs_g,
    fat: acc.fat + curr.fat_g,
  }), { calories: 0, protein: 0, carbs: 0, fat: 0 });

  // Calculate targets based on BMR/TDEE heuristic or defaults
  const targetCalories = profile ? Math.round(
    (10 * (profile.weight_kg || 70) + 6.25 * (profile.height_cm || 175) - 5 * (profile.age || 25) + 5) * (profile.activity_level || 1.2) +
    (profile.goal === 'lose' ? -500 : profile.goal === 'gain' ? 500 : 0)
  ) : 2000;
  
  const targetProtein = Math.round(targetCalories * 0.2 / 4);
  const targetCarbs = Math.round(targetCalories * 0.5 / 4);
  const targetFat = Math.round(targetCalories * 0.3 / 9);

  const calPercentage = Math.min(100, Math.round((totals.calories / targetCalories) * 100));
  const proPercentage = Math.min(100, Math.round((totals.protein / targetProtein) * 100));
  const carbPercentage = Math.min(100, Math.round((totals.carbs / targetCarbs) * 100));
  const fatPercentage = Math.min(100, Math.round((totals.fat / targetFat) * 100));

  // Chart data (last 7 days of logs)
  const getChartData = () => {
    const dataMap: { [key: string]: number } = {};
    const last7Days = Array.from({ length: 7 }).map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - i);
      return d.toISOString().split('T')[0];
    }).reverse();

    last7Days.forEach(date => {
      dataMap[date] = 0;
    });

    logs.forEach(log => {
      const logDate = new Date(log.detected_at || log.date).toISOString().split('T')[0];
      if (logDate in dataMap) {
        dataMap[logDate] += log.calories;
      }
    });

    return last7Days.map(date => {
      const [_, m, d] = date.split('-');
      return {
        name: `${m}/${d}`,
        Calories: Math.round(dataMap[date]),
      };
    });
  };

  const chartData = getChartData();
  const latestReport = reports[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Disclaimer Notice */}
      <p className="text-[10px] text-slate-400 text-center mb-4">
        NutriVision AI is an educational fitness planner, not a medical platform. In case of illness, consult a doctor.
      </p>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left column (Nutrient status gauges) */}
        <div className="lg:col-span-2 space-y-8">
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center">
              <Flame className="h-5 w-5 text-amber-500 mr-2 animate-bounce" /> Today's Energy Tracker
            </h2>

            {/* Calorie Gauge */}
            <div className="flex flex-col md:flex-row items-center justify-around gap-6 mb-8">
              <div className="relative flex items-center justify-center w-36 h-36">
                <svg className="w-full h-full transform -rotate-90">
                  <circle cx="72" cy="72" r="64" stroke="#e2e8f0" strokeWidth="12" fill="transparent" />
                  <circle
                    cx="72"
                    cy="72"
                    r="64"
                    stroke="#10b981"
                    strokeWidth="12"
                    fill="transparent"
                    strokeDasharray={402}
                    strokeDashoffset={402 - (402 * calPercentage) / 100}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="text-3xl font-extrabold text-slate-900">{Math.round(totals.calories)}</span>
                  <span className="text-xs font-semibold text-slate-500">/ {targetCalories} kcal</span>
                </div>
              </div>

              <div className="flex-1 w-full space-y-4">
                {/* Protein */}
                <div>
                  <div className="flex justify-between text-sm font-medium mb-1">
                    <span className="text-slate-700">Protein ({Math.round(totals.protein)}g / {targetProtein}g)</span>
                    <span className="text-slate-500 font-semibold">{proPercentage}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3">
                    <div className="bg-emerald-500 h-3 rounded-full transition-all duration-1000" style={{ width: `${proPercentage}%` }}></div>
                  </div>
                </div>

                {/* Carbs */}
                <div>
                  <div className="flex justify-between text-sm font-medium mb-1">
                    <span className="text-slate-700">Carbohydrates ({Math.round(totals.carbs)}g / {targetCarbs}g)</span>
                    <span className="text-slate-500 font-semibold">{carbPercentage}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3">
                    <div className="bg-blue-500 h-3 rounded-full transition-all duration-1000" style={{ width: `${carbPercentage}%` }}></div>
                  </div>
                </div>

                {/* Fat */}
                <div>
                  <div className="flex justify-between text-sm font-medium mb-1">
                    <span className="text-slate-700">Fat ({Math.round(totals.fat)}g / {targetFat}g)</span>
                    <span className="text-slate-500 font-semibold">{fatPercentage}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3">
                    <div className="bg-amber-500 h-3 rounded-full transition-all duration-1000" style={{ width: `${fatPercentage}%` }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 border-t pt-6 border-slate-100">
              <button onClick={() => navigate('/food-detection')} className="flex flex-col items-center p-3 rounded-xl hover:bg-emerald-50 text-slate-700 transition">
                <Apple className="h-6 w-6 text-emerald-600 mb-1" />
                <span className="text-xs font-semibold">Scan Meal</span>
              </button>
              <button onClick={() => navigate('/medical-upload')} className="flex flex-col items-center p-3 rounded-xl hover:bg-emerald-50 text-slate-700 transition">
                <FileText className="h-6 w-6 text-emerald-600 mb-1" />
                <span className="text-xs font-semibold">Upload Report</span>
              </button>
              <button onClick={() => navigate('/weekly-planner')} className="flex flex-col items-center p-3 rounded-xl hover:bg-emerald-50 text-slate-700 transition col-span-2 md:col-span-1">
                <Sparkles className="h-6 w-6 text-emerald-600 mb-1" />
                <span className="text-xs font-semibold">Get Diet Plan</span>
              </button>
            </div>
          </div>

          {/* Calorie Trend Chart */}
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center">
              <TrendingUp className="h-5 w-5 text-emerald-600 mr-2" /> Weekly Caloric Trend
            </h2>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="Calories" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorCal)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right column (Medical Alert & Recent logs) */}
        <div className="space-y-8">
          
          {/* Medical Summary & Alerts */}
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200 bg-slate-900 text-white">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center">
              <Activity className="h-5 w-5 text-emerald-400 mr-2" /> Medical Profile Status
            </h2>

            {latestReport ? (
              <div className="space-y-4">
                <div className="border-b border-slate-700 pb-3">
                  <p className="text-xs text-slate-400">Latest Report Date</p>
                  <p className="text-sm font-semibold">{new Date(latestReport.uploaded_at).toLocaleDateString()}</p>
                </div>

                {/* Biomarker Alerts */}
                <div className="space-y-2">
                  {latestReport.cholesterol && latestReport.cholesterol > 200 && (
                    <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-2.5 flex items-start space-x-2 text-xs">
                      <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-red-300">High Cholesterol Detected</span>
                        <p className="text-slate-300 mt-0.5">Total: {latestReport.cholesterol} mg/dL (Limit &lt; 200)</p>
                      </div>
                    </div>
                  )}

                  {latestReport.blood_sugar && latestReport.blood_sugar > 100 && (
                    <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-2.5 flex items-start space-x-2 text-xs">
                      <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-red-300">Elevated Blood Glucose</span>
                        <p className="text-slate-300 mt-0.5">Fasting: {latestReport.blood_sugar} mg/dL (Limit &lt; 100)</p>
                      </div>
                    </div>
                  )}

                  {latestReport.hba1c && latestReport.hba1c >= 5.7 && (
                    <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-2.5 flex items-start space-x-2 text-xs">
                      <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-red-300">HbA1c Alert</span>
                        <p className="text-slate-300 mt-0.5">Level: {latestReport.hba1c}% (Optimal &lt; 5.7%)</p>
                      </div>
                    </div>
                  )}

                  {/* Healthy Status */}
                  {(!latestReport.cholesterol || latestReport.cholesterol <= 200) &&
                   (!latestReport.blood_sugar || latestReport.blood_sugar <= 100) &&
                   (!latestReport.hba1c || latestReport.hba1c < 5.7) && (
                    <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg p-2.5 text-xs text-emerald-300">
                      ✅ All scanned biomarkers are within standard thresholds.
                    </div>
                  )}
                </div>

                <Link to="/medical-upload" className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center font-medium mt-2">
                  View full laboratory details <ChevronRight className="h-3 w-3 ml-1" />
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-sm text-slate-400 mb-4">No medical laboratory reports uploaded yet.</p>
                <button
                  onClick={() => navigate('/medical-upload')}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs py-2.5 px-4 rounded-lg transition"
                >
                  Upload Labs Report
                </button>
              </div>
            )}
          </div>

          {/* Recent Meals logged */}
          <div className="glass-panel p-6 rounded-2xl shadow-lg border border-slate-200">
            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center">
              <Apple className="h-5 w-5 text-emerald-600 mr-2" /> Recent Scans
            </h2>

            {todaysLogs.length > 0 ? (
              <div className="space-y-3">
                {todaysLogs.slice(0, 4).map((log, idx) => (
                  <div key={log.id || idx} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                    <div>
                      <h4 className="text-sm font-bold text-slate-800 capitalize">{log.food_name}</h4>
                      <p className="text-xs text-slate-500">{Math.round(log.calories)} kcal | P: {Math.round(log.protein_g)}g</p>
                    </div>
                    {log.health_score !== null && (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        log.health_score >= 80 ? 'bg-emerald-100 text-emerald-800' :
                        log.health_score >= 50 ? 'bg-amber-100 text-amber-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        Score: {log.health_score}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 py-4 text-center">No meals logged today.</p>
            )}
          </div>

        </div>

      </div>
    </div>
  );
};

export default Dashboard;
