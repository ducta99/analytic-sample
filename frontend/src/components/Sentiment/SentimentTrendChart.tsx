import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SentimentTrendChartProps {
  coinId: string;
}

const SentimentTrendChart: React.FC<SentimentTrendChartProps> = ({ coinId }) => {
  // Generate mock sentiment data over time
  const generateTrendData = () => {
    const data = [];
    for (let i = 30; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toLocaleDateString(),
        sentiment: Math.random() * 2 - 1, // -1 to 1
        positive: Math.random() * 100,
        negative: Math.random() * 100,
      });
    }
    return data;
  };

  const data = generateTrendData();

  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload && payload[0]) {
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          <p className="font-semibold">{payload[0].payload.date}</p>
          <p className="text-blue-400">Score: {payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">Sentiment Trend (30 Days)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <YAxis stroke="#9ca3af" />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="sentiment"
            stroke="#3b82f6"
            dot={false}
            name="Sentiment Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SentimentTrendChart;
