import React, { useState } from 'react';
import { Sparkles, LineChart } from 'lucide-react';

export default function JDOptimizer({ jd }: { jd: string }) {
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!jd) return;
    setLoading(true);
    try {
      const { analyzeJD } = await import('../lib/api');
      const res = await analyzeJD(jd);
      setAnalysis(res.suggestions);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dark-card mt-8 p-6 rounded-2xl border border-blue-900/30 bg-[#12161f] flex flex-col gap-4">
      <h3 className="font-bold flex items-center gap-2 text-blue-400 text-lg">
        <Sparkles size={18} /> JD Optimizer
      </h3>
      <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
        AI-powered analysis that catches bias, vague language, and missing info before you rank.
      </p>
      
      {!analysis && (
        <div className="mt-2 flex gap-3">
          <button 
            onClick={handleAnalyze} 
            disabled={loading || !jd}
            className="dark-btn-secondary py-2.5 px-5 text-sm flex items-center gap-2 hover:border-blue-800 hover:bg-blue-900/20 disabled:opacity-50"
          >
            {loading ? 'Analyzing...' : <><LineChart size={16} /> Analyze Current JD</>}
          </button>
        </div>
      )}

      {analysis && (
        <div className="mt-4 space-y-3">
          {analysis.map((sug: any, i: number) => (
            <div key={i} className="p-3 bg-blue-900/10 border border-blue-900/30 rounded-lg text-sm text-blue-100">
              <span className="font-bold text-blue-300 uppercase mr-2 tracking-wider text-xs">{sug.type}:</span>
              <span className="italic text-gray-400">"{sug.text}"</span>
              <div className="mt-1 font-medium text-blue-200">→ {sug.suggestion}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
