import React, { useState, useEffect } from 'react';
import { Search, Filter, Plus, Trash2, X } from 'lucide-react';
import { searchCandidates } from '../lib/api';

export default function CandidatesView() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Optional: load some defaults
  useEffect(() => {
    handleSearch('');
  }, []);

  const handleSearch = async (queryToSearch = searchQuery) => {
    setLoading(true);
    try {
      // Just query anything to get the top 20 candidates if empty
      const res = await searchCandidates(queryToSearch || "engineer", 20);
      setCandidates(res.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full px-8 md:px-12 mt-14 animate-in fade-in duration-300">
      <div className="flex justify-between items-start mb-10">
        <div>
          <h2 className="text-4xl font-serif font-bold text-[#e6e2db] mb-3">Talent Pool</h2>
          <p className="text-[#8b8680] text-xl">View, search, and manage all your candidates.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="dark-btn text-base py-3 px-6"
        >
          <Plus size={18} /> Add Candidate
        </button>
      </div>

      <div className="flex gap-4 items-center mb-10">
        <div className="relative flex-1 max-w-2xl flex">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8b8680]">
            <Search size={20} />
          </div>
          <input 
            type="text" 
            placeholder="Search by name, skills, title..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full bg-[#1c1a17] border border-[#35312c] rounded-l-lg py-3.5 pl-12 pr-4 text-lg text-[#e6e2db] focus:outline-none focus:border-[#5a544a]"
          />
          <button 
            onClick={() => handleSearch()}
            className="bg-[#9a5633] hover:bg-[#b0623a] text-white px-8 text-lg font-medium rounded-r-lg transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        <div className="flex-1" />
        <button className="dark-btn-secondary py-3.5 px-6 text-lg">
          <Filter size={18} /> Filter
        </button>
      </div>

      <div className="overflow-x-auto pb-24">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[#35312c] text-[#8b8680] text-base">
              <th className="py-5 font-medium">Candidate</th>
              <th className="py-5 font-medium">Experience</th>
              <th className="py-5 font-medium">Skills</th>
              <th className="py-5 font-medium">Status</th>
              <th className="py-5 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="text-base">
            {candidates.map((cand, idx) => (
              <tr key={cand.candidate_id || idx} className="border-b border-[#35312c]/50 hover:bg-white/5 transition-colors group">
                <td className="py-5 pr-4">
                  <div className="font-semibold text-lg text-[#e6e2db]">{cand.name || 'Unknown Name'}</div>
                  <div className="text-sm text-[#8b8680] mt-1">{cand.title || 'Unknown Title'}</div>
                </td>
                <td className="py-5 text-[#e6e2db]">{cand.experience_years} yrs</td>
                <td className="py-5">
                  <div className="flex flex-wrap gap-2">
                    {(cand.skills || []).slice(0, 4).map((skill: any, sIdx: number) => (
                      <span key={sIdx} className="bg-[#2a2724] text-[#a09c95] px-2.5 py-1.5 rounded-md text-sm">
                        {typeof skill === 'string' ? skill : skill.name}
                      </span>
                    ))}
                    {(cand.skills?.length > 4) && (
                      <span className="bg-[#2a2724] text-[#a09c95] px-2.5 py-1.5 rounded-md text-sm">
                        +{cand.skills.length - 4}
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-5">
                  <span className="text-green-500 border border-green-500/20 px-2.5 py-1.5 rounded-md text-sm font-medium bg-green-500/10">active</span>
                </td>
                <td className="py-5 text-right">
                  <button className="text-[#6e6a64] hover:text-white transition-colors p-2">
                    <Trash2 size={20} />
                  </button>
                </td>
              </tr>
            ))}
            {candidates.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="py-10 text-center text-[#8b8680]">No candidates found. Try a different search.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1c1a17] border border-[#35312c] rounded-xl w-full max-w-lg shadow-2xl p-8">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-2xl font-serif font-bold text-white">Add New Candidate</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-[#8b8680] hover:text-white transition-colors">
                <X size={24} />
              </button>
            </div>
            
            <div className="space-y-6 mb-8">
              <div>
                <label className="block text-base font-medium text-[#e6e2db] mb-2">Name</label>
                <input 
                  type="text" 
                  placeholder="Jane Doe" 
                  className="w-full bg-transparent border border-[#9a5633] rounded-lg py-3 px-4 text-lg text-white focus:outline-none focus:ring-1 focus:ring-[#9a5633]"
                />
              </div>
              <div>
                <label className="block text-base font-medium text-[#e6e2db] mb-2">Title</label>
                <input 
                  type="text" 
                  placeholder="Software Engineer" 
                  className="w-full bg-[#1c1a17] border border-[#35312c] rounded-lg py-3 px-4 text-lg text-white focus:outline-none focus:border-[#9a5633]"
                />
              </div>
            </div>
            
            <button 
              className="w-full dark-btn py-4 text-lg justify-center font-semibold rounded-lg"
              onClick={() => setIsModalOpen(false)}
            >
              Save Candidate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
