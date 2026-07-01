import React, { useState } from 'react';
import { MessageSquare, Loader2, Send } from 'lucide-react';
import { ragQuery } from '../lib/api';

export default function RAGQuery() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setAnswer(null);
    try {
      const res = await ragQuery(query);
      setAnswer(res.answer);
      setCitations(res.cited_candidate_ids || []);
    } catch (err) {
      console.error(err);
      setAnswer("Sorry, I encountered an error searching the candidate database.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="apple-card mt-6 bg-gradient-to-br from-[#ffffff] to-[#f5f5f7]">
      <div className="flex items-center gap-2 mb-4">
        <MessageSquare size={18} className="text-[var(--color-apple-blue)]" />
        <h3 className="font-semibold text-[var(--color-apple-text)]">Ask about Candidates</h3>
      </div>
      
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Which candidates have built production ML systems?"
          className="w-full pl-4 pr-12 py-3 rounded-xl border border-[var(--color-apple-border)] focus:outline-none focus:ring-2 focus:ring-[var(--color-apple-blue)] focus:border-transparent text-[15px]"
          disabled={loading}
        />
        <button 
          type="submit"
          disabled={!query.trim() || loading}
          className="absolute right-2 top-2 p-1.5 bg-[var(--color-apple-blue)] text-white rounded-lg disabled:opacity-50 transition-opacity"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </form>

      {answer && (
        <div className="mt-4 p-4 bg-white rounded-xl border border-[var(--color-apple-border)] shadow-sm">
          <p className="text-[15px] text-gray-700 leading-relaxed whitespace-pre-wrap">
            {answer}
          </p>
          
          {citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Citations:</span>
              {citations.map(cid => (
                <button 
                  key={cid} 
                  className="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs font-medium border border-blue-100 hover:bg-blue-100 transition-colors"
                  title="View Candidate"
                >
                  {cid.slice(-6)}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
