'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Dumbbell, MapPin, Check, Plus, Loader2 } from 'lucide-react';
import { focusSkillOnRoadmap } from '@/lib/api-client';

interface SkillActionBadgeProps {
  skillName: string;
  priority?: string;
  variant?: 'pill' | 'row';
}

export default function SkillActionBadge({
  skillName,
  priority,
  variant = 'pill',
}: SkillActionBadgeProps) {
  const [addingToRoadmap, setAddingToRoadmap] = useState(false);
  const [added, setAdded] = useState(false);

  const handleAddToRoadmap = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (addingToRoadmap || added) return;

    setAddingToRoadmap(true);
    try {
      await focusSkillOnRoadmap(skillName);
      setAdded(true);
      setTimeout(() => setAdded(false), 4000);
    } catch (err) {
      console.error('Failed to add skill to roadmap:', err);
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
          <button
            type="button"
            onClick={handleAddToRoadmap}
            disabled={addingToRoadmap || added}
            title={`Add ${skillName} to Roadmap`}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all min-h-[38px] ${
              added
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30'
            }`}
          >
            {addingToRoadmap ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : added ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <Plus className="w-3.5 h-3.5" />
            )}
            <span>{added ? 'Added to Roadmap ✓' : 'Add to Roadmap'}</span>
          </button>

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

      <button
        type="button"
        onClick={handleAddToRoadmap}
        disabled={addingToRoadmap || added}
        title={`Add ${skillName} to Roadmap`}
        className={`px-2 py-1 rounded-lg text-[11px] font-semibold flex items-center space-x-1 transition-all ${
          added
            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            : 'bg-indigo-950/70 hover:bg-indigo-900 text-indigo-300 border border-indigo-500/20'
        }`}
      >
        {addingToRoadmap ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : added ? (
          <Check className="w-3 h-3 text-emerald-400" />
        ) : (
          <MapPin className="w-3 h-3 text-indigo-400" />
        )}
        <span>{added ? 'Added ✓' : '+ Roadmap'}</span>
      </button>

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
