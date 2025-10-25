import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PortfolioAsset {
  id: string;
  coin_id: string;
  coin_name: string;
  symbol: string;
  quantity: number;
  purchase_price: number;
  current_price: number;
  purchase_date: string;
  gain_loss: number;
  gain_loss_percentage: number;
  current_value: number;
  allocation_percentage: number;
}

interface Portfolio {
  id: string;
  name: string;
  created_at: string;
  total_value: number;
  total_cost: number;
  gain_loss: number;
  roi_percentage: number;
  assets: PortfolioAsset[];
}

interface PortfolioPerformance {
  daily_change: number;
  weekly_change: number;
  monthly_change: number;
  best_performing_asset: {
    symbol: string;
    gain_percentage: number;
  };
  worst_performing_asset: {
    symbol: string;
    loss_percentage: number;
  };
}

interface PerformanceAnalyticsProps {
  portfolio: Portfolio;
  performance: PortfolioPerformance;
}

const PerformanceAnalytics: React.FC<PerformanceAnalyticsProps> = ({ portfolio, performance }) => {
  // Mock historical data for performance chart
  const performanceData = [
    { name: 'Day 1', value: portfolio.total_cost },
    { name: 'Day 2', value: portfolio.total_cost * 1.02 },
    { name: 'Day 3', value: portfolio.total_cost * 1.01 },
    { name: 'Day 4', value: portfolio.total_cost * 1.05 },
    { name: 'Day 5', value: portfolio.total_cost * 1.03 },
    { name: 'Day 6', value: portfolio.total_cost * 1.08 },
    { name: 'Day 7', value: portfolio.total_value },
  ];

  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload && payload[0]) {
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          <p className="font-semibold">{payload[0].payload.name}</p>
          <p className="text-blue-400">${payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Performance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className={`bg-gray-800 rounded-lg p-6 border ${
          performance.daily_change >= 0 ? 'border-green-700' : 'border-red-700'
        }`}>
          <p className="text-gray-400 text-sm font-medium mb-2">Daily Change</p>
          <p className={`text-2xl font-bold ${performance.daily_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {performance.daily_change >= 0 ? '+' : ''}{performance.daily_change.toFixed(2)}%
          </p>
        </div>

        <div className={`bg-gray-800 rounded-lg p-6 border ${
          performance.weekly_change >= 0 ? 'border-green-700' : 'border-red-700'
        }`}>
          <p className="text-gray-400 text-sm font-medium mb-2">Weekly Change</p>
          <p className={`text-2xl font-bold ${performance.weekly_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {performance.weekly_change >= 0 ? '+' : ''}{performance.weekly_change.toFixed(2)}%
          </p>
        </div>

        <div className={`bg-gray-800 rounded-lg p-6 border ${
          performance.monthly_change >= 0 ? 'border-green-700' : 'border-red-700'
        }`}>
          <p className="text-gray-400 text-sm font-medium mb-2">Monthly Change</p>
          <p className={`text-2xl font-bold ${performance.monthly_change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {performance.monthly_change >= 0 ? '+' : ''}{performance.monthly_change.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Portfolio Value Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#3b82f6"
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Portfolio Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Best/Worst Performers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-green-900/30 rounded-lg p-6 border border-green-700">
          <p className="text-gray-400 text-sm font-medium mb-4">Best Performing Asset</p>
          <p className="text-2xl font-bold text-green-400">{performance.best_performing_asset.symbol}</p>
          <p className="text-green-300 mt-2">
            +{performance.best_performing_asset.gain_percentage.toFixed(2)}%
          </p>
        </div>

        <div className="bg-red-900/30 rounded-lg p-6 border border-red-700">
          <p className="text-gray-400 text-sm font-medium mb-4">Worst Performing Asset</p>
          <p className="text-2xl font-bold text-red-400">{performance.worst_performing_asset.symbol}</p>
          <p className="text-red-300 mt-2">
            {performance.worst_performing_asset.loss_percentage.toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Asset Performance */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Asset Performance Details</h3>
        <div className="space-y-3">
          {portfolio.assets.map(asset => (
            <div key={asset.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div>
                <p className="font-semibold text-white">{asset.symbol}</p>
                <p className="text-sm text-gray-400">{asset.coin_name}</p>
              </div>
              <div className={`text-right font-semibold ${
                asset.gain_loss_percentage >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                <p>{asset.gain_loss_percentage.toFixed(2)}%</p>
                <p className="text-sm text-gray-400">${asset.gain_loss.toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PerformanceAnalytics;
