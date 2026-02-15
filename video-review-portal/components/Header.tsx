'use client';

import { LogOut, Video } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/lib/supabase';

export default function Header() {
  const router = useRouter();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push('/login');
    router.refresh();
  };

  return (
    <header className="mb-10 flex justify-between items-center">
      <div className="flex items-center space-x-3">
        <div className="bg-blue-600 p-2 rounded-lg shadow-sm">
          <Video className="text-white w-6 h-6" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Video Review Portal</h1>
          <p className="text-gray-500 text-sm">Skill Position Pro Training Dataset Review</p>
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium shadow-sm hover:bg-blue-700 cursor-pointer transition">
          Sync from Drive
        </div>
        <button 
          onClick={handleSignOut}
          className="p-2 text-gray-400 hover:text-red-600 transition"
          title="Sign Out"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}
