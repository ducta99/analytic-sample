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

interface PortfolioOverviewProps {
  portfolio: Portfolio;
}

const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ portfolio }) => {
  const gainLossColor = portfolio.gain_loss >= 0 ? 'text-green-400' : 'text-red-400';
  const gainLossBgColor = portfolio.gain_loss >= 0 ? 'bg-green-900/30' : 'bg-red-900/30';
  const gainLossBorderColor = portfolio.gain_loss >= 0 ? 'border-green-700' : 'border-red-700';

  const roiColor = portfolio.roi_percentage >= 0 ? 'text-green-400' : 'text-red-400';
  const roiBgColor = portfolio.roi_percentage >= 0 ? 'bg-green-900/30' : 'bg-red-900/30';
  const roiBorderColor = portfolio.roi_percentage >= 0 ? 'border-green-700' : 'border-red-700';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Value */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400 text-sm font-medium mb-2">Total Portfolio Value</p>
        <p className="text-3xl font-bold text-white">${portfolio.total_value.toFixed(2)}</p>
        <p className="text-gray-500 text-xs mt-2">Portfolio Size</p>
      </div>

      {/* Total Cost */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400 text-sm font-medium mb-2">Total Cost</p>
        <p className="text-3xl font-bold text-white">${portfolio.total_cost.toFixed(2)}</p>
        <p className="text-gray-500 text-xs mt-2">Amount Invested</p>
      </div>

      {/* Gain/Loss */}
      <div className={`${gainLossBgColor} rounded-lg p-6 border ${gainLossBorderColor}`}>
        <p className="text-gray-400 text-sm font-medium mb-2">Gain / Loss</p>
        <p className={`text-3xl font-bold ${gainLossColor}`}>
          ${portfolio.gain_loss.toFixed(2)}
        </p>
        <p className="text-gray-500 text-xs mt-2">Total Return</p>
      </div>

      {/* ROI Percentage */}
      <div className={`${roiBgColor} rounded-lg p-6 border ${roiBorderColor}`}>
        <p className="text-gray-400 text-sm font-medium mb-2">Return on Investment</p>
        <p className={`text-3xl font-bold ${roiColor}`}>
          {portfolio.roi_percentage.toFixed(2)}%
        </p>
        <p className="text-gray-500 text-xs mt-2">ROI</p>
      </div>
    </div>
  );
};

export default PortfolioOverview;
