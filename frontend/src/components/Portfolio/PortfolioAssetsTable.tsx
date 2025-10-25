import React from 'react';

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

interface PortfolioAssetsTableProps {
  assets: PortfolioAsset[];
}

const PortfolioAssetsTable: React.FC<PortfolioAssetsTableProps> = ({ assets }) => {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 overflow-x-auto">
      <h3 className="text-lg font-semibold text-white mb-4">Assets</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-2 text-gray-400 font-semibold">Coin</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Quantity</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Buy Price</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Current Price</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Value</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Gain/Loss</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Gain/Loss %</th>
            <th className="text-right py-3 px-2 text-gray-400 font-semibold">Allocation</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => {
            const isPositive = asset.gain_loss >= 0;
            const gainLossColor = isPositive ? 'text-green-400' : 'text-red-400';

            return (
              <tr key={asset.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                <td className="py-3 px-2 text-white font-medium">
                  {asset.symbol}
                  <p className="text-xs text-gray-500">{asset.coin_name}</p>
                </td>
                <td className="py-3 px-2 text-right text-white">{asset.quantity.toFixed(8)}</td>
                <td className="py-3 px-2 text-right text-gray-300">${asset.purchase_price.toFixed(2)}</td>
                <td className="py-3 px-2 text-right text-gray-300">${asset.current_price.toFixed(2)}</td>
                <td className="py-3 px-2 text-right text-white font-semibold">${asset.current_value.toFixed(2)}</td>
                <td className={`py-3 px-2 text-right font-semibold ${gainLossColor}`}>
                  ${asset.gain_loss.toFixed(2)}
                </td>
                <td className={`py-3 px-2 text-right font-semibold ${gainLossColor}`}>
                  {asset.gain_loss_percentage.toFixed(2)}%
                </td>
                <td className="py-3 px-2 text-right text-gray-300">{asset.allocation_percentage.toFixed(2)}%</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {assets.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          No assets in portfolio
        </div>
      )}
    </div>
  );
};

export default PortfolioAssetsTable;
