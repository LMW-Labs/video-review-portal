import fs from 'fs';
import path from 'path';
import { parse } from 'csv-parse/sync';
import Dashboard from '@/components/Dashboard';

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
  
  return (
    <main className="min-h-screen bg-gray-50 p-8 relative overflow-hidden">
      {/* Background Watermark */}
      <div className="fixed inset-0 flex items-center justify-center pointer-events-none z-0 opacity-[0.03]">
        <img src="/logo.png" alt="" className="w-[600px] h-auto grayscale" />
      </div>

      <div className="relative z-10">
        <Dashboard initialVideos={reviewVideos} initialAllVideos={allVideos} />
      </div>
    </main>
  );
}
