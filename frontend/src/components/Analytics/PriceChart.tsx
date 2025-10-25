import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartDataPoint {
  timestamp: string;
  price: number;
}

interface PriceChartProps {
  data: ChartDataPoint[];
  coin: string;
}

const PriceChart: React.FC<PriceChartProps> = ({ data, coin }) => {
  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload && payload[0]) {
      const date = new Date(payload[0].payload.timestamp).toLocaleDateString();
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          <p className="font-semibold">{date}</p>
          <p className="text-blue-400">${payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        No data available for this time range
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="timestamp"
          stroke="#9ca3af"
          tick={{ fontSize: 12 }}
          tickFormatter={(value: string) => new Date(value).toLocaleDateString()}
        />
        <YAxis
          stroke="#9ca3af"
          tick={{ fontSize: 12 }}
          domain={['dataMin - 1000', 'dataMax + 1000']}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="price"
          stroke="#3b82f6"
          dot={false}
          activeDot={{ r: 6 }}
          name={`${coin} Price`}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default PriceChart;
