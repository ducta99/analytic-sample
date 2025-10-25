'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/utils/api-client';
import SentimentScoreCard from '@/components/Sentiment/SentimentScoreCard';
import SentimentTrendChart from '@/components/Sentiment/SentimentTrendChart';
import NewsFeedComponent from '@/components/Sentiment/NewsFeedComponent';
import SentimentComparison from '@/components/Sentiment/SentimentComparison';
import SocialMediaSentiment from '@/components/Sentiment/SocialMediaSentiment';

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

export default function SentimentPage() {
  const [selectedCoin, setSelectedCoin] = useState<string>('bitcoin');
  const [sentimentData, setSentimentData] = useState<SentimentData | null>(null);
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [comparisonCoins, setComparisonCoins] = useState<string[]>(['ethereum']);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'news' | 'comparison' | 'social'>('overview');

  const popularCoins = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'ripple', name: 'Ripple', symbol: 'XRP' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
  ];

  useEffect(() => {
    loadSentimentData();
    loadNewsArticles();
  }, [selectedCoin]);

  const loadSentimentData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      const mockData: SentimentData = {
        coin_id: selectedCoin,
        coin_name: popularCoins.find(c => c.id === selectedCoin)?.name || 'Unknown',
        symbol: popularCoins.find(c => c.id === selectedCoin)?.symbol || 'UNK',
        score: Math.random() * 2 - 1, // -1 to 1
        positive_percentage: Math.random() * 100,
        negative_percentage: 0,
        neutral_percentage: 0,
        updated_at: new Date().toISOString(),
        trend: Math.random() > 0.5 ? 'bullish' : 'bearish',
      };
      
      mockData.neutral_percentage = 100 - mockData.positive_percentage - mockData.negative_percentage;
      setSentimentData(mockData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sentiment data');
    } finally {
      setLoading(false);
    }
  };

  const loadNewsArticles = async () => {
    try {
      // TODO: Replace with actual API call
      const mockArticles: NewsArticle[] = [
        {
          id: '1',
          title: `${selectedCoin} reaches new milestone in adoption`,
          source: 'CryptoNews',
          url: '#',
          published_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
          sentiment: 'positive',
          sentiment_score: 0.85,
          summary: 'Market sentiment remains positive as more institutions adopt cryptocurrency.',
        },
        {
          id: '2',
          title: `${selectedCoin} volatility continues amid market uncertainty`,
          source: 'BlockchainDaily',
          url: '#',
          published_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
          sentiment: 'neutral',
          sentiment_score: 0.1,
          summary: 'Traders remain cautious as regulatory updates emerge.',
        },
        {
          id: '3',
          title: `Market downturn affects ${selectedCoin} trading volume`,
          source: 'CryptoInsider',
          url: '#',
          published_at: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
          sentiment: 'negative',
          sentiment_score: -0.65,
          summary: 'Market-wide selloff leads to decreased trading activity.',
        },
      ];
      setNewsArticles(mockArticles);
    } catch (err) {
      console.error('Failed to load news articles:', err);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-400';
      case 'negative':
        return 'text-red-400';
      default:
        return 'text-yellow-400';
    }
  };

  const getSentimentBgColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-900/30 border-green-700';
      case 'negative':
        return 'bg-red-900/30 border-red-700';
      default:
        return 'bg-yellow-900/30 border-yellow-700';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading sentiment data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-800/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div>
            <h1 className="text-3xl font-bold">Sentiment Analysis</h1>
            <p className="text-gray-400 mt-1">Market sentiment, news feed, and social media trends</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="p-4 bg-red-900/50 border border-red-600 rounded-lg text-red-300">
            {error}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Coin Selection */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Select Coin</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
            {popularCoins.map(coin => (
              <button
                key={coin.id}
                onClick={() => setSelectedCoin(coin.id)}
                className={`px-3 py-2 rounded transition-colors text-sm font-medium ${
                  selectedCoin === coin.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {coin.symbol}
              </button>
            ))}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-4 border-b border-gray-800 overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'overview'
                ? 'border-blue-600 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`px-4 py-2 border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'news'
                ? 'border-blue-600 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            News Feed
          </button>
          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-4 py-2 border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'comparison'
                ? 'border-blue-600 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Comparison
          </button>
          <button
            onClick={() => setActiveTab('social')}
            className={`px-4 py-2 border-b-2 transition-colors whitespace-nowrap ${
              activeTab === 'social'
                ? 'border-blue-600 text-white'
                : 'border-transparent text-gray-400 hover:text-gray-300'
            }`}
          >
            Social Media
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && sentimentData && (
          <div className="space-y-6">
            <SentimentScoreCard sentiment={sentimentData} />
            <SentimentTrendChart coinId={selectedCoin} />
          </div>
        )}

        {activeTab === 'news' && (
          <NewsFeedComponent articles={newsArticles} />
        )}

        {activeTab === 'comparison' && (
          <SentimentComparison selectedCoin={selectedCoin} comparisonCoins={comparisonCoins} />
        )}

        {activeTab === 'social' && (
          <SocialMediaSentiment coinId={selectedCoin} />
        )}
      </div>
    </div>
  );
}
