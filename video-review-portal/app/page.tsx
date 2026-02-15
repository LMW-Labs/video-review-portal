import { Video, CheckCircle, AlertCircle, Clock, ExternalLink, LogOut } from 'lucide-react';
import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import Link from 'next/link';

async function getVideos() {
  try {
    const csvPath = path.join(process.cwd(), 'data', 'videos_for_review.csv');
    if (!fs.existsSync(csvPath)) return [];
    
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
    });
    return records;
  } catch (error) {
    console.error('Error reading CSV:', error);
    return [];
  }
}

export default async function Home() {
  const videos = await getVideos();
  const pendingCount = videos.length;
  
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-10 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Video Review Portal</h1>
            <p className="text-gray-500 mt-2">Skill Position Pro Training Dataset Review</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 cursor-pointer transition">
              Sync from Drive
            </div>
            <Link href="/login" className="p-2 text-gray-400 hover:text-gray-600 transition">
              <LogOut size={20} />
            </Link>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
          <StatCard icon={<Clock className="text-blue-500" />} label="Pending Review" value={pendingCount.toString()} />
          <StatCard icon={<CheckCircle className="text-green-500" />} label="Completed" value="856" />
          <StatCard icon={<AlertCircle className="text-red-500" />} label="Flagged" value="12" />
          <StatCard icon={<Video className="text-purple-500" />} label="Total Videos" value={(pendingCount + 856).toString()} />
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex justify-between items-center">
            <h2 className="font-semibold text-gray-800">Videos for Review</h2>
            <span className="text-sm text-blue-600 hover:underline cursor-pointer font-medium">Download CSV</span>
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
                {videos.slice(0, 15).map((video: any, i: number) => (
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
          {videos.length > 15 && (
            <div className="p-4 text-center border-t border-gray-100 text-gray-500 text-sm">
              Showing first 15 of {videos.length} videos
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
