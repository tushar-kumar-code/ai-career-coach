'use client';

import { useState, useEffect } from 'react';
import {
  X,
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
  Trash2,
  RefreshCw,
} from 'lucide-react';
import {
  getSavedAIConfig,
  saveAIConfig,
  clearSavedAIConfig,
  testApiKey,
} from '@/lib/api-client';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved?: () => void;
}

export default function ApiKeyModal({ isOpen, onClose, onSaved }: ApiKeyModalProps) {
  const [provider, setProvider] = useState<'groq' | 'gemini' | 'openai'>('groq');
  const [apiKey, setApiKey] = useState('');
  const [model, setModel] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [isSavedNotice, setIsSavedNotice] = useState(false);

  useEffect(() => {
    if (isOpen) {
      const config = getSavedAIConfig();
      setProvider((config.provider as any) || 'groq');
      setApiKey(config.apiKey || '');
      setModel(config.model || '');
      setTestResult(null);
      setIsSavedNotice(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleTestKey = async () => {
    if (!apiKey.trim()) {
      setTestResult({
        success: false,
        message: 'Please enter an API Key first to test connection.',
      });
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      const res = await testApiKey(provider, apiKey.trim(), model.trim() || undefined);
      setTestResult({
        success: true,
        message: res.message || `${provider.toUpperCase()} API key verified successfully!`,
      });
    } catch (err: any) {
      setTestResult({
        success: false,
        message: err.message || 'Failed to connect. Please verify your key.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = () => {
    if (!apiKey.trim()) {
      setTestResult({
        success: false,
        message: 'API Key cannot be blank.',
      });
      return;
    }

    saveAIConfig(provider, apiKey.trim(), model.trim() || undefined);
    setIsSavedNotice(true);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('ai-config-updated'));
    }
    setTimeout(() => {
      if (onSaved) onSaved();
      onClose();
    }, 600);
  };

  const handleClear = () => {
    clearSavedAIConfig();
    setApiKey('');
    setModel('');
    setTestResult(null);
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new Event('ai-config-updated'));
    }
    if (onSaved) onSaved();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                AI API Key Configuration
                <span className="px-2 py-0.5 text-[10px] uppercase font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                  All Features
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Connect your personal API key for instant, uncapped AI coaching & mock interviews
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto">
          {/* Provider Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Select AI Engine / Provider
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => {
                  setProvider('groq');
                  setTestResult(null);
                }}
                className={`p-3.5 rounded-xl border flex flex-col text-left transition ${
                  provider === 'groq'
                    ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500'
                    : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="font-bold text-sm text-slate-200 flex items-center gap-1.5">
                    <Zap className="w-4 h-4 text-amber-400" />
                    Groq
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-indigo-500/20 text-indigo-300 rounded font-semibold">
                    Recommended
                  </span>
                </div>
                <span className="text-xs text-slate-400">Ultra-fast Llama 3.3 70B with generous free tier</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setProvider('gemini');
                  setTestResult(null);
                }}
                className={`p-3.5 rounded-xl border flex flex-col text-left transition ${
                  provider === 'gemini'
                    ? 'bg-indigo-600/15 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500'
                    : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="font-bold text-sm text-slate-200 flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-sky-400" />
                    Google Gemini
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-sky-500/20 text-sky-300 rounded font-semibold">
                    Gemini Flash
                  </span>
                </div>
                <span className="text-xs text-slate-400">Google Gemini 2.5/2.0 Flash models via Google AI Studio</span>
              </button>
            </div>
          </div>

          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-300">
                {provider === 'groq' ? 'Groq API Key' : 'Gemini API Key'}
              </label>
              {provider === 'groq' ? (
                <a
                  href="https://console.groq.com/keys"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 hover:underline"
                >
                  Get free Groq key <ExternalLink className="w-3 h-3" />
                </a>
              ) : (
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 hover:underline"
                >
                  Get free Gemini key <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => {
                  setApiKey(e.target.value);
                  setTestResult(null);
                }}
                placeholder={
                  provider === 'groq'
                    ? 'gsk_...'
                    : 'AIzaSy...'
                }
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
              Stored privately in your browser session & securely sent directly to AI services.
            </p>
          </div>

          {/* Test Connection Banner */}
          {testResult && (
            <div
              className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
                testResult.success
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              }`}
            >
              {testResult.success ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <span className="font-semibold block mb-0.5">
                  {testResult.success ? 'Connection Verified' : 'Connection Failed'}
                </span>
                <span>{testResult.message}</span>
              </div>
            </div>
          )}

          {isSavedNotice && (
            <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              API Key saved! Activating for all coach & interview features...
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between">
          <div>
            {apiKey && (
              <button
                type="button"
                onClick={handleClear}
                className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 px-2.5 py-1.5 rounded-lg hover:bg-rose-500/10 transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Remove Key
              </button>
            )}
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={handleTestKey}
              disabled={isTesting || !apiKey.trim()}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition flex items-center gap-1.5 disabled:opacity-50"
            >
              {isTesting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  Test Key
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={!apiKey.trim()}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-sm shadow-indigo-600/30 flex items-center gap-1.5 disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              Save & Activate
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
