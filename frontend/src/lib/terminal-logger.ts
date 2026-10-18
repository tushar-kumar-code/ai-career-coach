/**
 * Frontend Terminal Logger
 * Sends client-side actions, page navigations, and errors to both:
 * 1. Next.js local terminal (/api/terminal-log)
 * 2. FastAPI backend terminal (/api/v1/client-log)
 */

function getBackendLogUrl(): string {
  let raw = (process.env.NEXT_PUBLIC_API_URL || '').trim();
  if (!raw || raw.includes('<') || raw.includes('>') || raw.includes('backend-render-url')) {
    if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
      raw = 'https://ai-career-coach-backend-qkha.onrender.com/api/v1';
    } else {
      raw = 'http://127.0.0.1:8000/api/v1';
    }
  }
  if (!raw.startsWith('http://') && !raw.startsWith('https://')) {
    raw = `https://${raw}`;
  }
  return raw.endsWith('/api/v1') ? raw.replace(/\/+$/, '') : `${raw.replace(/\/+$/, '')}/api/v1`;
}

const BACKEND_API_BASE = getBackendLogUrl();

export interface TerminalLogPayload {
  level?: 'info' | 'action' | 'navigation' | 'api' | 'auth' | 'warn' | 'error';
  message: string;
  route?: string;
  details?: Record<string, any>;
}

export function logToTerminal(payload: TerminalLogPayload) {
  if (typeof window === 'undefined') return;

  const route = payload.route || window.location.pathname;
  const data = {
    level: payload.level || 'info',
    message: payload.message,
    route,
    details: payload.details,
  };

  const bodyStr = JSON.stringify(data);

  // 1. Output to browser console as well for local inspection
  const consolePrefix = `[TERMINAL-LOG]`;
  if (data.level === 'error') {
    console.error(consolePrefix, data.message, data.details || '');
  } else if (data.level === 'warn') {
    console.warn(consolePrefix, data.message, data.details || '');
  } else {
    console.log(consolePrefix, data.message, data.details || '');
  }

  // 2. Send to Next.js terminal (npm run dev console)
  try {
    fetch('/api/terminal-log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: bodyStr,
      keepalive: true,
    }).catch(() => {});
  } catch {}

  // 3. Send to FastAPI backend terminal (uvicorn console)
  try {
    fetch(`${BACKEND_API_BASE}/client-log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: bodyStr,
      keepalive: true,
    }).catch(() => {});
  } catch {}
}

export const terminalLogger = {
  action: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'action', message, details }),
  navigation: (route: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'navigation', message: `Navigated to ${route}`, route, details }),
  api: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'api', message, details }),
  auth: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'auth', message, details }),
  error: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'error', message, details }),
  warn: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'warn', message, details }),
  info: (message: string, details?: Record<string, any>) =>
    logToTerminal({ level: 'info', message, details }),
};
