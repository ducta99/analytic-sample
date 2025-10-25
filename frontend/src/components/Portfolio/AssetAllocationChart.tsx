import React from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';

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

interface AssetAllocationChartProps {
  assets: PortfolioAsset[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({ assets }) => {
  const chartData = assets.map(asset => ({
    name: asset.symbol,
    value: asset.allocation_percentage,
  }));

  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload && payload[0]) {
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          <p className="font-semibold">{payload[0].name}</p>
          <p className="text-blue-400">{payload[0].value.toFixed(2)}%</p>
        </div>
      );
    }
    return null;
  };

  if (assets.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-center">
        <p className="text-gray-400">No assets in portfolio</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Asset Allocation</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AssetAllocationChart;
