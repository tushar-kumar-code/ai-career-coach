'use client';

import { useState, useEffect } from 'react';
import {
  Key,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ExternalLink,
  Shield,
  Eye,
  EyeOff,
  Sparkles,
  Zap,
  X,
  ArrowRight,
} from 'lucide-react';
import {
  getSavedAIConfig,
  saveAIConfig,
  testApiKey,
} from '@/lib/api-client';

interface FirstTimeApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSkip?: () => void;
}

export default function FirstTimeApiKeyModal({ isOpen, onClose, onSkip }: FirstTimeApiKeyModalProps) {
  const [provider, setProvider] = useState<'groq' | 'gemini'>('groq');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setApiKey('');
      setTestResult(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestAndSave = async () => {
    if (!apiKey.trim()) {
      setTestResult({ success: false, message: 'Please enter an API key first.' });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      await testApiKey(provider, apiKey.trim());
      setIsTesting(false);
      setIsSaving(true);
      saveAIConfig(provider, apiKey.trim());
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new Event('ai-config-updated'));
      }
      setTimeout(() => {
        onClose();
      }, 800);
      setTestResult({ success: true, message: 'Key verified and activated! AI features are now unlocked.' });
    } catch (err: any) {
      setIsTesting(false);
      setTestResult({ success: false, message: err.message || 'Invalid API key. Please check and try again.' });
    }
  };

  const handleSkip = () => {
    if (onSkip) onSkip();
    else onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md">
      <div className="relative w-full max-w-lg rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden">
        {/* Glow accent */}
        <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />

        {/* Header */}
        <div className="p-6 pb-4 border-b border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
                <Key className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-white text-base">Activate AI Features</h2>
                <p className="text-xs text-slate-400">One-time setup to enable all AI-powered features</p>
              </div>
            </div>
            <button
              onClick={handleSkip}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition"
              title="Skip for now"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Info Banner */}
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <p className="text-xs text-slate-300 leading-relaxed">
              To use AI Career Coach, Mock Interviews, Resume Analysis, and Roadmap Generation, you need a free AI API key.
              <strong className="text-white"> Once set, you won't be asked again.</strong>
            </p>
          </div>

          {/* Provider Choice */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Select AI Provider</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => { setProvider('groq'); setTestResult(null); }}
                className={`p-3 rounded-xl border text-left transition ${
                  provider === 'groq'
                    ? 'bg-indigo-600/15 border-indigo-500 ring-1 ring-indigo-500'
                    : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Zap className="w-3.5 h-3.5 text-amber-400" />
                  <span className="font-bold text-sm text-slate-200">Groq</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded font-semibold">Free</span>
                </div>
                <p className="text-[11px] text-slate-500">Llama 3.3 70B, ultra-fast</p>
              </button>
              <button
                type="button"
                onClick={() => { setProvider('gemini'); setTestResult(null); }}
                className={`p-3 rounded-xl border text-left transition ${
                  provider === 'gemini'
                    ? 'bg-indigo-600/15 border-indigo-500 ring-1 ring-indigo-500'
                    : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                  <span className="font-bold text-sm text-slate-200">Gemini</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-sky-500/20 text-sky-300 rounded font-semibold">Free</span>
                </div>
                <p className="text-[11px] text-slate-500">Google Gemini 2.5 Flash</p>
              </button>
            </div>
          </div>

          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                {provider === 'groq' ? 'Groq API Key' : 'Gemini API Key'}
              </label>
              <a
                href={provider === 'groq' ? 'https://console.groq.com/keys' : 'https://aistudio.google.com/app/apikey'}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-indigo-400 hover:underline flex items-center gap-1"
              >
                Get free key <ExternalLink className="w-3 h-3" />
              </a>
            </div>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => { setApiKey(e.target.value); setTestResult(null); }}
                placeholder={provider === 'groq' ? 'gsk_...' : 'AIzaSy...'}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 pr-10 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
              <Shield className="w-3 h-3 text-emerald-400" />
              Saved in your browser only — never shared or stored on servers.
            </p>
          </div>

          {/* Result Banner */}
          {testResult && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
              testResult.success
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}>
              {testResult.success
                ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                : <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />}
              <span>{testResult.message}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/50 border-t border-slate-800 flex items-center justify-between">
          <button
            type="button"
            onClick={handleSkip}
            className="text-xs text-slate-500 hover:text-slate-300 transition px-3 py-1.5 rounded-lg hover:bg-slate-800"
          >
            Skip for now
          </button>
          <button
            type="button"
            onClick={handleTestAndSave}
            disabled={isTesting || isSaving || !apiKey.trim()}
            className="px-5 py-2 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-2 disabled:opacity-50 shadow-md shadow-indigo-600/25"
          >
            {isTesting ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Verifying Key...</>
            ) : isSaving ? (
              <><CheckCircle2 className="w-3.5 h-3.5" /> Activated!</>
            ) : (
              <>Verify & Activate <ArrowRight className="w-3.5 h-3.5" /></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
