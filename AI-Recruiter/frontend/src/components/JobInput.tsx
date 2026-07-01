import React, { useState } from 'react';
import { Target, Loader2, Upload, Search, Zap } from 'lucide-react';

interface JobInputProps {
  onRank: (jd: string) => void;
  isLoading?: boolean;
}

export default function JobInput({ onRank, isLoading = false }: JobInputProps) {
  const [jd, setJd] = useState('');
  const [activeTab, setActiveTab] = useState('RANK DB');
  const [searchQuery, setSearchQuery] = useState('');

  const handleRank = () => {
    if (jd.trim()) {
      onRank(jd.trim());
    }
  };

  const tabs = ['RANK DB', 'UPLOAD FILE', 'SEARCH'];
  const quickTries = ['Senior ML Engineer', 'Product Manager', 'DevOps Lead', 'Frontend Developer'];
  const popularSearches = ['Python', 'NLP', 'Embeddings', 'Vector DB'];

  return (
    <div className="dark-card w-full flex flex-col p-0 overflow-hidden bg-[#23211e] rounded-2xl">
      <div className="p-5 pb-0">
        <div className="flex bg-[#2c2926] p-1.5 rounded-xl">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3.5 text-sm font-mono tracking-wider rounded-lg transition-colors ${
                activeTab === tab
                  ? 'bg-[#1c1a17] text-white shadow-sm'
                  : 'text-[#969188] hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>
      
      <div className="p-6 pt-6">
        {activeTab === 'RANK DB' && (
          <>
            <textarea
              className="w-full h-56 p-3 bg-transparent focus:outline-none resize-none text-base font-mono text-[#e6e2db] placeholder:text-[#6e6a64]"
              placeholder="Paste your job description here, including requirements, responsibilities, and required skills..."
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              disabled={isLoading}
            />
            
            <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-sm text-[#969188] mr-2">Quick try:</span>
                {quickTries.map((role) => (
                  <button
                    key={role}
                    onClick={() => setJd(role)}
                    className="text-sm px-3.5 py-2 bg-[#2c2926] hover:bg-[#35312c] rounded-md text-[#b4afa6] font-medium transition-colors"
                  >
                    {role}
                  </button>
                ))}
              </div>
              
              <button 
                onClick={handleRank}
                disabled={!jd.trim() || isLoading}
                className="dark-btn shrink-0 py-3 px-6 text-base"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Target className="w-5 h-5" />
                )}
                Rank Candidates
              </button>
            </div>
          </>
        )}

        {activeTab === 'UPLOAD FILE' && (
          <div className="flex flex-col gap-5">
            <div className="border border-dashed border-[#5a544a] rounded-xl p-12 flex flex-col items-center justify-center cursor-pointer hover:bg-white/5 transition-colors">
              <Upload size={32} className="text-[#a09c95] mb-5" />
              <div className="text-[#e6e2db] font-medium text-xl mb-3">Upload candidates file</div>
              <div className="text-[#8b8680] text-base">sample_candidates.json • candidates.jsonl • .json array</div>
            </div>

            <div className="border border-[#9a5633]/50 rounded-xl p-6">
              <div className="text-[#e6e2db] font-medium text-base mb-5">Scoring weights</div>
              <div className="grid grid-cols-5 text-center divide-x divide-[#35312c]">
                <div className="flex flex-col">
                  <span className="text-[#e6b464] font-bold text-xl mb-2">35%</span>
                  <span className="text-[#e6b464] text-base font-medium">Skills</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[#e6b464] font-bold text-xl mb-2">30%</span>
                  <span className="text-[#e6b464] text-base font-medium">Career</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[#e6b464] font-bold text-xl mb-2">10%</span>
                  <span className="text-[#e6b464] text-base font-medium">Exp</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[#e6b464] font-bold text-xl mb-2">10%</span>
                  <span className="text-[#e6b464] text-base font-medium">Location</span>
                </div>
                <div className="flex flex-col">
                  <span className="text-[#e6b464] font-bold text-xl mb-2">15%</span>
                  <span className="text-[#e6b464] text-base font-medium">Behavioral</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <button className="bg-[#8b4f30] hover:bg-[#a65d38] text-white/90 hover:text-white px-8 py-3.5 rounded-xl font-medium transition-colors flex items-center gap-2 text-base">
                <Zap size={20} /> Rank Candidates
              </button>
            </div>
          </div>
        )}

        {activeTab === 'SEARCH' && (
          <div className="flex flex-col gap-5 py-8">
            <div className="flex gap-5">
              <div className="relative flex-1">
                <div className="absolute left-5 top-1/2 -translate-y-1/2 text-[#8b8680]">
                  <Search size={24} />
                </div>
                <input 
                  type="text" 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search skills, titles, companies..." 
                  className="w-full bg-[#1c1a17] border border-[#35312c] rounded-xl py-4 pl-14 pr-5 text-[#e6e2db] text-xl focus:outline-none focus:border-[#5a544a]"
                />
              </div>
              <button className="bg-[#8b4f30] hover:bg-[#a65d38] text-white px-10 font-medium rounded-xl transition-colors text-xl">
                Search
              </button>
            </div>
            
            <div className="flex items-center gap-4 mt-4">
              <span className="text-base text-[#8b8680]">Popular:</span>
              {popularSearches.map((term) => (
                <button
                  key={term}
                  onClick={() => setSearchQuery(term)}
                  className="text-base px-4 py-2 bg-[#1c1a17] border border-[#35312c] hover:border-[#5a544a] hover:bg-[#2a2724] rounded-lg text-[#e6e2db] font-medium transition-all"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
