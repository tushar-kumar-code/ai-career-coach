import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Career Coach | Personal Career Guidance Platform',
  description: 'AI-powered personal career coach for career discovery, digital twin tracking, skill gap analysis, personalized roadmaps, resume ATS tailoring, and mock interviews.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
