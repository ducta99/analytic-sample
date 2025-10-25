import React from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, ResponsiveContainer } from 'recharts';

interface SentimentComparisonProps {
  selectedCoin: string;
  comparisonCoins: string[];
}

const SentimentComparison: React.FC<SentimentComparisonProps> = ({ selectedCoin, comparisonCoins }) => {
  const coins = [selectedCoin, ...comparisonCoins];

  // Generate mock comparison data
  const generateComparisonData = () => {
    return [
      { metric: 'Twitter Sentiment', bitcoin: 75, ethereum: 68, cardano: 55 },
      { metric: 'News Sentiment', bitcoin: 82, ethereum: 70, cardano: 60 },
      { metric: 'Reddit Activity', bitcoin: 88, ethereum: 92, cardano: 65 },
      { metric: 'Trading Volume', bitcoin: 95, ethereum: 85, cardano: 45 },
      { metric: 'Market Trend', bitcoin: 72, ethereum: 65, cardano: 58 },
      { metric: 'Community Growth', bitcoin: 78, ethereum: 80, cardano: 70 },
    ];
  };

  const data = generateComparisonData();
  const colors = ['#3b82f6', '#10b981', '#f59e0b'];

  return (
    <div className="space-y-6">
      {/* Radar Chart */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Sentiment Metrics Comparison</h3>
        <ResponsiveContainer width="100%" height={400}>
          <RadarChart data={data}>
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
            <PolarRadiusAxis stroke="#9ca3af" />
            <Radar
              name="Bitcoin"
              dataKey="bitcoin"
              stroke={colors[0]}
              fill={colors[0]}
              fillOpacity={0.25}
            />
            <Radar
              name="Ethereum"
              dataKey="ethereum"
              stroke={colors[1]}
              fill={colors[1]}
              fillOpacity={0.25}
            />
            <Radar
              name="Cardano"
              dataKey="cardano"
              stroke={colors[2]}
              fill={colors[2]}
              fillOpacity={0.25}
            />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Comparison */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Detailed Metrics</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-gray-400 font-semibold">Metric</th>
                {coins.map(coin => (
                  <th key={coin} className="text-right py-3 px-4 text-gray-400 font-semibold">
                    {coin.charAt(0).toUpperCase() + coin.slice(1)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map(row => (
                <tr key={row.metric} className="border-b border-gray-700 hover:bg-gray-700/50">
                  <td className="py-3 px-4 text-gray-300">{row.metric}</td>
                  <td className="py-3 px-4 text-right">
                    <div className="inline-block px-3 py-1 bg-blue-900/50 rounded text-blue-400">
                      {row.bitcoin}%
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="inline-block px-3 py-1 bg-green-900/50 rounded text-green-400">
                      {row.ethereum}%
                    </div>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="inline-block px-3 py-1 bg-yellow-900/50 rounded text-yellow-400">
                      {row.cardano}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SentimentComparison;
