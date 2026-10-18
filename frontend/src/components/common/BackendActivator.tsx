'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Zap, CheckCircle2, Loader2, RefreshCw, AlertCircle, Server, Activity } from 'lucide-react';
import { wakeAndPingBackend, BASE_URL } from '@/lib/api-client';
import { HealthStatus } from '@/lib/types';

interface BackendActivatorProps {
  variant?: 'navbar-pill' | 'hero-card' | 'standalone-button';
  autoWakeOnMount?: boolean;
  className?: string;
}

export function BackendActivator({
  variant = 'navbar-pill',
  autoWakeOnMount = true,
  className = '',
}: BackendActivatorProps) {
  const [status, setStatus] = useState<'idle' | 'waking' | 'active' | 'error'>('idle');
  const [latency, setLatency] = useState<number | null>(null);
  const [elapsedSec, setElapsedSec] = useState<number>(0);
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef<boolean>(false);

  const performWake = useCallback(async () => {
    if (isPollingRef.current) return;
    isPollingRef.current = true;
    setStatus('waking');
    setElapsedSec(0);

    // Elapsed seconds counter
    const startTime = Date.now();
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    const maxAttempts = 15;
    let attempt = 0;
    let success = false;

    while (attempt < maxAttempts && !success) {
      attempt++;
      try {
        const res = await wakeAndPingBackend();
        if (res.ok) {
          success = true;
          setStatus('active');
          setLatency(res.latencyMs);
          if (res.data) setHealthData(res.data);
          break;
        }
      } catch {
        // Retry
      }

      // Wait 3 seconds before next poll
      await new Promise((r) => setTimeout(r, 3000));
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    isPollingRef.current = false;

    if (!success) {
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    if (autoWakeOnMount) {
      performWake();
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoWakeOnMount, performWake]);

  // Variant 1: Navbar Pill (Fits neatly into header / navbar)
  if (variant === 'navbar-pill') {
    return (
      <div className={`relative inline-block ${className}`}>
        <button
          onClick={() => {
            if (status !== 'waking') {
              if (status === 'active') {
                setShowDetails((prev) => !prev);
              } else {
                performWake();
              }
            }
          }}
          title={
            status === 'active'
              ? `Backend is online (${latency}ms). Click for details.`
              : status === 'waking'
              ? `Render backend is waking up (${elapsedSec}s)...`
              : 'Click to wake up backend server'
          }
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all shadow-sm border ${
            status === 'active'
              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 dark:hover:bg-emerald-900/50'
              : status === 'waking'
              ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800 animate-pulse'
              : 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800 hover:bg-indigo-100 dark:hover:bg-indigo-900/50'
          }`}
        >
          {status === 'active' && (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-semibold">Backend Active</span>
              {latency !== null && (
                <span className="text-[10px] opacity-75 hidden sm:inline">({latency}ms)</span>
              )}
            </>
          )}

          {status === 'waking' && (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600 dark:text-amber-400" />
              <span className="font-semibold">Waking Backend...</span>
              <span className="text-[10px] font-mono bg-amber-200/60 dark:bg-amber-800/60 px-1.5 py-0.2 rounded">
                {elapsedSec}s
              </span>
            </>
          )}

          {(status === 'idle' || status === 'error') && (
            <>
              <Zap className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
              <span className="font-semibold">Wake Backend</span>
            </>
          )}
        </button>

        {/* Dropdown details popup */}
        {showDetails && status === 'active' && (
          <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-slate-900 rounded-xl shadow-xl border border-slate-200 dark:border-slate-800 p-3.5 z-50 text-xs text-left animate-in fade-in slide-in-from-top-1">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 dark:border-slate-800">
              <span className="font-bold text-slate-800 dark:text-slate-100 flex items-center space-x-1.5">
                <Server className="w-3.5 h-3.5 text-emerald-600" />
                <span>Backend Live Status</span>
              </span>
              <button
                onClick={() => performWake()}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded"
                title="Re-ping backend"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            <div className="space-y-1.5 text-slate-600 dark:text-slate-300">
              <div className="flex justify-between">
                <span>Status:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold">Online (200 OK)</span>
              </div>
              <div className="flex justify-between">
                <span>Latency:</span>
                <span className="font-mono">{latency}ms</span>
              </div>
              <div className="flex justify-between">
                <span>Database:</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-medium">Connected</span>
              </div>
              <div className="text-[10px] text-slate-400 dark:text-slate-500 pt-1 border-t border-slate-100 dark:border-slate-800 truncate" title={BASE_URL}>
                Target: {BASE_URL}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Variant 2: Hero Section Action Card / Banner
  if (variant === 'hero-card') {
    return (
      <div
        className={`w-full max-w-xl mx-auto rounded-2xl border p-4 sm:p-5 transition-all text-left shadow-sm ${
          status === 'active'
            ? 'bg-gradient-to-r from-emerald-500/10 via-teal-500/5 to-transparent border-emerald-500/30'
            : status === 'waking'
            ? 'bg-gradient-to-r from-amber-500/10 via-orange-500/5 to-transparent border-amber-500/30 animate-pulse'
            : 'bg-gradient-to-r from-blue-500/10 via-indigo-500/5 to-transparent border-blue-500/30 hover:border-blue-500/50'
        } ${className}`}
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div
              className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${
                status === 'active'
                  ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800'
                  : status === 'waking'
                  ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 border-amber-300 dark:border-amber-800'
                  : 'bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border-blue-300 dark:border-blue-800'
              }`}
            >
              {status === 'active' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              ) : status === 'waking' ? (
                <Loader2 className="w-5 h-5 animate-spin text-amber-600 dark:text-amber-400" />
              ) : (
                <Zap className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              )}
            </div>

            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-sm sm:text-base text-slate-900 dark:text-white">
                  {status === 'active'
                    ? 'Backend Server: Active & Ready'
                    : status === 'waking'
                    ? 'Waking Up Render Backend Server...'
                    : 'Activate Backend Server'}
                </span>
                {status === 'active' && latency !== null && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full font-mono font-medium bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300">
                    {latency}ms
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                {status === 'active'
                  ? 'FastAPI AI Engine, ATS Resume & Mock Interview APIs are live.'
                  : status === 'waking'
                  ? `Render Free Tier container is booting up (elapsed: ${elapsedSec}s). Takes ~20-30s.`
                  : 'Click below to spin up the Render container before logging in.'}
              </p>
            </div>
          </div>

          <button
            onClick={() => performWake()}
            disabled={status === 'waking'}
            className={`w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold flex items-center justify-center space-x-2 transition-all shadow-sm shrink-0 ${
              status === 'active'
                ? 'bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
                : status === 'waking'
                ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-400/40 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20'
            }`}
          >
            {status === 'active' ? (
              <>
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Re-Check</span>
              </>
            ) : status === 'waking' ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Waking ({elapsedSec}s)...</span>
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5" />
                <span>Activate Backend Now</span>
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  // Variant 3: Standalone Button
  return (
    <button
      onClick={() => performWake()}
      disabled={status === 'waking'}
      className={`px-4 py-2 rounded-xl text-sm font-semibold flex items-center space-x-2 transition-all shadow-sm ${
        status === 'active'
          ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
          : status === 'waking'
          ? 'bg-amber-600 text-white cursor-wait animate-pulse'
          : 'bg-blue-600 hover:bg-blue-500 text-white'
      } ${className}`}
    >
      {status === 'active' ? (
        <>
          <CheckCircle2 className="w-4 h-4" />
          <span>Backend Online</span>
        </>
      ) : status === 'waking' ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Activating Backend ({elapsedSec}s)...</span>
        </>
      ) : (
        <>
          <Zap className="w-4 h-4" />
          <span>Activate Backend</span>
        </>
      )}
    </button>
  );
}
