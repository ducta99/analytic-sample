'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/utils/api-client';
import PriceChart from '@/components/Analytics/PriceChart';
import CoinComparisonChart from '@/components/Analytics/CoinComparisonChart';
import TrendIndicators from '@/components/Analytics/TrendIndicators';
import ExchangeComparison from '@/components/Analytics/ExchangeComparison';

interface CoinData {
  id: string;
  name: string;
  symbol: string;
  current_price: number;
  market_cap: number;
  market_cap_rank: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  total_volume: number;
}

interface ChartDataPoint {
  timestamp: string;
  price: number;
}

type TimeRange = '1H' | '24H' | '7D' | '1M' | '3M' | '1Y';

export default function AnalyticsPage() {
  const [selectedCoin, setSelectedCoin] = useState<string>('bitcoin');
  const [timeRange, setTimeRange] = useState<TimeRange>('24H');
  const [coins, setCoins] = useState<CoinData[]>([]);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [comparisonCoins, setComparisonCoins] = useState<string[]>(['ethereum']);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Popular coins list
  const popularCoins = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'ripple', name: 'Ripple', symbol: 'XRP' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
    { id: 'dogecoin', name: 'Dogecoin', symbol: 'DOGE' },
    { id: 'litecoin', name: 'Litecoin', symbol: 'LTC' },
  ];

  // Load initial data
  useEffect(() => {
    loadCoinsData();
    loadChartData();
  }, [selectedCoin, timeRange]);

  const loadCoinsData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API calls
      const mockData: CoinData[] = popularCoins.map((coin, idx) => ({
        id: coin.id,
        name: coin.name,
        symbol: coin.symbol,
        current_price: Math.random() * 100000,
        market_cap: Math.random() * 1000000000000,
        market_cap_rank: idx + 1,
        price_change_24h: (Math.random() - 0.5) * 10000,
        price_change_percentage_24h: (Math.random() - 0.5) * 20,
        total_volume: Math.random() * 100000000000,
      }));
      setCoins(mockData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load coins data');
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async () => {
    try {
      // Generate mock historical data based on time range
      const now = new Date();
      const points: ChartDataPoint[] = [];
      let dataPoints = 24; // default for 24H

      if (timeRange === '1H') dataPoints = 12;
      else if (timeRange === '1M') dataPoints = 30;
      else if (timeRange === '3M') dataPoints = 90;
      else if (timeRange === '1Y') dataPoints = 52; // weeks
      else if (timeRange === '7D') dataPoints = 7;

      const basePrice = 45000 + Math.random() * 5000;

      for (let i = 0; i < dataPoints; i++) {
        const date = new Date(now);
        if (timeRange === '1H') date.setHours(date.getHours() - (dataPoints - i));
        else if (timeRange === '7D' || timeRange === '24H') {
          date.setDate(date.getDate() - (dataPoints - i));
        } else if (timeRange === '1M') {
          date.setDate(date.getDate() - (dataPoints - i));
        } else if (timeRange === '3M') {
          date.setDate(date.getDate() - (dataPoints - i));
        } else if (timeRange === '1Y') {
          date.setDate(date.getDate() - (dataPoints - i) * 7);
        }

        const variance = (Math.random() - 0.5) * (basePrice * 0.1);
        points.push({
          timestamp: date.toISOString(),
          price: basePrice + variance + (i * 100),
        });
      }

      setChartData(points);
    } catch (err) {
      console.error('Failed to load chart data:', err);
    }
  };

  const selectedCoinData = coins.find(c => c.id === selectedCoin);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-800/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div>
            <h1 className="text-3xl font-bold">Market Analytics</h1>
            <p className="text-gray-400 mt-1">Real-time price charts, trends, and technical indicators</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="p-4 bg-red-900/50 border border-red-600 rounded-lg text-red-300">
            {error}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Coin Selection */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Select Coin</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {popularCoins.map(coin => (
              <button
                key={coin.id}
                onClick={() => setSelectedCoin(coin.id)}
                className={`px-3 py-2 rounded transition-colors text-sm font-medium ${
                  selectedCoin === coin.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {coin.symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Selected Coin Info */}
        {selectedCoinData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <p className="text-gray-400 text-sm font-medium mb-2">Current Price</p>
              <p className="text-3xl font-bold text-white">${selectedCoinData.current_price.toFixed(2)}</p>
              <p className="text-gray-500 text-xs mt-2">Market Cap Rank #{selectedCoinData.market_cap_rank}</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <p className="text-gray-400 text-sm font-medium mb-2">24h Change</p>
              <p className={`text-3xl font-bold ${selectedCoinData.price_change_percentage_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {selectedCoinData.price_change_percentage_24h >= 0 ? '+' : ''}
                {selectedCoinData.price_change_percentage_24h.toFixed(2)}%
              </p>
              <p className={`text-gray-400 text-xs mt-2 ${selectedCoinData.price_change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${selectedCoinData.price_change_24h.toFixed(2)}
              </p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <p className="text-gray-400 text-sm font-medium mb-2">Market Cap</p>
              <p className="text-3xl font-bold text-white">${(selectedCoinData.market_cap / 1000000000).toFixed(2)}B</p>
              <p className="text-gray-500 text-xs mt-2">Billions</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <p className="text-gray-400 text-sm font-medium mb-2">24h Volume</p>
              <p className="text-3xl font-bold text-white">${(selectedCoinData.total_volume / 1000000000).toFixed(2)}B</p>
              <p className="text-gray-500 text-xs mt-2">Billions</p>
            </div>
          </div>
        )}

        {/* Price Chart with Time Range Selector */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Price Chart</h3>
            <div className="flex gap-2">
              {(['1H', '24H', '7D', '1M', '3M', '1Y'] as TimeRange[]).map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
          <PriceChart data={chartData} coin={selectedCoinData?.symbol || 'BTC'} />
        </div>

        {/* Trend Indicators */}
        <TrendIndicators coinId={selectedCoin} />

        {/* Coin Comparison */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Coin Comparison</h3>
          <div className="mb-4">
            <label className="text-gray-300 text-sm font-medium">Compare with:</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 mt-2">
              {popularCoins.filter(c => c.id !== selectedCoin).map(coin => (
                <button
                  key={coin.id}
                  onClick={() => {
                    if (comparisonCoins.includes(coin.id)) {
                      setComparisonCoins(comparisonCoins.filter(c => c !== coin.id));
                    } else {
                      setComparisonCoins([...comparisonCoins, coin.id]);
                    }
                  }}
                  className={`px-3 py-2 rounded transition-colors text-sm font-medium ${
                    comparisonCoins.includes(coin.id)
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {coin.symbol}
                </button>
              ))}
            </div>
          </div>
          {comparisonCoins.length > 0 && (
            <CoinComparisonChart selectedCoin={selectedCoin} comparisonCoins={comparisonCoins} />
          )}
        </div>

        {/* Exchange Comparison */}
        <ExchangeComparison coinId={selectedCoin} />
      </div>
    </div>
  );
}
