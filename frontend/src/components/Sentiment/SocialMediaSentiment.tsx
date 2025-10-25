import React, { useState } from 'react';

interface SocialMediaSentimentProps {
  coinId: string;
}

interface SocialMetric {
  platform: string;
  positive: number;
  negative: number;
  neutral: number;
  mentions: number;
  trend: 'up' | 'down' | 'stable';
}

const SocialMediaSentiment: React.FC<SocialMediaSentimentProps> = ({ coinId }) => {
  const [metrics] = useState<SocialMetric[]>([
    {
      platform: 'Twitter',
      positive: 68,
      negative: 18,
      neutral: 14,
      mentions: 45230,
      trend: 'up',
    },
    {
      platform: 'Reddit',
      positive: 72,
      negative: 15,
      neutral: 13,
      mentions: 12450,
      trend: 'up',
    },
    {
      platform: 'Telegram',
      positive: 65,
      negative: 20,
      neutral: 15,
      mentions: 8900,
      trend: 'stable',
    },
    {
      platform: 'Discord',
      positive: 70,
      negative: 16,
      neutral: 14,
      mentions: 6200,
      trend: 'down',
    },
  ]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return '📈';
      case 'down':
        return '📉';
      default:
        return '➡️';
    }
  };

  return (
    <div className="space-y-6">
      {/* Social Media Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map(metric => (
          <div
            key={metric.platform}
            className="bg-gray-800 rounded-lg p-6 border border-gray-700"
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-white">{metric.platform}</h4>
              <span className="text-2xl">{getTrendIcon(metric.trend)}</span>
            </div>

            <p className="text-gray-400 text-sm mb-3">Mentions: {metric.mentions.toLocaleString()}</p>

            {/* Sentiment Bars */}
            <div className="space-y-2">
              {/* Positive */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-xs text-green-400">Positive</span>
                  <span className="text-xs font-semibold text-green-400">{metric.positive}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-green-500"
                    style={{ width: `${metric.positive}%` }}
                  ></div>
                </div>
              </div>

              {/* Neutral */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-xs text-yellow-400">Neutral</span>
                  <span className="text-xs font-semibold text-yellow-400">{metric.neutral}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-yellow-500"
                    style={{ width: `${metric.neutral}%` }}
                  ></div>
                </div>
              </div>

              {/* Negative */}
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-xs text-red-400">Negative</span>
                  <span className="text-xs font-semibold text-red-400">{metric.negative}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div
                    className="h-1.5 rounded-full bg-red-500"
                    style={{ width: `${metric.negative}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Trending Topics */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Trending Topics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { topic: '#BUY', trend: 'up', mentions: 3420 },
            { topic: '#HODL', trend: 'up', mentions: 2890 },
            { topic: '#Bullish', trend: 'stable', mentions: 1560 },
            { topic: '#Adoption', trend: 'up', mentions: 1240 },
            { topic: '#FUD', trend: 'down', mentions: 890 },
            { topic: '#Resistance', trend: 'down', mentions: 670 },
          ].map(item => (
            <div
              key={item.topic}
              className="flex items-center justify-between p-4 bg-gray-700/50 rounded border border-gray-600"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{getTrendIcon(item.trend)}</span>
                <div>
                  <p className="font-semibold text-white">{item.topic}</p>
                  <p className="text-xs text-gray-400">{item.mentions} mentions</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Community Insights */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Community Insights</h3>
        <div className="space-y-3">
          <div className="p-4 bg-blue-900/30 border border-blue-700 rounded">
            <p className="text-blue-300 text-sm">
              <span className="font-semibold">Strong Community Engagement:</span> Discord and Telegram show high activity levels with consistently positive sentiment.
            </p>
          </div>
          <div className="p-4 bg-green-900/30 border border-green-700 rounded">
            <p className="text-green-300 text-sm">
              <span className="font-semibold">Bullish Trend:</span> Mentions of "#BUY" and "#HODL" are trending upward, indicating increased buying interest.
            </p>
          </div>
          <div className="p-4 bg-yellow-900/30 border border-yellow-700 rounded">
            <p className="text-yellow-300 text-sm">
              <span className="font-semibold">Notable Discussions:</span> Community members are actively discussing price targets and technical analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SocialMediaSentiment;
