import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ExchangeComparisonProps {
  coinId: string;
}

interface ExchangePrice {
  exchange: string;
  price: number;
  premium: number;
}

const ExchangeComparison: React.FC<ExchangeComparisonProps> = ({ coinId }) => {
  const [exchangePrices, setExchangePrices] = useState<ExchangePrice[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExchangePrices();
  }, [coinId]);

  const loadExchangePrices = async () => {
    try {
      setLoading(true);
      // Mock data for different exchanges
      const basePrice = 45250.50;
      const mockData: ExchangePrice[] = [
        { exchange: 'Binance', price: basePrice + (Math.random() * 100 - 50), premium: 0 },
        { exchange: 'Coinbase', price: basePrice + (Math.random() * 100 - 50), premium: 0 },
        { exchange: 'Kraken', price: basePrice + (Math.random() * 100 - 50), premium: 0 },
        { exchange: 'Bitstamp', price: basePrice + (Math.random() * 100 - 50), premium: 0 },
      ];
      
      // Calculate premiums
      const minPrice = Math.min(...mockData.map(d => d.price));
      mockData.forEach(item => {
        item.premium = ((item.price - minPrice) / minPrice) * 100;
      });
      
      setExchangePrices(mockData);
    } catch (err) {
      console.error('Failed to load exchange prices:', err);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = (props: any) => {
    const { active, payload } = props;
    if (active && payload && payload[0]) {
      return (
        <div className="bg-gray-800 p-3 rounded border border-gray-700 text-white text-sm">
          <p className="font-semibold">{payload[0].payload.exchange}</p>
          <p className="text-blue-400">${payload[0].value.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  const highestPrice = Math.max(...exchangePrices.map(d => d.price));
  const lowestPrice = Math.min(...exchangePrices.map(d => d.price));
  const priceDifference = highestPrice - lowestPrice;
  const arbitrageOpportunity = (priceDifference / lowestPrice) * 100;

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Exchange Price Comparison</h3>
        
        {loading ? (
          <p className="text-gray-400">Loading exchange data...</p>
        ) : exchangePrices.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={exchangePrices}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="exchange" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="price" fill="#3b82f6" name="Price (USD)" />
              </BarChart>
            </ResponsiveContainer>

            {/* Exchange Price Details */}
            <div className="mt-6 space-y-2">
              <div className="text-sm text-gray-300">
                <p className="font-semibold text-white mb-3">Price by Exchange:</p>
                {exchangePrices.map(ex => (
                  <div key={ex.exchange} className="flex justify-between items-center py-2 border-b border-gray-700">
                    <span>{ex.exchange}</span>
                    <div className="text-right">
                      <p className="text-white font-semibold">${ex.price.toFixed(2)}</p>
                      <p className={`text-xs ${ex.premium > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {ex.premium > 0 ? '+' : ''}{ex.premium.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Arbitrage Opportunity */}
            <div className="mt-6 p-4 bg-blue-900/30 border border-blue-700 rounded">
              <p className="text-gray-400 text-sm font-medium mb-2">Arbitrage Opportunity</p>
              <p className="text-2xl font-bold text-blue-400">{arbitrageOpportunity.toFixed(3)}%</p>
              <p className="text-gray-400 text-xs mt-2">
                Difference: ${priceDifference.toFixed(2)} between lowest ({lowestPrice.toFixed(2)}) and highest ({highestPrice.toFixed(2)})
              </p>
            </div>
          </>
        ) : (
          <p className="text-gray-400">No exchange data available</p>
        )}
      </div>
    </div>
  );
};

export default ExchangeComparison;
