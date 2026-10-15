'use client';

import { useEffect, useRef, Suspense } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import { terminalLogger } from '@/lib/terminal-logger';

function RouteTrackerInner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const lastPathRef = useRef<string>('');

  // Track route changes
  useEffect(() => {
    const fullPath = searchParams?.toString() ? `${pathname}?${searchParams.toString()}` : pathname;
    if (fullPath && fullPath !== lastPathRef.current) {
      lastPathRef.current = fullPath;
      terminalLogger.navigation(fullPath);
    }
  }, [pathname, searchParams]);

  // Global listeners for client errors, unhandled rejections, and user actions
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      // Ignore routine cross-origin script error noise
      if (!event.message) return;
      terminalLogger.error(`Uncaught Client Error: ${event.message}`, {
        source: event.filename,
        line: event.lineno,
      });
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason?.message || event.reason || 'Unknown error';
      terminalLogger.error(`Unhandled Promise: ${reason}`);
    };

    const handleClick = (event: MouseEvent) => {
      const target = (event.target as HTMLElement)?.closest('button, a[data-action]');
      if (!target) return;

      const actionName =
        target.getAttribute('data-action') ||
        target.getAttribute('aria-label') ||
        target.textContent?.trim().slice(0, 40) ||
        'Button clicked';

      // Avoid spamming icon-only or trivial clicks
      if (actionName && actionName.length > 1 && !actionName.includes('undefined')) {
        terminalLogger.action(`Clicked: "${actionName}"`);
      }
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    document.addEventListener('click', handleClick, { passive: true });

    terminalLogger.info('Web application running & live terminal telemetry active');

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      document.removeEventListener('click', handleClick);
    };
  }, []);

  return null;
}

export function TerminalRouteTracker() {
  return (
    <Suspense fallback={null}>
      <RouteTrackerInner />
    </Suspense>
  );
}
