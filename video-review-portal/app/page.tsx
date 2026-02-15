import { Video, CheckCircle, AlertCircle, Clock, ExternalLink, Files } from 'lucide-react';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import Header from '@/components/Header';

async function getReviewVideos() {
  try {
    const csvPath = path.join(process.cwd(), 'data', 'videos_for_review.csv');
    if (!fs.existsSync(csvPath)) return [];
    
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    return parse(fileContent, { columns: true, skip_empty_lines: true });
  } catch (error) {
    console.error('Error reading review CSV:', error);
    return [];
  }
}

async function getCleanVideos() {
  try {
    const csvPath = path.join(process.cwd(), 'data', 'categorized_videos.csv');
    if (!fs.existsSync(csvPath)) return [];
    
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    return parse(fileContent, { columns: true, skip_empty_lines: true });
  } catch (error) {
    console.error('Error reading categorized CSV:', error);
    return [];
  }
}

export default async function Home() {
  const reviewVideos = await getReviewVideos();
  const allVideos = await getCleanVideos();
  
  const pendingCount = reviewVideos.length;
  const totalRecords = allVideos.length;
  
  // Calculate duplicates and unique counts
  const uniqueFiles = new Set(allVideos.map((v: any) => v.filename.replace(/\s*\(\d+\)$/, '')));
  const uniqueCount = uniqueFiles.size;
  
  const flaggedCount = reviewVideos.filter((v: any) => 
    v.issues.includes('GARBAGE_TRANSCRIPT') || v.issues.includes('NON_DRILL_CONTENT')
  ).length;

  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <Header />

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <StatCard icon={<Clock className="text-blue-500" />} label="Pending Review" value={pendingCount.toString()} />
          <StatCard icon={<Files className="text-green-500" />} label="Unique Videos" value={uniqueCount.toString()} />
          <StatCard icon={<AlertCircle className="text-red-500" />} label="Flagged Issues" value={flaggedCount.toString()} />
          <StatCard icon={<Video className="text-purple-500" />} label="Total Records" value={totalRecords.toString()} />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">Videos for Review</h2>
            <div className="flex space-x-2 text-sm">
                <span className="text-gray-400">Total in Drive: ~401</span>
            </div>
          </div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-xs uppercase text-gray-400 font-semibold bg-gray-50/50 border-b border-gray-100">
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4">Current Category</th>
                  <th className="px-6 py-4">Action</th>
                  <th className="px-6 py-4">Issues</th>
                  <th className="px-6 py-4 text-right">Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {reviewVideos.slice(0, 15).map((video: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 font-medium text-gray-700">{video.filename}</td>
                    <td className="px-6 py-4 text-gray-500">{video.current_category}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        video.action === 'REMOVE' ? 'text-red-600 bg-red-50' : 
                        video.action === 'REVIEW' ? 'text-blue-600 bg-blue-50' : 
                        'text-yellow-600 bg-yellow-50'
                      }`}>
                        {video.action}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm truncate max-w-xs">{video.issues}</td>
                    <td className="px-6 py-4 text-right">
                      <a href={video.video_link} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 inline-block">
                        <ExternalLink size={18} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {reviewVideos.length > 15 && (
            <div className="p-4 text-center border-t border-gray-100 text-gray-500 text-sm">
              Showing first 15 of {reviewVideos.length} videos needing review
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode, label: string, value: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
      <div className="p-3 rounded-lg bg-gray-50">{icon}</div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  );
}
