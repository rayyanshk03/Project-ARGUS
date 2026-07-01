import React, { useState } from 'react';
import { Search, Filter, Plus, Trash2, X } from 'lucide-react';

const mockCandidates = [
  { id: 1, name: 'Sarah Chen', title: 'Senior ML Engineer at DeepMind', experience: '7 yrs', skills: ['Python', 'TensorFlow', 'PyTorch', '+3'], status: 'active' },
  { id: 2, name: 'Priya Nair', title: 'DevOps Lead at HashiCorp', experience: '8 yrs', skills: ['Terraform', 'Kubernetes', 'Docker', '+3'], status: 'active' },
  { id: 3, name: 'James Wright', title: 'Full Stack Engineer at Vercel', experience: '4 yrs', skills: ['TypeScript', 'React', 'Node.js', '+2'], status: 'active' },
  { id: 4, name: 'Aisha Okonkwo', title: 'Data Scientist at Spotify', experience: '6 yrs', skills: ['Python', 'R', 'Machine Learning', '+3'], status: 'active' },
  { id: 5, name: 'Daniel Park', title: 'Backend Engineer at Cloudflare', experience: '5 yrs', skills: ['Go', 'Rust', 'Distributed Systems', '+3'], status: 'active' },
  { id: 6, name: 'Emily Torres', title: 'Engineering Manager at Shopify', experience: '9 yrs', skills: ['Leadership', 'React', 'Ruby on Rails', '+2'], status: 'active' },
  { id: 7, name: 'Ryan Osei', title: 'Security Engineer at Palo Alto Networks', experience: '6 yrs', skills: ['Penetration Testing', 'Python', 'AWS Security', '+2'], status: 'inactive' },
  { id: 8, name: 'Lisa Bergmann', title: 'UX Designer at Figma', experience: '5 yrs', skills: ['Figma', 'User Research', 'Prototyping', '+2'], status: 'active' },
  { id: 9, name: 'Kevin Huang', title: 'Platform Engineer at Databricks', experience: '7 yrs', skills: ['Spark', 'Delta Lake', 'Python', '+4'], status: 'active' },
  { id: 10, name: 'Rachel Kim', title: 'Frontend Engineer at Linear', experience: '3 yrs', skills: ['TypeScript', 'React', 'CSS', '+2'], status: 'active' },
];

export default function CandidatesView() {
  const [isModalOpen, setIsModalOpen] = useState(false);

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
            className="w-full bg-[#1c1a17] border border-[#35312c] rounded-l-lg py-3.5 pl-12 pr-4 text-lg text-[#e6e2db] focus:outline-none focus:border-[#5a544a]"
          />
          <button className="bg-[#9a5633] hover:bg-[#b0623a] text-white px-8 text-lg font-medium rounded-r-lg transition-colors">
            Search
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
            {mockCandidates.map((cand) => (
              <tr key={cand.id} className="border-b border-[#35312c]/50 hover:bg-white/5 transition-colors group">
                <td className="py-5 pr-4">
                  <div className="font-semibold text-lg text-[#e6e2db]">{cand.name}</div>
                  <div className="text-sm text-[#8b8680] mt-1">{cand.title}</div>
                </td>
                <td className="py-5 text-[#e6e2db]">{cand.experience}</td>
                <td className="py-5">
                  <div className="flex flex-wrap gap-2">
                    {cand.skills.map((skill, idx) => (
                      <span key={idx} className="bg-[#2a2724] text-[#a09c95] px-2.5 py-1.5 rounded-md text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-5">
                  {cand.status === 'active' ? (
                    <span className="text-green-500 border border-green-500/20 px-2.5 py-1.5 rounded-md text-sm font-medium bg-green-500/10">active</span>
                  ) : (
                    <span className="text-[#8b8680] border border-[#35312c] px-2.5 py-1.5 rounded-md text-sm font-medium bg-[#2a2724]">inactive</span>
                  )}
                </td>
                <td className="py-5 text-right">
                  <button className="text-[#6e6a64] hover:text-white transition-colors p-2">
                    <Trash2 size={20} />
                  </button>
                </td>
              </tr>
            ))}
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
