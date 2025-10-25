'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Portfolio', href: '/portfolio', icon: '💼' },
  { name: 'Analytics', href: '/analytics', icon: '📈' },
  { name: 'Sentiment', href: '/sentiment', icon: '💭' },
  { name: 'Watchlist', href: '/watchlist', icon: '👁️' },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 min-h-screen">
      <div className="p-6">
        <h2 className="text-xl font-bold text-blue-400">Crypto Dashboard</h2>
      </div>

      <nav className="px-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="absolute bottom-6 left-4 right-4 text-xs text-slate-400 text-center">
        <p>v1.0.0</p>
      </div>
    </aside>
  );
}
