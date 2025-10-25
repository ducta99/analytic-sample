'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/utils/api-client';
import { useState } from 'react';

export default function Header() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    apiClient.logout();
    router.push('/auth/login');
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-blue-400">Crypto Analytics</h1>
          <p className="text-sm text-slate-400">Real-time Dashboard</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="relative">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-slate-300 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            {isOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-lg z-50 border border-slate-700">
                <Link
                  href="/profile"
                  className="block px-4 py-2 text-slate-300 hover:bg-slate-700 rounded-t-lg"
                >
                  Profile
                </Link>
                <Link
                  href="/settings"
                  className="block px-4 py-2 text-slate-300 hover:bg-slate-700"
                >
                  Settings
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-red-400 hover:bg-slate-700 rounded-b-lg"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
