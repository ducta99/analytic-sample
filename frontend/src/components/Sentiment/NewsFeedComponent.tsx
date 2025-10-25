import React from 'react';

interface NewsArticle {
  id: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  summary: string;
}

interface NewsFeedComponentProps {
  articles: NewsArticle[];
}

const NewsFeedComponent: React.FC<NewsFeedComponentProps> = ({ articles }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-400 bg-green-900/30 border-green-700';
      case 'negative':
        return 'text-red-400 bg-red-900/30 border-red-700';
      default:
        return 'text-yellow-400 bg-yellow-900/30 border-yellow-700';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return '👍';
      case 'negative':
        return '👎';
      default:
        return '➖';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="space-y-4">
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Latest News & Updates</h3>
        {articles.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No news articles available</p>
        ) : (
          <div className="space-y-3">
            {articles.map(article => (
              <div
                key={article.id}
                className="p-4 bg-gray-700/50 rounded border border-gray-600 hover:bg-gray-700 transition-colors"
              >
                <div className="flex gap-4">
                  {/* Sentiment Badge */}
                  <div className={`flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center text-2xl border ${getSentimentColor(article.sentiment)}`}>
                    {getSentimentIcon(article.sentiment)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-white font-semibold hover:text-blue-400 transition-colors line-clamp-2"
                        >
                          {article.title}
                        </a>
                        <p className="text-gray-400 text-sm mt-1">{article.summary}</p>
                      </div>
                      <div className="flex-shrink-0 text-right">
                        <p className={`font-semibold ${
                          article.sentiment === 'positive'
                            ? 'text-green-400'
                            : article.sentiment === 'negative'
                            ? 'text-red-400'
                            : 'text-yellow-400'
                        }`}>
                          {(article.sentiment_score * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between mt-3">
                      <p className="text-xs text-gray-500">{article.source}</p>
                      <p className="text-xs text-gray-500">{formatDate(article.published_at)}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsFeedComponent;
