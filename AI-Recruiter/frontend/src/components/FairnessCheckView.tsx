import React, { useState, useEffect } from 'react';
import { ShieldCheck, ArrowUpRight, ArrowDownRight, Minus, Loader2 } from 'lucide-react';
import { biasCheck } from '../lib/api';

interface FairnessCheckViewProps {
  onGoHome: () => void;
  activeJobDesc: string;
}

export default function FairnessCheckView({ onGoHome, activeJobDesc }: FairnessCheckViewProps) {
  const [loading, setLoading] = useState(false);
  const [biasData, setBiasData] = useState<any[]>([]);

  useEffect(() => {
    if (activeJobDesc) {
      runBiasCheck();
    }
  }, [activeJobDesc]);

  const runBiasCheck = async () => {
    setLoading(true);
    try {
      const res = await biasCheck(activeJobDesc);
      setBiasData(res.bias_analysis || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (!activeJobDesc) {
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

  return (
    <div className="w-full px-8 md:px-12 mt-14 animate-in fade-in duration-300">
      <div className="mb-10 flex justify-between items-start">
        <div>
          <h2 className="text-4xl font-serif font-bold text-[#e6e2db] mb-2">Fairness & Bias Check</h2>
          <p className="text-[#8b8680] text-xl">
            Comparing standard ranking vs identity-masked ranking to uncover systemic bias.
          </p>
        </div>
        <button 
          onClick={runBiasCheck}
          disabled={loading}
          className="dark-btn text-base py-3 px-6 flex items-center gap-2"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
          {loading ? 'Analyzing...' : 'Re-run Analysis'}
        </button>
      </div>

      {loading ? (
        <div className="w-full py-32 flex flex-col items-center justify-center">
          <Loader2 size={40} className="animate-spin text-[#d97743] mb-4" />
          <div className="text-[#e6e2db] text-xl">Running masked identity simulation...</div>
        </div>
      ) : (
        <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#35312c] text-[#8b8680] text-base bg-[#2a2724]">
                <th className="py-5 px-6 font-medium">Candidate</th>
                <th className="py-5 font-medium">Standard Rank</th>
                <th className="py-5 font-medium">Masked Rank</th>
                <th className="py-5 font-medium">Shift (Uncovered Talent)</th>
              </tr>
            </thead>
            <tbody className="text-base">
              {biasData.map((cand, idx) => (
                <tr key={cand.candidate_id || idx} className="border-b border-[#35312c]/50 hover:bg-white/5 transition-colors">
                  <td className="py-5 px-6 font-medium text-[#e6e2db]">
                    {cand.original_name}
                  </td>
                  <td className="py-5 text-[#8b8680]">
                    #{cand.normal_rank}
                  </td>
                  <td className="py-5 text-[#e6e2db] font-bold">
                    #{cand.masked_rank}
                  </td>
                  <td className="py-5">
                    {cand.rank_shift > 0 ? (
                      <span className="flex items-center gap-1.5 text-green-500 font-medium bg-green-500/10 px-3 py-1.5 rounded-full w-fit">
                        <ArrowUpRight size={16} /> +{cand.rank_shift} spots
                      </span>
                    ) : cand.rank_shift < 0 ? (
                      <span className="flex items-center gap-1.5 text-red-500 font-medium bg-red-500/10 px-3 py-1.5 rounded-full w-fit">
                        <ArrowDownRight size={16} /> {cand.rank_shift} spots
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-[#8b8680] font-medium bg-[#2a2724] px-3 py-1.5 rounded-full w-fit">
                        <Minus size={16} /> Unchanged
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {biasData.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-10 text-center text-[#8b8680]">No data available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
