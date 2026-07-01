import React from 'react';
import { ShieldCheck } from 'lucide-react';

interface FairnessCheckViewProps {
  onGoHome: () => void;
}

export default function FairnessCheckView({ onGoHome }: FairnessCheckViewProps) {
  return (
    <div className="w-full px-8 md:px-12 mt-14 animate-in fade-in duration-300">
      <div className="mb-10">
        <h2 className="text-4xl font-serif font-bold text-[#e6e2db] mb-2">Fairness & Bias Check</h2>
        <p className="text-[#8b8680] text-xl">
          Analyze your shortlisted candidates for diversity gaps and systemic bias.
        </p>
      </div>

      <div className="w-full bg-transparent border border-dashed border-[#35312c] rounded-2xl flex flex-col items-center justify-center py-32">
        <div className="w-16 h-16 rounded-full bg-[#1c1a17] flex items-center justify-center text-[#8b8680] border border-[#35312c] mb-6">
          <ShieldCheck size={32} />
        </div>
        <h3 className="text-2xl font-bold text-[#e6e2db] mb-4 tracking-tight">No active shortlist</h3>
        <p className="text-[#8b8680] text-lg max-w-md text-center mb-8">
          You need to rank candidates for a job first before running a fairness check on the results.
        </p>
        <button 
          onClick={onGoHome}
          className="bg-[#1c1a17] border border-[#35312c] text-[#e6e2db] hover:text-white hover:bg-[#2a2724] px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
    </div>
  );
}
