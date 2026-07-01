import React, { useState } from 'react';
import { ChevronDown, ChevronUp, User, BrainCircuit, Activity, GraduationCap, Briefcase } from 'lucide-react';

interface RankedListProps {
  candidates: any[];
  onSelectCandidate: (candidate: any) => void;
}

export default function RankedList({ candidates, onSelectCandidate }: RankedListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!candidates || candidates.length === 0) return null;

  return (
    <div className="apple-card mt-6">
      <h3 className="text-lg font-semibold mb-4">Top Candidates</h3>
      <div className="flex flex-col gap-3">
        {candidates.map((cand, idx) => {
          const isExpanded = expandedId === cand.candidate_id;
          const scorePercent = Math.round((cand.final_score || 0) * 100);
          
          return (
            <div key={cand.candidate_id} className="border border-[var(--color-apple-border)] rounded-xl overflow-hidden bg-white">
              {/* Row Header */}
              <div 
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setExpandedId(isExpanded ? null : cand.candidate_id)}
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-8 text-center font-bold text-gray-400">#{idx + 1}</div>
                  
                  <div className="flex-shrink-0 w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 overflow-hidden">
                    <User size={20} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold text-[var(--color-apple-text)] truncate">{cand.name}</h4>
                      {cand.used_ml_ranker && (
                        <span className="text-[10px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">LTR</span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1 overflow-x-auto pb-1 hide-scrollbar">
                      {cand.skills?.slice(0, 4).map((skill: string) => (
                        <span key={skill} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-md whitespace-nowrap">
                          {skill}
                        </span>
                      ))}
                      {cand.missing_critical?.length > 0 && (
                        <span className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded-md border border-red-100 whitespace-nowrap">
                          Missing: {cand.missing_critical[0]}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-6 ml-4">
                  <div className="flex flex-col items-end w-24">
                    <span className="text-sm font-semibold mb-1">{scorePercent}% Match</span>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-[var(--color-apple-blue)] rounded-full transition-all duration-500" 
                        style={{ width: `${scorePercent}%` }}
                      />
                    </div>
                  </div>
                  
                  <button 
                    className="p-2 hover:bg-gray-200 rounded-full transition-colors text-gray-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectCandidate(cand);
                    }}
                    title="View Profile"
                  >
                    <User size={18} />
                  </button>
                  
                  <div className="text-gray-400">
                    {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-16 pb-5 pt-2 border-t border-gray-100 bg-gray-50">
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">AI Explanation</h5>
                      <div className="text-sm text-gray-700 space-y-1">
                        {cand.explanation ? (
                          cand.explanation.split('\n').map((line: string, i: number) => (
                            <p key={i}>{line}</p>
                          ))
                        ) : (
                          <p className="italic text-gray-400">No explanation generated.</p>
                        )}
                      </div>
                      
                      {cand.suggestion && (
                        <div className="mt-3 text-sm text-blue-700 bg-blue-50 p-2 rounded-lg border border-blue-100">
                          <strong>Tip:</strong> {cand.suggestion}
                        </div>
                      )}
                    </div>
                    
                    <div>
                      <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Score Breakdown</h5>
                      <div className="space-y-3">
                        <ScoreBar icon={<BrainCircuit size={14}/>} label="Semantic" score={cand.semantic_score} />
                        <ScoreBar icon={<Briefcase size={14}/>} label="Skills" score={cand.skill_match_score} />
                        <ScoreBar icon={<Activity size={14}/>} label="Experience" score={cand.experience_match_score} />
                        <ScoreBar icon={<GraduationCap size={14}/>} label="Education" score={cand.education_match_score} />
                        <ScoreBar icon={<User size={14}/>} label="Behavior" score={cand.behavior_score} />
                      </div>
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

function ScoreBar({ icon, label, score }: { icon: React.ReactNode, label: string, score: number }) {
  const pct = Math.round((score || 0) * 100);
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="text-gray-400 w-4 flex justify-center">{icon}</div>
      <div className="w-24 text-gray-600 font-medium">{label}</div>
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div className="h-full bg-gray-400 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <div className="w-8 text-right text-xs text-gray-500">{pct}%</div>
    </div>
  );
}
