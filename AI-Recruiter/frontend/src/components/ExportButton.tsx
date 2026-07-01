import React from 'react';
import { Download } from 'lucide-react';
import { exportRankings } from '../lib/api';

export default function ExportButton() {
  return (
    <button 
      onClick={exportRankings}
      className="apple-btn-secondary flex items-center gap-2 text-sm"
      title="Export top candidates as CSV"
    >
      <Download size={16} />
      Export CSV
    </button>
  );
}
