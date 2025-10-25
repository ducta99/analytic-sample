'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import apiClient from '@/utils/api-client';

export default function Dashboard() {
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        setLoading(true);
        // Fetch prices for major coins
        const coins = ['bitcoin', 'ethereum', 'cardano', 'solana'];
        const pricesData: Record<string, number> = {};
        
        for (const coin of coins) {
          try {
            const response = await apiClient.getPrice(coin);
            pricesData[coin] = response.price || 0;
          } catch (err) {
            pricesData[coin] = 0;
          }
        }
        
        setPrices(pricesData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch prices');
      } finally {
        setLoading(false);
      }
    };

    fetchPrices();
    // Refresh prices every 10 seconds
    const interval = setInterval(fetchPrices, 10000);
    return () => clearInterval(interval);
  }, []);

  const coinList = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC', icon: '₿' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH', icon: '◆' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA', icon: '◈' },
    { id: 'solana', name: 'Solana', symbol: 'SOL', icon: '◎' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-2">Real-time cryptocurrency market overview</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-900 border border-red-600 rounded-lg p-4 text-red-100">
          {error}
        </div>
      )}

      {/* Main Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-slate-900 rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-slate-700 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-slate-700 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {coinList.map((coin) => (
            <Link
              key={coin.id}
              href={`/portfolio?coin=${coin.id}`}
              className="bg-slate-900 hover:bg-slate-800 rounded-lg p-6 border border-slate-800 hover:border-blue-600 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-3xl">{coin.icon}</span>
                <span className="text-sm font-semibold bg-blue-600 text-white px-2 py-1 rounded">
                  {coin.symbol}
                </span>
              </div>
              <h3 className="text-white font-semibold mb-2">{coin.name}</h3>
              <p className="text-2xl font-bold text-green-400">
                ${(prices[coin.id] || 0).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </p>
              <p className="text-slate-400 text-sm mt-2">Tap to view details</p>
            </Link>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/portfolio"
          className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg p-6 text-white transition-colors"
        >
          <div className="flex items-center gap-4">
            <span className="text-4xl">💼</span>
            <div>
              <h3 className="font-semibold">Manage Portfolio</h3>
              <p className="text-sm text-blue-100">Track your investments</p>
            </div>
          </div>
        </Link>

        <Link
          href="/analytics"
          className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 rounded-lg p-6 text-white transition-colors"
        >
          <div className="flex items-center gap-4">
            <span className="text-4xl">📈</span>
            <div>
              <h3 className="font-semibold">View Analytics</h3>
              <p className="text-sm text-purple-100">Technical analysis tools</p>
            </div>
          </div>
        </Link>
      </div>

      {/* Info Section */}
      <div className="bg-slate-900 rounded-lg p-6 border border-slate-800">
        <h2 className="text-white font-semibold mb-4">Market Statistics</h2>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-slate-400 text-sm">Total Coins</p>
            <p className="text-2xl font-bold text-white">4</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Last Updated</p>
            <p className="text-lg font-semibold text-green-400">Now</p>
          </div>
          <div>
            <p className="text-slate-400 text-sm">Status</p>
            <p className="text-lg font-semibold text-green-400">Live</p>
          </div>
        </div>
      </div>
    </div>
  );
}
