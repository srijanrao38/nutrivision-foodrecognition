// src/pages/Profile.tsx
import React, { useState, useEffect } from 'react';
import { User, Save, AlertTriangle, ShieldCheck } from 'lucide-react';
import api from '../api';

const Profile: React.FC = () => {
  const [profile, setProfile] = useState<any>({
    age: '',
    weight_kg: '',
    height_cm: '',
    gender: '',
    activity_level: 1.2,
    goal: 'maintain',
    diet_type: 'any',
    diet_high_protein: false,
    diet_low_carb: false,
    diet_diabetic: false,
    allergies: ''
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/api/profile/');
      setProfile({
        age: response.data.age || '',
        weight_kg: response.data.weight_kg || '',
        height_cm: response.data.height_cm || '',
        gender: response.data.gender || 'M',
        activity_level: response.data.activity_level || 1.2,
        goal: response.data.goal || 'maintain',
        diet_type: response.data.diet_type || 'any',
        diet_high_protein: response.data.diet_high_protein || false,
        diet_low_carb: response.data.diet_low_carb || false,
        diet_diabetic: response.data.diet_diabetic || false,
        allergies: response.data.allergies || ''
      });
    } catch (err) {
      setError('Failed to fetch profile details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    setError('');

    // Sanitize values
    const data = {
      ...profile,
      age: profile.age ? parseInt(profile.age) : null,
      weight_kg: profile.weight_kg ? parseFloat(profile.weight_kg) : null,
      height_cm: profile.height_cm ? parseFloat(profile.height_cm) : null,
    };

    try {
      await api.put('/api/profile/', data);
      setMessage('Profile updated successfully!');
      window.scrollTo(0, 0);
    } catch (err) {
      setError('Failed to save profile. Make sure values are valid.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="glass-panel rounded-2xl shadow-lg p-6 md:p-8 border border-slate-200">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
          <div className="flex items-center space-x-3">
            <User className="h-7 w-7 text-emerald-600" />
            <h1 className="text-2xl font-bold text-slate-800">Personal Health Profile</h1>
          </div>
          <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-0.5 rounded-full flex items-center">
            <ShieldCheck className="h-3 w-3 mr-1" /> Verified AI Assistant
          </span>
        </div>

        {message && (
          <div className="mb-6 bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded text-emerald-800 text-sm">
            {message}
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded text-red-800 text-sm">
            {error}
          </div>
        )}

        {/* MEDICAL DISCLAIMER BANNER */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-8 flex items-start space-x-3">
          <AlertTriangle className="h-6 w-6 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-amber-900 text-sm">Medical Disclaimer & Educational Scope</h4>
            <p className="text-amber-800 text-xs mt-1 leading-relaxed">
              All recommendations, nutrient calculations, and analysis provided by NutriVision AI are strictly for educational and informational purposes. This tool is NOT a medical diagnostic system and does NOT substitute for professional medical advice, treatment, or clinical decisions. Please consult a qualified health professional or doctor before implementing diet or lifestyle changes.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <h3 className="text-lg font-semibold text-slate-800 border-b pb-2">1. Physical Biomarkers</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Age (years)</label>
              <input
                type="number"
                min="1"
                max="120"
                value={profile.age}
                onChange={(e) => setProfile({ ...profile, age: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                placeholder="e.g., 24"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Weight (kg)</label>
              <input
                type="number"
                step="0.1"
                min="20"
                value={profile.weight_kg}
                onChange={(e) => setProfile({ ...profile, weight_kg: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                placeholder="e.g., 70"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Height (cm)</label>
              <input
                type="number"
                step="0.1"
                min="50"
                value={profile.height_cm}
                onChange={(e) => setProfile({ ...profile, height_cm: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                placeholder="e.g., 175"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Gender</label>
              <select
                value={profile.gender}
                onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Activity Level</label>
              <select
                value={profile.activity_level}
                onChange={(e) => setProfile({ ...profile, activity_level: parseFloat(e.target.value) })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              >
                <option value="1.2">Sedentary (little or no exercise)</option>
                <option value="1.375">Lightly active (exercise 1-3 days/week)</option>
                <option value="1.55">Moderately active (exercise 3-5 days/week)</option>
                <option value="1.725">Very active (hard exercise 6-7 days/week)</option>
                <option value="1.9">Super active (very hard work/athlete)</option>
              </select>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-800 border-b pb-2 pt-4">2. Nutrition Goals & Preferences</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Primary Weight Goal</label>
              <select
                value={profile.goal}
                onChange={(e) => setProfile({ ...profile, goal: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              >
                <option value="maintain">Weight Maintenance</option>
                <option value="lose">Weight Loss</option>
                <option value="gain">Weight Gain</option>
                <option value="muscle">Muscle Gain</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Dietary Category</label>
              <select
                value={profile.diet_type}
                onChange={(e) => setProfile({ ...profile, diet_type: e.target.value })}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              >
                <option value="any">Standard / Non-restrictive</option>
                <option value="veg">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="nonveg">Non-Vegetarian</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">Health Targets & Medical Diets</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={profile.diet_high_protein}
                  onChange={(e) => setProfile({ ...profile, diet_high_protein: e.target.checked })}
                  className="h-5 w-5 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500"
                />
                <span className="text-sm font-medium text-slate-700">High Protein Diet</span>
              </label>

              <label className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={profile.diet_low_carb}
                  onChange={(e) => setProfile({ ...profile, diet_low_carb: e.target.checked })}
                  className="h-5 w-5 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500"
                />
                <span className="text-sm font-medium text-slate-700">Low Carb Diet</span>
              </label>

              <label className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100 transition">
                <input
                  type="checkbox"
                  checked={profile.diet_diabetic}
                  onChange={(e) => setProfile({ ...profile, diet_diabetic: e.target.checked })}
                  className="h-5 w-5 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500"
                />
                <span className="text-sm font-medium text-slate-700">Diabetic Diet</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Food Allergies</label>
            <input
              type="text"
              value={profile.allergies}
              onChange={(e) => setProfile({ ...profile, allergies: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-emerald-500 focus:border-emerald-500 outline-none"
              placeholder="e.g., peanuts, dairy, shellfish (comma separated)"
            />
            <p className="text-xs text-slate-400 mt-1">If none, leave blank. Commas separate items.</p>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center justify-center py-3 px-6 border border-transparent text-sm font-semibold rounded-lg text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 transition-all shadow-md w-full md:w-auto"
            >
              <Save className="h-4 w-4 mr-2" />
              {saving ? 'Saving...' : 'Save Profile Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Profile;
