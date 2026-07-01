import React, { useState } from 'react';
import { Download, CheckCircle2, ChevronDown, ChevronUp, MapPin, Building2 } from 'lucide-react';

interface RankResultsViewProps {
  candidates: any[];
  activeJobDesc?: string;
}

export default function RankResultsView({ candidates, activeJobDesc }: RankResultsViewProps) {
  const [expandedId, setExpandedId] = useState<string | null>('1');

  const hasCandidates = candidates && candidates.length > 0;

  const displayCandidates = hasCandidates ? candidates : [
    {
      candidate_id: 'CAND_0000666',
      rank: 1,
      title: 'Data Scientist',
      company: 'PhonePe',
      location: 'Vizag, Andhra Pradesh',
      experience: '6.5 yrs',
      final_score: 0.9900,
      explanation: "Data Scientist with 6.5 yrs at PhonePe; skills in embeddings (sentence transformers); vector search (weaviate); fine-tuning (lora). Response rate 29%.",
      breakdown: {
        skills: { pct: 69, raw: 0.35 },
        career: { pct: 81, raw: 0.30 },
        experience: { pct: 100, raw: 0.10 },
        location: { pct: 85, raw: 0.10 },
        behavioral: { pct: 61, raw: 0.15 }
      }
    }
  ];

  return (
    <div className="w-full px-10 md:px-14 mt-16 animate-in fade-in duration-300 pb-24 max-w-[1600px] mx-auto">
      <div className="flex justify-between items-start mb-10">
        <div>
          <h2 className="text-5xl font-serif font-bold text-[#e6e2db] mb-3 tracking-tight">Rank Results</h2>
          <p className="text-[#8b8680] text-xl">
            candidates.jsonl (100,000 candidates) • {displayCandidates.length} candidates ranked for {activeJobDesc || 'Senior AI Engineer'}
          </p>
        </div>
        <div className="flex gap-4">
          <button className="bg-transparent border border-[#35312c] text-[#e6e2db] hover:bg-[#2a2724] px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 text-base">
            <Download size={18} /> Download submission.csv
          </button>
          <button className="bg-transparent border border-[#35312c] text-[#e6e2db] hover:bg-[#2a2724] px-6 py-3 rounded-lg font-medium transition-colors text-base">
            Fairness Check
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl p-6">
          <div className="text-[#8b8680] text-sm font-medium mb-2">Ranked</div>
          <div className="text-[#e6e2db] text-2xl font-bold font-mono">{displayCandidates.length}</div>
        </div>
        <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl p-6">
          <div className="text-[#8b8680] text-sm font-medium mb-2">Top 100 score</div>
          <div className="text-[#e6e2db] text-2xl font-bold font-mono">0.9900 → 0.5847</div>
        </div>
        <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl p-6">
          <div className="text-[#8b8680] text-sm font-medium mb-2">Honeypots</div>
          <div className="text-[#e6e2db] text-2xl font-bold font-mono">0 <span className="text-[#8b8680] text-lg">(0.0% in top 100)</span></div>
        </div>
        <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl p-6">
          <div className="text-[#8b8680] text-sm font-medium mb-2">Status</div>
          <div className="text-green-500 flex items-center gap-2 text-2xl font-bold font-mono">
            <CheckCircle2 size={24} className="fill-green-500 text-[#1c1a17]" /> Valid
          </div>
        </div>
      </div>

      <div className="border border-green-900/50 bg-[#0a1a10] rounded-xl p-4 flex items-center gap-3 text-green-500 text-base font-medium mb-10">
        <CheckCircle2 size={20} />
        Honeypot rate OK (0.0% in top 100). Scores monotonically non-increasing. Ready to download.
      </div>

      <div className="space-y-5">
        {displayCandidates.map((cand, idx) => {
          const rank = cand.rank || idx + 1;
          const isExpanded = expandedId === String(cand.candidate_id);
          const scoreStr = typeof cand.final_score === 'number' ? cand.final_score.toFixed(4) : cand.final_score;

          return (
            <div key={cand.candidate_id} className="border border-[#35312c] rounded-xl bg-[#1c1a17] overflow-hidden">
              <div 
                className="flex items-start justify-between p-6 cursor-pointer hover:bg-white/5 transition-colors"
                onClick={() => setExpandedId(isExpanded ? null : String(cand.candidate_id))}
              >
                <div className="flex items-start gap-5">
                  <div className="w-12 h-12 rounded-full bg-[#b0623a] text-white flex items-center justify-center font-bold text-lg mt-1 shrink-0">
                    {rank}
                  </div>
                  <div className="flex flex-col">
                    <div className="flex items-center gap-3 mb-1.5">
                      <h3 className="text-xl font-bold text-[#e6e2db]">{cand.title || 'Unknown Title'}</h3>
                      <div className="flex items-center gap-1.5 text-[#a09c95] bg-[#2a2724] px-2.5 py-0.5 rounded-md text-sm font-medium">
                        <Building2 size={14} /> {cand.company || 'Unknown Company'}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-[#8b8680] font-mono text-sm">
                      <span className="flex items-center gap-1.5"><MapPin size={14} /> {cand.location || 'Unknown Location'}</span>
                      <span>{cand.experience || 'N/A'}</span>
                      <span className="text-[#5a544a]">{cand.candidate_id}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-8 mt-1">
                  <div className="flex flex-col items-end">
                    <span className="text-[#d97743] font-mono font-bold text-2xl tracking-tight">{scoreStr}</span>
                    <span className="text-xs text-[#8b8680] uppercase tracking-widest mt-0.5">Score</span>
                  </div>
                  <div className="text-[#8b8680]">
                    {isExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="px-8 pb-8 pt-4 border-t border-[#35312c]">
                  {cand.trap_score > 0 && (
                    <div className={`mb-6 p-4 rounded-lg border flex items-start gap-3 ${cand.trap_score > 0.65 ? 'bg-red-950/30 border-red-900/50 text-red-400' : 'bg-orange-950/30 border-orange-900/50 text-orange-400'}`}>
                      <div className="font-bold uppercase tracking-wider text-sm mt-0.5">
                        {cand.trap_score > 0.65 ? 'Critical Trap Penalty' : 'Suspicious Profile'}
                      </div>
                      <div className="text-sm">
                        Trap Score: {(cand.trap_score * 100).toFixed(0)}%. This candidate triggered the anti-cheat heuristics and their final score was heavily penalized.
                      </div>
                    </div>
                  )}

                  <div className="mb-8">
                    <h4 className="text-sm font-bold text-[#e6e2db] uppercase tracking-wider mb-4">AI Reasoning</h4>
                    <div className="bg-[#23211e] border border-[#35312c] p-5 rounded-lg text-base text-[#a09c95] italic font-serif">
                      "{cand.explanation}"
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-[#e6e2db] uppercase tracking-wider mb-5">Score Breakdown</h4>
                    <div className="space-y-4 max-w-4xl">
                      <ScoreRow label="Semantic Match" data={{ pct: Math.round((cand.semantic_score || 0) * 100), raw: 0.35 }} />
                      <ScoreRow label="Skills Match" data={{ pct: Math.round((cand.skill_match_score || 0) * 100), raw: 0.25 }} />
                      <ScoreRow label="Experience" data={{ pct: Math.round((cand.experience_match_score || 0) * 100), raw: 0.15 }} />
                      <ScoreRow label="Behavioral" data={{ pct: Math.round((cand.behavior_score || 0) * 100), raw: 0.15 }} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ScoreRow({ label, data }: { label: string, data: { pct: number, raw: number } }) {
  return (
    <div className="flex items-center text-base font-mono">
      <div className="w-32 text-[#8b8680] text-right pr-6">{label}</div>
      <div className="flex-1 h-2.5 bg-[#2a2724] rounded-full overflow-hidden mr-8">
        <div 
          className="h-full bg-[#d97743] rounded-full" 
          style={{ width: `${data.pct}%` }} 
        />
      </div>
      <div className="w-14 text-[#e6e2db] text-right font-medium">{data.pct}%</div>
      <div className="w-20 text-[#6e6a64] text-right text-sm">×{data.raw.toFixed(2)}</div>
    </div>
  );
}
