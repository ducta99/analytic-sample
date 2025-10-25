import React from 'react';

interface SentimentData {
  coin_id: string;
  coin_name: string;
  symbol: string;
  score: number;
  positive_percentage: number;
  negative_percentage: number;
  neutral_percentage: number;
  updated_at: string;
  trend: 'bullish' | 'bearish' | 'neutral';
}

interface SentimentScoreCardProps {
  sentiment: SentimentData;
}

const SentimentScoreCard: React.FC<SentimentScoreCardProps> = ({ sentiment }) => {
  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'bullish':
        return { color: 'text-green-400', bg: 'bg-green-900/30', border: 'border-green-700' };
      case 'bearish':
        return { color: 'text-red-400', bg: 'bg-red-900/30', border: 'border-red-700' };
      default:
        return { color: 'text-yellow-400', bg: 'bg-yellow-900/30', border: 'border-yellow-700' };
    }
  };

  const trendStyle = getTrendColor(sentiment.trend);
  const scoreNormalized = (sentiment.score + 1) / 2; // Convert -1 to 1 range to 0 to 1

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Score */}
      <div className={`lg:col-span-1 ${trendStyle.bg} border ${trendStyle.border} rounded-lg p-6`}>
        <p className="text-gray-400 text-sm font-medium mb-4">Overall Sentiment Score</p>
        <div className="text-center">
          <p className={`text-5xl font-bold ${trendStyle.color}`}>
            {(sentiment.score * 100).toFixed(1)}
          </p>
          <p className={`text-sm font-semibold ${trendStyle.color} mt-2 uppercase`}>
            {sentiment.trend}
          </p>
          <p className="text-gray-400 text-xs mt-3">
            Updated {new Date(sentiment.updated_at).toLocaleString()}
          </p>
        </div>

        {/* Score Gauge */}
        <div className="mt-6">
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${trendStyle.color}`}
              style={{ width: `${Math.max(0, (scoreNormalized) * 100)}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-2">
            <span>Very Negative</span>
            <span>Neutral</span>
            <span>Very Positive</span>
          </div>
        </div>
      </div>

      {/* Sentiment Breakdown */}
      <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400 text-sm font-medium mb-4">Sentiment Breakdown</p>
        
        <div className="space-y-4">
          {/* Positive */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <p className="text-green-400 font-semibold">Positive</p>
              <p className="text-green-400 font-bold">{sentiment.positive_percentage.toFixed(1)}%</p>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-green-500 transition-all"
                style={{ width: `${sentiment.positive_percentage}%` }}
              ></div>
            </div>
          </div>

          {/* Neutral */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <p className="text-yellow-400 font-semibold">Neutral</p>
              <p className="text-yellow-400 font-bold">{sentiment.neutral_percentage.toFixed(1)}%</p>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-yellow-500 transition-all"
                style={{ width: `${sentiment.neutral_percentage}%` }}
              ></div>
            </div>
          </div>

          {/* Negative */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <p className="text-red-400 font-semibold">Negative</p>
              <p className="text-red-400 font-bold">{sentiment.negative_percentage.toFixed(1)}%</p>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-red-500 transition-all"
                style={{ width: `${sentiment.negative_percentage}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Insight */}
        <div className="mt-6 p-4 bg-gray-700/50 rounded">
          <p className="text-gray-300 text-sm">
            {sentiment.positive_percentage > 60
              ? `Market sentiment for ${sentiment.coin_name} is predominantly positive, with ${sentiment.positive_percentage.toFixed(0)}% of recent sentiment indicators showing bullish signals.`
              : sentiment.negative_percentage > 60
              ? `Market sentiment for ${sentiment.coin_name} is predominantly negative, with ${sentiment.negative_percentage.toFixed(0)}% of recent sentiment indicators showing bearish signals.`
              : `Market sentiment for ${sentiment.coin_name} is mixed, with roughly balanced positive and negative signals.`}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SentimentScoreCard;
