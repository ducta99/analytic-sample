import React, { useState, useEffect } from 'react';
import apiClient from '@/utils/api-client';

interface TrendIndicatorsProps {
  coinId: string;
}

interface TrendData {
  sma_20: number;
  sma_50: number;
  ema_12: number;
  ema_26: number;
  volatility_24h: number;
  rsi_14: number;
  macd: number;
}

const TrendIndicators: React.FC<TrendIndicatorsProps> = ({ coinId }) => {
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTrendData();
  }, [coinId]);

  const loadTrendData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API calls
      const mockData: TrendData = {
        sma_20: 45250.50,
        sma_50: 44800.25,
        ema_12: 45100.75,
        ema_26: 45050.25,
        volatility_24h: 2.5,
        rsi_14: 65.5,
        macd: 125.50,
      };
      setTrendData(mockData);
    } catch (err) {
      console.error('Failed to load trend data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-gray-400">Loading trend indicators...</div>;
  }

  if (!trendData) {
    return <div className="text-gray-400">No trend data available</div>;
  }

  const indicators = [
    { name: 'SMA 20', value: trendData.sma_20, unit: 'USD' },
    { name: 'SMA 50', value: trendData.sma_50, unit: 'USD' },
    { name: 'EMA 12', value: trendData.ema_12, unit: 'USD' },
    { name: 'EMA 26', value: trendData.ema_26, unit: 'USD' },
    { name: 'Volatility 24h', value: trendData.volatility_24h, unit: '%' },
    { name: 'RSI 14', value: trendData.rsi_14, unit: 'Index' },
    { name: 'MACD', value: trendData.macd, unit: 'Signal' },
  ];

  const getRSISignal = (rsi: number) => {
    if (rsi > 70) return { text: 'Overbought', color: 'text-red-400' };
    if (rsi < 30) return { text: 'Oversold', color: 'text-green-400' };
    return { text: 'Neutral', color: 'text-yellow-400' };
  };

  const rsiSignal = getRSISignal(trendData.rsi_14);

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Technical Indicators</h3>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {indicators.map((indicator) => (
          <div key={indicator.name} className="bg-gray-700/50 rounded p-4">
            <p className="text-gray-400 text-xs font-medium mb-1">{indicator.name}</p>
            <p className="text-lg font-semibold text-white">{indicator.value.toFixed(2)}</p>
            <p className="text-gray-500 text-xs mt-1">{indicator.unit}</p>
          </div>
        ))}
      </div>

      {/* RSI Signal */}
      <div className="mt-4 p-4 bg-gray-700/50 rounded">
        <p className="text-gray-400 text-xs font-medium mb-2">RSI Signal</p>
        <p className={`text-sm font-semibold ${rsiSignal.color}`}>{rsiSignal.text}</p>
        <p className="text-gray-500 text-xs mt-2">
          {trendData.rsi_14 > 70
            ? 'Price may be overextended to the upside'
            : trendData.rsi_14 < 30
            ? 'Price may be overextended to the downside'
            : 'Market is in balance'}
        </p>
      </div>

      {/* Moving Average Crossover Signal */}
      <div className="mt-4 p-4 bg-gray-700/50 rounded">
        <p className="text-gray-400 text-xs font-medium mb-2">MA Cross Signal</p>
        <p className={`text-sm font-semibold ${
          trendData.sma_20 > trendData.sma_50 ? 'text-green-400' : 'text-red-400'
        }`}>
          {trendData.sma_20 > trendData.sma_50 ? 'Bullish' : 'Bearish'}
        </p>
        <p className="text-gray-500 text-xs mt-2">
          SMA 20 is {trendData.sma_20 > trendData.sma_50 ? 'above' : 'below'} SMA 50
        </p>
      </div>
    </div>
  );
};

export default TrendIndicators;
