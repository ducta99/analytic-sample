import React, { useState } from 'react';
import apiClient from '@/utils/api-client';

interface AddAssetModalProps {
  portfolioId: string;
  onClose: () => void;
  onAssetAdded: () => void;
}

const AddAssetModal: React.FC<AddAssetModalProps> = ({ portfolioId, onClose, onAssetAdded }) => {
  const [formData, setFormData] = useState({
    coin_id: '',
    quantity: '',
    purchase_price: '',
    purchase_date: new Date().toISOString().split('T')[0],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const commonCoins = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'ripple', name: 'Ripple', symbol: 'XRP' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
    { id: 'dogecoin', name: 'Dogecoin', symbol: 'DOGE' },
    { id: 'litecoin', name: 'Litecoin', symbol: 'LTC' },
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.coin_id || !formData.quantity || !formData.purchase_price) {
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // TODO: Replace with actual API call once backend endpoint exists
      // await apiClient.addPortfolioAsset(portfolioId, formData);
      
      console.log('Adding asset:', { portfolioId, ...formData });
      onAssetAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add asset');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-lg font-semibold text-white">Add Asset to Portfolio</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-900/50 border border-red-600 rounded text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* Coin Selection */}
          <div>
            <label htmlFor="coin_id" className="block text-sm font-medium text-gray-300 mb-2">
              Select Coin
            </label>
            <select
              id="coin_id"
              name="coin_id"
              value={formData.coin_id}
              onChange={handleInputChange}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
            >
              <option value="">-- Select a coin --</option>
              {commonCoins.map(coin => (
                <option key={coin.id} value={coin.id}>
                  {coin.name} ({coin.symbol})
                </option>
              ))}
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label htmlFor="quantity" className="block text-sm font-medium text-gray-300 mb-2">
              Quantity
            </label>
            <input
              type="number"
              id="quantity"
              name="quantity"
              value={formData.quantity}
              onChange={handleInputChange}
              placeholder="0.00000000"
              step="0.00000001"
              min="0"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Purchase Price */}
          <div>
            <label htmlFor="purchase_price" className="block text-sm font-medium text-gray-300 mb-2">
              Purchase Price ($)
            </label>
            <input
              type="number"
              id="purchase_price"
              name="purchase_price"
              value={formData.purchase_price}
              onChange={handleInputChange}
              placeholder="0.00"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Purchase Date */}
          <div>
            <label htmlFor="purchase_date" className="block text-sm font-medium text-gray-300 mb-2">
              Purchase Date
            </label>
            <input
              type="date"
              id="purchase_date"
              name="purchase_date"
              value={formData.purchase_date}
              onChange={handleInputChange}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded text-white transition-colors"
            >
              {loading ? 'Adding...' : 'Add Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddAssetModal;
