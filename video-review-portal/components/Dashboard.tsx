'use client';

import { useState, useEffect } from 'react';
import { Video, CheckCircle, AlertCircle, Clock, ExternalLink, Files, Check, X, Edit2, Search, Filter } from 'lucide-react';
import Header from './Header';

export default function Dashboard({ initialVideos, initialAllVideos }: { initialVideos: any[], initialAllVideos: any[] }) {
  const [videos, setVideos] = useState(initialVideos);
  const [filter, setFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [updating, setUpdating] = useState<string | null>(null);

  // Stats calculation
  const pendingCount = videos.filter(v => !v.reviewer_decision).length;
  const totalRecords = initialAllVideos.length;
  
  // Strip extension and duplicate suffixes like " (1)" to find unique videos
  const uniqueFiles = new Set(initialAllVideos.map((v: any) => {
    return v.filename.replace(/\s*\(\d+\)?(\.[^.]+)$/, '').replace(/\.[^.]+$/, '');
  }));
  const uniqueCount = uniqueFiles.size;
  const flaggedCount = videos.filter((v: any) => 
    v.issues.includes('GARBAGE_TRANSCRIPT') || v.issues.includes('NON_DRILL_CONTENT')
  ).length;

  const filteredVideos = videos.filter(v => {
    const matchesSearch = v.filename.toLowerCase().includes(searchTerm.toLowerCase());
    if (filter === 'ALL') return matchesSearch;
    if (filter === 'PENDING') return matchesSearch && !v.reviewer_decision;
    if (filter === 'FLAGGED') return matchesSearch && (v.issues.includes('GARBAGE_TRANSCRIPT') || v.issues.includes('NON_DRILL_CONTENT'));
    if (filter === 'UNIQUE') return matchesSearch; // For simplicity in this UI
    return matchesSearch;
  });

  const handleDecision = async (filename: string, decision: string, category?: string) => {
    setUpdating(filename);
    try {
      const res = await fetch('/api/videos/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, decision, category }),
      });
      if (res.ok) {
        setVideos(videos.map(v => v.filename === filename ? { ...v, reviewer_decision: decision, reviewer_category: category || v.reviewer_category } : v));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(null);
    }
  };

  const VALID_CATEGORIES = [
    "Route Running", "Footwork", "Release Moves", "Speed/Conditioning", "Agility", "Catching/Hands", "Body Control"
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <Header />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <StatCard 
          icon={<Clock className="text-blue-500" />} 
          label="Pending Review" 
          value={pendingCount.toString()} 
          onClick={() => setFilter('PENDING')}
          active={filter === 'PENDING'}
        />
        <StatCard 
          icon={<Files className="text-green-500" />} 
          label="Unique Videos" 
          value={uniqueCount.toString()} 
          onClick={() => setFilter('ALL')}
          active={filter === 'ALL'}
        />
        <StatCard 
          icon={<AlertCircle className="text-red-500" />} 
          label="Flagged Issues" 
          value={flaggedCount.toString()} 
          onClick={() => setFilter('FLAGGED')}
          active={filter === 'FLAGGED'}
        />
        <StatCard 
          icon={<Video className="text-purple-500" />} 
          label="Total Records" 
          value={totalRecords.toString()} 
          onClick={() => setFilter('ALL')}
        />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h2 className="font-semibold text-gray-800">
            {filter === 'ALL' ? 'All Videos' : filter === 'PENDING' ? 'Pending Review' : 'Flagged Videos'}
            <span className="ml-2 text-sm font-normal text-gray-400">({filteredVideos.length})</span>
          </h2>
          
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input 
                type="text" 
                placeholder="Search filenames..."
                className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none w-64"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button 
                onClick={() => setFilter('ALL')}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition"
                title="Clear Filters"
            >
                <Filter size={18} />
            </button>
          </div>
        </div>

        <div className="p-0 overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs uppercase text-gray-400 font-semibold bg-gray-50/50 border-b border-gray-100">
                <th className="px-6 py-4">Video Info</th>
                <th className="px-6 py-4">Action Required</th>
                <th className="px-6 py-4">Issues</th>
                <th className="px-6 py-4 text-center">Review Decision</th>
                <th className="px-6 py-4 text-right">Preview</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredVideos.slice(0, 50).map((video: any, i: number) => (
                <tr key={i} className={`hover:bg-gray-50 transition ${video.reviewer_decision ? 'bg-gray-50/30' : ''}`}>
                  <td className="px-6 py-4">
                    <p className="font-medium text-gray-700 truncate max-w-[200px]">{video.filename}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{video.current_category}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-[10px] font-bold uppercase ${
                      video.action === 'REMOVE' ? 'text-red-600 bg-red-50' : 
                      video.action === 'REVIEW' ? 'text-blue-600 bg-blue-50' : 
                      'text-yellow-600 bg-yellow-50'
                    }`}>
                      {video.action}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-gray-400 text-xs max-w-[150px] truncate" title={video.issues}>
                        {video.issues}
                    </p>
                  </td>
                  <td className="px-6 py-4">
                    {updating === video.filename ? (
                        <div className="flex justify-center"><Clock className="animate-spin text-blue-500 w-5 h-5" /></div>
                    ) : video.reviewer_decision ? (
                        <div className="flex items-center justify-center space-x-2 text-green-600 font-medium text-sm">
                            <CheckCircle size={16} />
                            <span>{video.reviewer_decision}</span>
                            <button onClick={() => handleDecision(video.filename, '')} className="text-gray-300 hover:text-gray-500">
                                <Edit2 size={12} />
                            </button>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center space-x-2">
                            <button 
                                onClick={() => handleDecision(video.filename, 'KEEP')}
                                className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition"
                                title="Approve Current"
                            >
                                <Check size={18} />
                            </button>
                            <button 
                                onClick={() => handleDecision(video.filename, 'REMOVE')}
                                className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition"
                                title="Remove Video"
                            >
                                <X size={18} />
                            </button>
                            <div className="relative group">
                                <button 
                                    className="p-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition"
                                    title="Recategorize"
                                >
                                    <Edit2 size={18} />
                                </button>
                                <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block bg-white shadow-xl border border-gray-100 rounded-xl p-2 z-50 w-48">
                                    <p className="text-[10px] font-bold text-gray-400 uppercase px-2 py-1">New Category</p>
                                    {VALID_CATEGORIES.map(cat => (
                                        <button 
                                            key={cat}
                                            onClick={() => handleDecision(video.filename, 'RECATEGORIZE', cat)}
                                            className="w-full text-left px-3 py-1.5 text-xs text-gray-600 hover:bg-blue-50 hover:text-blue-600 rounded-md transition"
                                        >
                                            {cat}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <a href={video.video_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 inline-block p-2 bg-blue-50 rounded-lg">
                      <ExternalLink size={18} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredVideos.length > 50 && (
          <div className="p-4 text-center border-t border-gray-100 text-gray-500 text-sm">
            Showing first 50 results. Use search to find specific videos.
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, onClick, active }: { icon: React.ReactNode, label: string, value: string, onClick?: () => void, active?: boolean }) {
  return (
    <div 
      onClick={onClick}
      className={`bg-white p-6 rounded-xl shadow-sm border transition-all cursor-pointer hover:shadow-md hover:-translate-y-1 ${
        active ? 'border-blue-500 ring-4 ring-blue-500/10' : 'border-gray-100'
      }`}
    >
      <div className="flex items-center space-x-4">
        <div className="p-3 rounded-lg bg-gray-50">{icon}</div>
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
