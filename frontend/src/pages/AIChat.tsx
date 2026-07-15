// src/pages/AIChat.tsx
import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, AlertTriangle, ShieldCheck, Heart, FileText, User } from 'lucide-react';
import api from '../api';

interface Message {
  role: 'user' | 'assistant';
  text: string;
}

const AIChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchProfileContext();
    // Default welcome message
    setMessages([
      { role: 'assistant', text: 'Hello! I am your AI Nutrition Assistant. Ask me anything about diet, calories, healthy breakfast options, or foods to eat based on your profile.' }
    ]);
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchProfileContext = async () => {
    try {
      const [profileRes, reportRes] = await Promise.all([
        api.get('/api/profile/'),
        api.get('/api/medical/history/')
      ]);
      setProfile(profileRes.data);
      if (reportRes.data && reportRes.data.length > 0) {
        setReport(reportRes.data[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setLoading(true);

    try {
      const response = await api.post('/api/chat/', { message: userText });
      setMessages(prev => [...prev, { role: 'assistant', text: response.data.message }]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Sorry, I failed to process that request. Please try again later.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Educational disclaimer */}
      <p className="text-[10px] text-slate-400 text-center mb-4">
        NutriVision AI is an educational fitness planner, not a medical platform. In case of illness, consult a doctor.
      </p>

      <div className="flex items-center space-x-3 border-b pb-4 mb-6">
        <MessageSquare className="h-7 w-7 text-emerald-600" />
        <h1 className="text-2xl font-bold text-slate-800">Personalized Nutrition AI Assistant</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left Side: Active Health Context Panel (Grounding Panel) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-5 rounded-2xl shadow border border-slate-200 bg-slate-900 text-white">
            <h3 className="text-sm font-bold text-emerald-400 mb-4 flex items-center">
              <ShieldCheck className="h-4 w-4 mr-1.5" /> RAG Grounding Profile
            </h3>
            
            <div className="space-y-4 text-xs">
              <div>
                <p className="text-slate-400 font-semibold mb-1 flex items-center"><User className="h-3.5 w-3.5 mr-1" /> Core Goals</p>
                <ul className="space-y-1 text-slate-350">
                  <li>Goal: <span className="text-slate-200 capitalize font-medium">{profile?.goal || 'N/A'}</span></li>
                  <li>Type: <span className="text-slate-200 capitalize font-medium">{profile?.diet_type || 'N/A'}</span></li>
                  <li>Allergies: <span className="text-slate-200 font-medium">{profile?.allergies || 'None'}</span></li>
                </ul>
              </div>

              <div className="border-t border-slate-800 pt-3">
                <p className="text-slate-400 font-semibold mb-1 flex items-center"><Heart className="h-3.5 w-3.5 mr-1" /> Active Diets</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {profile?.diet_high_protein && <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/30">High Protein</span>}
                  {profile?.diet_low_carb && <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded border border-blue-500/30">Low Carb</span>}
                  {profile?.diet_diabetic && <span className="bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded border border-amber-500/30">Diabetic Diet</span>}
                  {!profile?.diet_high_protein && !profile?.diet_low_carb && !profile?.diet_diabetic && <span className="text-slate-500">None selected</span>}
                </div>
              </div>

              <div className="border-t border-slate-800 pt-3">
                <p className="text-slate-400 font-semibold mb-1 flex items-center"><FileText className="h-3.5 w-3.5 mr-1" /> Lab Biomarkers</p>
                {report ? (
                  <ul className="space-y-1 text-slate-350">
                    {report.blood_sugar && <li>Sugar: <span className="text-slate-200 font-medium">{report.blood_sugar} mg/dL</span></li>}
                    {report.hba1c && <li>HbA1c: <span className="text-slate-200 font-medium">{report.hba1c}%</span></li>}
                    {report.cholesterol && <li>Cholesterol: <span className="text-slate-200 font-medium">{report.cholesterol} mg/dL</span></li>}
                    {report.ldl && <li>LDL: <span className="text-slate-200 font-medium">{report.ldl} mg/dL</span></li>}
                  </ul>
                ) : (
                  <p className="text-slate-550">No reports uploaded.</p>
                )}
              </div>
            </div>
          </div>
          
          {/* Medical disclaimer notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start space-x-2 text-xs">
            <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-amber-900">Safety Notice</p>
              <p className="text-amber-800 leading-relaxed mt-1">
                Recommendations are educational. Consult a clinician before modifying diagnostic parameters.
              </p>
            </div>
          </div>
        </div>

        {/* Right Side: Chat Window */}
        <div className="lg:col-span-3 flex flex-col h-[650px] glass-panel rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
          
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/50">
            {messages.map((msg, idx) => {
              const isAI = msg.role === 'assistant';
              return (
                <div key={idx} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-2xl px-4 py-3 rounded-2xl shadow-sm text-sm leading-relaxed ${
                    isAI
                      ? 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                      : 'bg-emerald-600 text-white rounded-br-none'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              );
            })}
            
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl rounded-bl-none shadow-sm flex items-center space-x-2">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce"></span>
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce delay-100"></span>
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce delay-200"></span>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>

          {/* Input field form */}
          <form onSubmit={handleSend} className="p-4 border-t border-slate-200 bg-white flex items-center space-x-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about vitamins, sugar values, cholesterol food tips..."
              className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition text-sm"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white p-3 rounded-xl transition shadow-md shrink-0"
            >
              <Send className="h-5 w-5" />
            </button>
          </form>

        </div>

      </div>
    </div>
  );
};

export default AIChat;
