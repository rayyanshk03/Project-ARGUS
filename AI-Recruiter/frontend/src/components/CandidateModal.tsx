import React, { useState } from 'react';
import { X, Sparkles, Loader2, Mail, MapPin, Briefcase } from 'lucide-react';
import { explainCandidate } from '../lib/api';

interface CandidateModalProps {
  candidate: any;
  onClose: () => void;
  jobDescription: string;
}

export default function CandidateModal({ candidate, onClose, jobDescription }: CandidateModalProps) {
  const [explanation, setExplanation] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleExplain = async () => {
    if (!jobDescription) {
      alert("Please paste a job description on the main page first!");
      return;
    }
    setLoading(true);
    try {
      const data = await explainCandidate(candidate._id || candidate.candidate_id, jobDescription);
      setExplanation(data);
    } catch (err) {
      console.error(err);
      alert("Failed to generate explanation.");
    } finally {
      setLoading(false);
    }
  };

  if (!candidate) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-[var(--color-apple-blue)] text-white rounded-full flex items-center justify-center text-xl font-bold">
              {candidate.name?.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-semibold">{candidate.name}</h2>
              <div className="flex items-center gap-3 text-sm text-gray-500 mt-1">
                <span className="flex items-center gap-1"><Mail size={14}/> {candidate.email || 'No email'}</span>
                <span className="flex items-center gap-1"><MapPin size={14}/> {candidate.location || 'Unknown location'}</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-700 rounded-full hover:bg-gray-100 transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto flex-1">
          
          {/* Explain Action */}
          <div className="mb-8 p-5 bg-[#f5f5f7] rounded-xl border border-gray-200">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-[var(--color-apple-text)] flex items-center gap-2">
                  <Sparkles size={16} className="text-[var(--color-apple-blue)]" />
                  AI Candidate Explanation
                </h3>
                <p className="text-sm text-gray-500 mt-1 max-w-md">
                  Generate a strict evidence-based explanation of why this candidate fits the current Job Description.
                </p>
              </div>
              <button 
                onClick={handleExplain} 
                disabled={loading}
                className="apple-btn-secondary text-sm"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate Explanation"}
              </button>
            </div>
            
            {explanation && (
              <div className="mt-4 pt-4 border-t border-gray-200 text-sm">
                <div className="font-medium text-gray-700 mb-2">Claude's Analysis:</div>
                <div className="text-gray-600 space-y-1">
                  {explanation.explanation.split('\n').map((line: string, i: number) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
                
                {explanation.skill_gap?.missing_critical?.length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg border border-red-100">
                    <strong>Critical Gaps:</strong> {explanation.skill_gap.missing_critical.join(', ')}
                  </div>
                )}
                {explanation.skill_gap?.suggestion && (
                  <div className="mt-2 text-blue-700 bg-blue-50 p-3 rounded-lg border border-blue-100">
                    <strong>Actionable Tip:</strong> {explanation.skill_gap.suggestion}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {candidate.skills?.map((skill: string) => (
                  <span key={skill} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3">Experience ({candidate.experience_years} years)</h3>
              <div className="space-y-4">
                {candidate.past_roles?.map((role: any, idx: number) => (
                  <div key={idx} className="flex gap-4">
                    <div className="mt-1 text-gray-400"><Briefcase size={18} /></div>
                    <div>
                      <h4 className="font-semibold">{role.title} at {role.company}</h4>
                      <p className="text-sm text-gray-500 mt-0.5">{role.duration_years} years</p>
                      <p className="text-sm text-gray-700 mt-2">{role.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
