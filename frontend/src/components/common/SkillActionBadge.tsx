'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Dumbbell, MapPin, Check, Plus, Loader2, ArrowRight } from 'lucide-react';
import { createRoadmapSkillRequest } from '@/lib/api-client';

interface SkillActionBadgeProps {
  skillName: string;
  priority?: string;
  source?: string;
  variant?: 'pill' | 'row';
  onAdded?: (skillName: string, message: string) => void;
}

export default function SkillActionBadge({
  skillName,
  priority,
  source = 'Skill Matrix',
  variant = 'pill',
  onAdded,
}: SkillActionBadgeProps) {
  const [addingToRoadmap, setAddingToRoadmap] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddToRoadmap = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (addingToRoadmap || added) return;

    setAddingToRoadmap(true);
    setError(null);
    try {
      const res = await createRoadmapSkillRequest(skillName, source, priority || 'Medium');
      setAdded(true);
      if (onAdded) {
        onAdded(
          skillName,
          res.suggested_phase_title
            ? `Request created for ${skillName}! Review and accept in ${res.suggested_phase_title} in Roadmap.`
            : `Request for ${skillName} sent to Roadmap & Tasks!`
        );
      }
      setTimeout(() => setAdded(false), 8000);
    } catch (err: any) {
      console.error('Failed to create skill request for roadmap:', err);
      setError(err?.message || 'Failed to request');
      setTimeout(() => setError(null), 4000);
    } finally {
      setAddingToRoadmap(false);
    }
  };

  if (variant === 'row') {
    return (
      <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/30 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-200 text-sm">{skillName}</span>
          {priority && (
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${
                priority === 'Critical' || priority === 'High'
                  ? 'bg-red-500/10 text-red-400 border-red-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}
            >
              {priority}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {error && (
            <span className="text-[11px] text-red-400 bg-red-950/60 border border-red-800/60 px-2 py-1 rounded-lg">
              {error}
            </span>
          )}

          {added ? (
            <Link
              href="/roadmap"
              onClick={(e) => e.stopPropagation()}
              title="Click to view and accept this request in your Roadmap"
              className="px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all min-h-[38px] bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 shadow-sm"
            >
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>Requested! Review in Roadmap →</span>
            </Link>
          ) : (
            <button
              type="button"
              onClick={handleAddToRoadmap}
              disabled={addingToRoadmap}
              title={`Add ${skillName} to Roadmap`}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all min-h-[38px] bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30"
            >
              {addingToRoadmap ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              <span>{addingToRoadmap ? 'Adding...' : 'Add to Roadmap'}</span>
            </button>
          )}

          <Link
            href={`/practice?topic=${encodeURIComponent(skillName)}`}
            title={`Practice ${skillName} with AI`}
            className="px-3 py-1.5 rounded-lg bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all min-h-[38px]"
          >
            <Dumbbell className="w-3.5 h-3.5 text-violet-400" />
            <span>Practice</span>
          </Link>
        </div>
      </div>
    );
  }

  // Default 'pill' variant
  return (
    <div className="inline-flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-amber-500/20 text-xs group">
      <span className="font-semibold text-amber-300 px-2 py-0.5">{skillName}</span>

      {added ? (
        <Link
          href="/roadmap"
          onClick={(e) => e.stopPropagation()}
          title="Click to view and accept in Roadmap"
          className="px-2 py-1 rounded-lg text-[11px] font-semibold flex items-center space-x-1 transition-all bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40"
        >
          <Check className="w-3 h-3 text-emerald-400" />
          <span>Requested →</span>
        </Link>
      ) : (
        <button
          type="button"
          onClick={handleAddToRoadmap}
          disabled={addingToRoadmap}
          title={`Add ${skillName} to Roadmap`}
          className="px-2 py-1 rounded-lg text-[11px] font-semibold flex items-center space-x-1 transition-all bg-indigo-950/70 hover:bg-indigo-900 text-indigo-300 border border-indigo-500/20"
        >
          {addingToRoadmap ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <MapPin className="w-3 h-3 text-indigo-400" />
          )}
          <span>{addingToRoadmap ? 'Adding...' : '+ Roadmap'}</span>
        </button>
      )}

      <Link
        href={`/practice?topic=${encodeURIComponent(skillName)}`}
        title={`Practice ${skillName}`}
        className="px-2 py-1 rounded-lg bg-violet-950/70 hover:bg-violet-900 text-violet-300 border border-violet-500/20 text-[11px] font-semibold flex items-center space-x-1 transition-all"
      >
        <Dumbbell className="w-3 h-3 text-violet-400" />
        <span>Practice</span>
      </Link>
    </div>
  );
}
