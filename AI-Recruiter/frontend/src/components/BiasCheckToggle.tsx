import React, { useState } from 'react';
import { Scale, Loader2, ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { biasCheck } from '../lib/api';

interface BiasCheckToggleProps {
  jobDescription: string;
}

export default function BiasCheckToggle({ jobDescription }: BiasCheckToggleProps) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[] | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const runCheck = async () => {
    if (!jobDescription) return;
    setLoading(true);
    try {
      const res = await biasCheck(jobDescription);
      setResults(res.bias_analysis);
      setIsOpen(true);
    } catch (err) {
      console.error(err);
      alert("Bias check failed");
    } finally {
      setLoading(false);
    }
  };

  if (!jobDescription) return null;

  return (
    <div className="mt-6 apple-card">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold flex items-center gap-2">
            <Scale size={18} className="text-purple-600" />
            Fairness & Bias Check
          </h3>
          <p className="text-sm text-[var(--color-apple-text-muted)] mt-1">
            Simulate ranking with masked identity variables to uncover hidden talent penalized by bias.
          </p>
        </div>
        <button 
          onClick={runCheck}
          disabled={loading}
          className="apple-btn-secondary"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Run Check"}
        </button>
      </div>

      {isOpen && results && (
        <div className="mt-6 pt-6 border-t border-gray-100">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-gray-400 font-medium border-b border-gray-100">
                <th className="pb-3 font-medium">Candidate</th>
                <th className="pb-3 font-medium text-center">Original Rank</th>
                <th className="pb-3 font-medium text-center">Masked Rank</th>
                <th className="pb-3 font-medium text-right">Shift</th>
              </tr>
            </thead>
            <tbody>
              {results.slice(0, 10).map((r, i) => (
                <tr key={i} className="border-b border-gray-50 last:border-0">
                  <td className="py-3 font-medium">{r.original_name}</td>
                  <td className="py-3 text-center">{r.normal_rank}</td>
                  <td className="py-3 text-center font-medium text-purple-700">{r.masked_rank}</td>
                  <td className="py-3 text-right">
                    {r.rank_shift > 0 ? (
                      <span className="inline-flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
                        <ArrowUp size={14} /> +{r.rank_shift}
                      </span>
                    ) : r.rank_shift < 0 ? (
                      <span className="inline-flex items-center gap-1 text-red-500 bg-red-50 px-2 py-1 rounded">
                        <ArrowDown size={14} /> {r.rank_shift}
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-gray-400">
                        <Minus size={14} /> 0
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-gray-400 mt-4 text-center">Showing top 10 shifts</p>
        </div>
      )}
    </div>
  );
}
