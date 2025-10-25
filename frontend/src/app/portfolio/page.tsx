'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import apiClient from '@/utils/api-client';
import PortfolioOverview from '@/components/Portfolio/PortfolioOverview';
import AssetAllocationChart from '@/components/Portfolio/AssetAllocationChart';
import PortfolioAssetsTable from '@/components/Portfolio/PortfolioAssetsTable';
import AddAssetModal from '@/components/Portfolio/AddAssetModal';
import PerformanceAnalytics from '@/components/Portfolio/PerformanceAnalytics';
import WatchlistManager from '@/components/Portfolio/WatchlistManager';

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

interface PortfolioPerformance {
  daily_change: number;
  weekly_change: number;
  monthly_change: number;
  best_performing_asset: {
    symbol: string;
    gain_percentage: number;
  };
  worst_performing_asset: {
    symbol: string;
    loss_percentage: number;
  };
}

export default function PortfolioPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [performance, setPerformance] = useState<PortfolioPerformance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddAssetModal, setShowAddAssetModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'watchlist'>('overview');

  // Load portfolios on mount
  useEffect(() => {
    loadPortfolios();
  }, []);

  // Load selected portfolio details and performance
  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioPerformance(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getPortfolios();
      
      // Handle different response formats
      let portfolioList = [];
      if (response.data?.portfolios) {
        portfolioList = response.data.portfolios;
      } else if (response.data) {
        portfolioList = Array.isArray(response.data) ? response.data : [];
      }
      
      // Ensure all portfolios have an id property
      portfolioList = portfolioList.filter((p: any) => p && p.id);
      
      setPortfolios(portfolioList);
      
      // Auto-select first portfolio
      if (portfolioList.length > 0) {
        setSelectedPortfolio(portfolioList[0]);
      }
      setError(null);
    } catch (err: any) {
      console.error('Failed to load portfolios:', err);
      const errorMsg = err.response?.data?.error?.message || err.message || 'Failed to load portfolios. Please check if services are running.';
      setError(errorMsg);
      setPortfolios([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPortfolioPerformance = async (portfolioId: string) => {
    try {
      const response = await apiClient.getPortfolioPerformance(portfolioId);
      setPerformance(response.data);
    } catch (err) {
      console.error('Failed to load performance:', err);
    }
  };

  const handleCreatePortfolio = async (name: string) => {
    try {
      const response = await apiClient.createPortfolio(name);
      setPortfolios([...portfolios, response.data]);
      setSelectedPortfolio(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create portfolio');
    }
  };

  const handleExportCSV = () => {
    if (!selectedPortfolio) return;

    const headers = ['Coin', 'Symbol', 'Quantity', 'Purchase Price', 'Current Price', 'Gain/Loss', 'Gain/Loss %', 'Value'];
    const rows = selectedPortfolio.assets.map(asset => [
      asset.coin_name,
      asset.symbol,
      asset.quantity.toFixed(8),
      asset.purchase_price.toFixed(2),
      asset.current_price.toFixed(2),
      asset.gain_loss.toFixed(2),
      asset.gain_loss_percentage.toFixed(2),
      asset.current_value.toFixed(2),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
      '',
      ['Portfolio Summary'],
      [`Total Value: $${selectedPortfolio.total_value.toFixed(2)}`],
      [`Total Cost: $${selectedPortfolio.total_cost.toFixed(2)}`],
      [`Gain/Loss: $${selectedPortfolio.gain_loss.toFixed(2)}`],
      [`ROI: ${selectedPortfolio.roi_percentage.toFixed(2)}%`],
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `portfolio-${selectedPortfolio.name}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleExportPDF = () => {
    // TODO: Implement PDF export using a library like jsPDF
    console.log('PDF export not yet implemented');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading portfolios...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-800/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Portfolio Manager</h1>
              <p className="text-gray-400 mt-1">Track and manage your cryptocurrency investments</p>
            </div>
            <button
              onClick={() => setShowAddAssetModal(true)}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              + Add Asset
            </button>
          </div>
        </div>
      </div>

      {/* Portfolio Selection */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-600 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-300">Error Loading Portfolios</h3>
                <div className="mt-2 text-sm text-red-200">{error}</div>
                <div className="mt-3">
                  <button
                    onClick={loadPortfolios}
                    className="text-sm font-medium text-red-200 hover:text-red-100 underline"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {!loading && !error && portfolios.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">No portfolios yet</p>
            <button
              onClick={() => {
                const name = prompt('Enter portfolio name:');
                if (name) handleCreatePortfolio(name);
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Create First Portfolio
            </button>
          </div>
        ) : (
          <>
            {/* Portfolio Tabs */}
            <div className="flex gap-2 mb-6 overflow-x-auto">
              {portfolios.filter(p => p && p.id).map((portfolio) => (
                <button
                  key={portfolio.id}
                  onClick={() => setSelectedPortfolio(portfolio)}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                    selectedPortfolio?.id === portfolio.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {portfolio.name || 'Unnamed Portfolio'}
                </button>
              ))}
              <button
                onClick={() => {
                  const name = prompt('Enter new portfolio name:');
                  if (name) handleCreatePortfolio(name);
                }}
                className="px-4 py-2 rounded-lg bg-gray-800 text-gray-400 hover:bg-gray-700 transition-colors"
              >
                + New Portfolio
              </button>
            </div>

            {selectedPortfolio && (
              <>
                {/* Navigation Tabs */}
                <div className="flex gap-4 mb-6 border-b border-gray-800">
                  <button
                    onClick={() => setActiveTab('overview')}
                    className={`px-4 py-2 border-b-2 transition-colors ${
                      activeTab === 'overview'
                        ? 'border-blue-600 text-white'
                        : 'border-transparent text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('analytics')}
                    className={`px-4 py-2 border-b-2 transition-colors ${
                      activeTab === 'analytics'
                        ? 'border-blue-600 text-white'
                        : 'border-transparent text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Performance Analytics
                  </button>
                  <button
                    onClick={() => setActiveTab('watchlist')}
                    className={`px-4 py-2 border-b-2 transition-colors ${
                      activeTab === 'watchlist'
                        ? 'border-blue-600 text-white'
                        : 'border-transparent text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Watchlist
                  </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    <PortfolioOverview portfolio={selectedPortfolio} />
                    
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="lg:col-span-1">
                        <AssetAllocationChart assets={selectedPortfolio.assets} />
                      </div>
                      <div className="lg:col-span-2">
                        <PortfolioAssetsTable assets={selectedPortfolio.assets} />
                      </div>
                    </div>

                    {/* Export Buttons */}
                    <div className="flex gap-4">
                      <button
                        onClick={handleExportCSV}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
                      >
                        📥 Export as CSV
                      </button>
                      <button
                        onClick={handleExportPDF}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                      >
                        📄 Export as PDF
                      </button>
                    </div>
                  </div>
                )}

                {activeTab === 'analytics' && performance && (
                  <PerformanceAnalytics portfolio={selectedPortfolio} performance={performance} />
                )}

                {activeTab === 'watchlist' && (
                  <WatchlistManager />
                )}
              </>
            )}
          </>
        )}
      </div>

      {/* Add Asset Modal */}
      {showAddAssetModal && (
        <AddAssetModal
          portfolioId={selectedPortfolio?.id || ''}
          onClose={() => setShowAddAssetModal(false)}
          onAssetAdded={() => {
            if (selectedPortfolio) {
              loadPortfolios();
            }
            setShowAddAssetModal(false);
          }}
        />
      )}
    </div>
  );
}
