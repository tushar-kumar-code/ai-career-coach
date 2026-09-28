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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-lg rounded-3xl bg-white dark:bg-[#172235] border border-[#E7E2D8] dark:border-[#334155] shadow-2xl overflow-hidden">
        {/* Header bar */}
        <div className="absolute top-0 inset-x-0 h-1 bg-[#17324D] dark:bg-[#B89B72]" />

        {/* Header */}
        <div className="p-6 pb-4 border-b border-[#E7E2D8] dark:border-[#334155]">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[#17324D] dark:bg-[#102A43] flex items-center justify-center shadow-sm text-[#B89B72]">
                <Key className="w-5 h-5 text-[#B89B72]" />
              </div>
              <div>
                <h2 className="font-bold text-[#17324D] dark:text-[#F1F5F9] text-base">Activate AI Features</h2>
                <p className="text-xs text-[#64748B] dark:text-[#A8B3C2]">One-time setup to enable all AI-powered features</p>
              </div>
            </div>
            <button
              onClick={handleSkip}
              className="p-1.5 rounded-lg text-[#64748B] hover:text-[#17324D] dark:hover:text-white hover:bg-[#FAF8F3] dark:hover:bg-[#102A43] transition"
              title="Skip for now"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-5">
          {/* Info Banner */}
          <div className="p-3.5 rounded-xl bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-[#B89B72] shrink-0 mt-0.5" />
            <p className="text-xs text-[#64748B] dark:text-[#A8B3C2] leading-relaxed">
              To use AI Career Coach, Mock Interviews, Resume Analysis, and Roadmap Generation, you need a free AI API key.
              <strong className="text-[#17324D] dark:text-[#F1F5F9]"> Once set, you won&apos;t be asked again.</strong>
            </p>
          </div>

          {/* Provider Choice */}
          <div>
            <label className="block text-xs font-semibold text-[#273444] dark:text-[#F1F5F9] mb-2">Select AI Provider</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => { setProvider('groq'); setTestResult(null); }}
                className={`p-3 rounded-xl border text-left transition ${
                  provider === 'groq'
                    ? 'bg-[#B89B72]/15 border-[#B89B72] ring-1 ring-[#B89B72]'
                    : 'bg-[#FAF8F3] dark:bg-[#102A43] border-[#E7E2D8] dark:border-[#334155] hover:border-[#B89B72]/50'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Zap className="w-3.5 h-3.5 text-[#C78A20]" />
                  <span className="font-bold text-sm text-[#17324D] dark:text-[#F1F5F9]">Groq</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-[#B89B72]/20 text-[#17324D] dark:text-[#D9C19A] rounded font-semibold">Free</span>
                </div>
                <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">Llama 3.3 70B, ultra-fast</p>
              </button>
              <button
                type="button"
                onClick={() => { setProvider('gemini'); setTestResult(null); }}
                className={`p-3 rounded-xl border text-left transition ${
                  provider === 'gemini'
                    ? 'bg-[#B89B72]/15 border-[#B89B72] ring-1 ring-[#B89B72]'
                    : 'bg-[#FAF8F3] dark:bg-[#102A43] border-[#E7E2D8] dark:border-[#334155] hover:border-[#B89B72]/50'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Sparkles className="w-3.5 h-3.5 text-[#B89B72]" />
                  <span className="font-bold text-sm text-[#17324D] dark:text-[#F1F5F9]">Gemini</span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-[#B89B72]/20 text-[#17324D] dark:text-[#D9C19A] rounded font-semibold">Free</span>
                </div>
                <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2]">Google Gemini 2.5 Flash</p>
              </button>
            </div>
          </div>

          {/* API Key Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-[#273444] dark:text-[#F1F5F9]">
                {provider === 'groq' ? 'Groq API Key' : 'Gemini API Key'}
              </label>
              <a
                href={provider === 'groq' ? 'https://console.groq.com/keys' : 'https://aistudio.google.com/app/apikey'}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-[#B89B72] hover:underline flex items-center gap-1 font-semibold"
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
                className="w-full bg-[#FAF8F3] dark:bg-[#102A43] border border-[#E7E2D8] dark:border-[#334155] rounded-xl px-3.5 py-2.5 text-sm text-[#273444] dark:text-[#F1F5F9] placeholder-[#64748B] focus:outline-none focus:ring-2 focus:ring-[#B89B72] pr-10 font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#273444] dark:hover:text-[#F1F5F9]"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[11px] text-[#64748B] dark:text-[#A8B3C2] mt-1.5 flex items-center gap-1">
              <Shield className="w-3 h-3 text-[#2E7D5B]" />
              Saved in your browser only — never shared or stored on servers.
            </p>
          </div>

          {/* Result Banner */}
          {testResult && (
            <div className={`p-3.5 rounded-xl border text-xs flex items-start gap-2.5 ${
              testResult.success
                ? 'bg-emerald-500/10 border-[#2E7D5B]/30 text-[#2E7D5B]'
                : 'bg-rose-500/10 border-[#C75C5C]/30 text-[#C75C5C]'
            }`}>
              {testResult.success
                ? <CheckCircle2 className="w-4 h-4 text-[#2E7D5B] shrink-0 mt-0.5" />
                : <AlertCircle className="w-4 h-4 text-[#C75C5C] shrink-0 mt-0.5" />}
              <span>{testResult.message}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#FAF8F3] dark:bg-[#102A43] border-t border-[#E7E2D8] dark:border-[#334155] flex items-center justify-between">
          <button
            type="button"
            onClick={handleSkip}
            className="text-xs text-[#64748B] dark:text-[#A8B3C2] hover:text-[#17324D] dark:hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-white dark:hover:bg-[#172235]"
          >
            Skip for now
          </button>
          <button
            type="button"
            onClick={handleTestAndSave}
            disabled={isTesting || isSaving || !apiKey.trim()}
            className="px-5 py-2 text-xs font-bold rounded-xl bg-[#17324D] hover:bg-[#102A43] text-white transition flex items-center gap-2 disabled:opacity-50 shadow-sm"
          >
            {isTesting ? (
              <><Loader2 className="w-3.5 h-3.5 animate-spin text-[#B89B72]" /> Verifying Key...</>
            ) : isSaving ? (
              <><CheckCircle2 className="w-3.5 h-3.5 text-[#2E7D5B]" /> Activated!</>
            ) : (
              <>Verify & Activate <ArrowRight className="w-3.5 h-3.5" /></>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
