import React from 'react';
import { Sparkles, LineChart } from 'lucide-react';

export default function JDOptimizer() {
  return (
    <div className="dark-card mt-8 p-6 rounded-2xl border border-blue-900/30 bg-[#12161f] flex flex-col gap-4">
      <h3 className="font-bold flex items-center gap-2 text-blue-400 text-lg">
        <Sparkles size={18} /> JD Optimizer
      </h3>
      <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
        AI-powered analysis that catches bias, vague language, and missing info before you rank.
      </p>
      <div className="mt-2 flex gap-3">
        <button className="dark-btn-secondary py-2.5 px-5 text-sm flex items-center gap-2 hover:border-blue-800 hover:bg-blue-900/20">
          <LineChart size={16} /> Analyze Current JD
        </button>
      </div>
    </div>
  );
}
