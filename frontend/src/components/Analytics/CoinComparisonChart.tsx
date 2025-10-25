import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface CoinComparisonChartProps {
  selectedCoin: string;
  comparisonCoins: string[];
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const CoinComparisonChart: React.FC<CoinComparisonChartProps> = ({ selectedCoin, comparisonCoins }) => {
  // Mock data for comparison
  const generateMockData = () => {
    const data = [];
    for (let i = 0; i < 24; i++) {
      const point: any = { time: `${i}h` };
      point[selectedCoin] = Math.random() * 100;
      comparisonCoins.forEach(coin => {
        point[coin] = Math.random() * 100;
      });
      data.push(point);
    }
    return data;
  };

  const data = generateMockData();
  const allCoins = [selectedCoin, ...comparisonCoins];

  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload) {
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time" stroke="#9ca3af" />
        <YAxis stroke="#9ca3af" />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {allCoins.map((coin, idx) => (
          <Line
            key={coin}
            type="monotone"
            dataKey={coin}
            stroke={COLORS[idx % COLORS.length]}
            dot={false}
            name={coin.toUpperCase()}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default CoinComparisonChart;
