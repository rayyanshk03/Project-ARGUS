import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export default function SearchBar({ onSearch, isLoading = false }: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto relative group">
      <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
        {isLoading ? (
          <Loader2 className="h-5 w-5 text-[var(--color-apple-text-muted)] animate-spin" />
        ) : (
          <Search className="h-5 w-5 text-[var(--color-apple-text-muted)] group-focus-within:text-[var(--color-apple-blue)] transition-colors" />
        )}
      </div>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="apple-input pl-11 py-4 text-[17px] shadow-sm bg-white"
        placeholder="Search naturally... e.g. 'Backend engineers with FastAPI open to relocation'"
        disabled={isLoading}
      />
      <button 
        type="submit" 
        className="absolute inset-y-2 right-2 px-4 bg-[var(--color-apple-bg)] text-[var(--color-apple-text)] text-sm font-medium rounded-lg hover:bg-gray-100 transition-colors"
        disabled={isLoading || !query.trim()}
      >
        Search
      </button>
    </form>
  );
}
