'use client';

import React, { useState } from 'react';
import JobInput from '../components/JobInput';
import RankedList from '../components/RankedList';
import CandidateModal from '../components/CandidateModal';
import JDOptimizer from '../components/JDOptimizer';
import CandidatesView from '../components/CandidatesView';
import RankResultsView from '../components/RankResultsView';
import AskAIView from '../components/AskAIView';
import FairnessCheckView from '../components/FairnessCheckView';
import { rankCandidates, searchCandidates } from '../lib/api';
import { Search, Users, Zap, Clock, Moon, UserPlus } from 'lucide-react';

export default function Home() {
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [activeJobDesc, setActiveJobDesc] = useState<string>('');
  const [currentJd, setCurrentJd] = useState<string>('');
  const [activeTab, setActiveTab] = useState('Dashboard');

  const handleRank = async (jd: string) => {
    setLoading(true);
    setActiveJobDesc(jd);
    try {
      const res = await rankCandidates(jd);
      setCandidates(res.results || []);
      setActiveTab('Rank Results');
    } catch (err) {
      console.error(err);
      alert("Failed to rank candidates. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const navItems = ['Dashboard', 'Candidates', 'Rank Results', 'Ask AI', 'Fairness Check'];

  const recentActivity = [
    { name: 'Michael Adams', role: 'Solutions Architect', company: 'AWS', date: '01/07/2026' },
    { name: 'Rachel Kim', role: 'Frontend Engineer', company: 'Linear', date: '01/07/2026' },
    { name: 'Kevin Huang', role: 'Platform Engineer', company: 'Databricks', date: '01/07/2026' },
    { name: 'Lisa Bergmann', role: 'UX Designer', company: 'Figma', date: '01/07/2026' },
    { name: 'Ryan Osei', role: 'Security Engineer', company: 'Palo Alto Networks', date: '01/07/2026' },
  ];

  const topSkills = ['Python', 'AWS', 'Kubernetes', 'React', 'Terraform', 'Go', 'TypeScript', 'Spark'];

  return (
    <main className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] font-sans pb-20">
      {/* Top Navigation */}
      <header className="flex items-center justify-between px-10 py-6 border-b border-[var(--color-border)] bg-[var(--color-bg)]">
        <div className="flex items-center gap-12">
          <div className="flex items-center gap-3">
            <Search className="text-[var(--color-primary)]" size={24} />
            <span className="text-2xl font-serif font-bold tracking-tight text-white">AI-Recruiter</span>
          </div>
          
          <nav className="hidden md:flex gap-2">
            {navItems.map((item) => (
              <button
                key={item}
                onClick={() => setActiveTab(item)}
                className={`px-5 py-2.5 text-base font-medium transition-colors ${
                  activeTab === item
                    ? 'bg-[var(--color-surface)] text-white rounded-md'
                    : 'text-[var(--color-text-muted)] hover:text-white'
                }`}
              >
                {item}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex items-center gap-8 text-[var(--color-text-muted)]">
          <div className="flex items-center gap-6 text-sm font-medium">
            <span className="flex items-center gap-2"><Users size={18} /> 11</span>
            <span className="flex items-center gap-2"><Zap size={18} className="text-green-500" /> 9</span>
            <span className="flex items-center gap-2"><Clock size={18} /> 6.5y</span>
          </div>
          
          <div className="flex items-center gap-2 bg-[#14291c] text-green-500 px-3 py-1.5 rounded-full text-xs font-bold tracking-wider">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            CONNECTED
          </div>

          <Moon size={22} className="cursor-pointer hover:text-white transition-colors" />
        </div>
      </header>

      {activeTab === 'Dashboard' ? (
        <div className="w-full px-10 md:px-14 mt-16 animate-in fade-in duration-300 max-w-[1600px] mx-auto">
          <h2 className="text-5xl font-serif font-bold mb-4 tracking-tight">Talent Command Center</h2>
          <p className="text-[var(--color-text-muted)] text-xl max-w-3xl mb-12">
            Precision matching engine. Rank your database, search candidates, or upload a file for instant AI-powered scoring.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Column: Inputs & Tools */}
            <div className="lg:col-span-2 flex flex-col">
              <JobInput onRank={handleRank} isLoading={loading} jd={currentJd} setJd={setCurrentJd} />
              <JDOptimizer jd={currentJd} />
            </div>

            {/* Right Column: Results / Activity */}
            <div className="lg:col-span-1">
              {candidates.length > 0 ? (
                <div className="dark-card h-full">
                  <div className="flex justify-between items-center mb-8">
                    <h2 className="text-2xl font-semibold tracking-tight text-white">
                      Talent Pool
                    </h2>
                  </div>
                  <RankedList candidates={candidates} onSelectCandidate={setSelectedCandidate} />
                </div>
              ) : (
                <div className="dark-card h-full flex flex-col p-8 rounded-2xl">
                  <h3 className="text-xl font-semibold text-white mb-8">Recent Activity</h3>
                  
                  <div className="flex-1 space-y-8">
                    {recentActivity.map((activity, i) => (
                      <div key={i} className="flex gap-5">
                        <div className="mt-1 w-10 h-10 rounded-full bg-[var(--color-surface-lighter)] flex items-center justify-center shrink-0 border border-[var(--color-border)] text-[var(--color-text-muted)]">
                          <UserPlus size={18} />
                        </div>
                        <div>
                          <p className="text-base text-gray-200 leading-snug">
                            <span className="font-semibold text-white">{activity.name}</span> added as {activity.role} at {activity.company}
                          </p>
                          <p className="text-sm text-[var(--color-text-muted)] mt-1.5">{activity.date}</p>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-10 pt-10 border-t border-[var(--color-border)]">
                    <h3 className="text-base font-semibold text-white mb-5">Top Skills in Database</h3>
                    <div className="flex flex-wrap gap-3">
                      {topSkills.map((skill) => (
                        <span key={skill} className="px-4 py-2 text-sm font-medium bg-[var(--color-surface-lighter)] text-gray-200 rounded-md border border-[var(--color-border)]">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : activeTab === 'Candidates' ? (
        <CandidatesView />
      ) : activeTab === 'Rank Results' ? (
        <RankResultsView candidates={candidates} activeJobDesc={activeJobDesc} />
      ) : activeTab === 'Ask AI' ? (
        <AskAIView />
      ) : activeTab === 'Fairness Check' ? (
        <FairnessCheckView activeJobDesc={activeJobDesc} onGoHome={() => setActiveTab('Dashboard')} />
      ) : (
        <div className="w-full px-8 mt-12 flex justify-center items-center h-64 text-[#8b8680]">
          {activeTab} view is not implemented yet.
        </div>
      )}

      {selectedCandidate && (
        <CandidateModal 
          candidate={selectedCandidate} 
          jobDescription={activeJobDesc}
          onClose={() => setSelectedCandidate(null)} 
        />
      )}
    </main>
  );
}
