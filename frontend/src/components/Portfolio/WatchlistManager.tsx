import React, { useState } from 'react';

interface WatchlistItem {
  id: string;
  coin_id: string;
  coin_name: string;
  symbol: string;
  current_price: number;
  price_change_24h: number;
  added_at: string;
}

const WatchlistManager: React.FC = () => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([
    {
      id: '1',
      coin_id: 'bitcoin',
      coin_name: 'Bitcoin',
      symbol: 'BTC',
      current_price: 45250.50,
      price_change_24h: 2.5,
      added_at: new Date().toISOString(),
    },
    {
      id: '2',
      coin_id: 'ethereum',
      coin_name: 'Ethereum',
      symbol: 'ETH',
      current_price: 2850.75,
      price_change_24h: -1.2,
      added_at: new Date().toISOString(),
    },
  ]);

  const [newCoin, setNewCoin] = useState('');

  const commonCoins = [
    { id: 'bitcoin', name: 'Bitcoin', symbol: 'BTC' },
    { id: 'ethereum', name: 'Ethereum', symbol: 'ETH' },
    { id: 'cardano', name: 'Cardano', symbol: 'ADA' },
    { id: 'solana', name: 'Solana', symbol: 'SOL' },
    { id: 'ripple', name: 'Ripple', symbol: 'XRP' },
    { id: 'polkadot', name: 'Polkadot', symbol: 'DOT' },
  ];

  const handleAddToWatchlist = (coinId: string) => {
    const coin = commonCoins.find(c => c.id === coinId);
    if (coin && !watchlist.some(w => w.coin_id === coinId)) {
      setWatchlist([...watchlist, {
        id: Date.now().toString(),
        coin_id: coinId,
        coin_name: coin.name,
        symbol: coin.symbol,
        current_price: Math.random() * 100000,
        price_change_24h: (Math.random() - 0.5) * 10,
        added_at: new Date().toISOString(),
      }]);
      setNewCoin('');
    }
  };

  const handleRemoveFromWatchlist = (id: string) => {
    setWatchlist(watchlist.filter(item => item.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Add to Watchlist */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Add Coins to Watchlist</h3>
        <div className="flex gap-2">
          <select
            value={newCoin}
            onChange={(e) => setNewCoin(e.target.value)}
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white focus:outline-none focus:border-blue-500"
          >
            <option value="">-- Select a coin --</option>
            {commonCoins.map(coin => (
              <option key={coin.id} value={coin.id}>
                {coin.name} ({coin.symbol})
              </option>
            ))}
          </select>
          <button
            onClick={() => newCoin && handleAddToWatchlist(newCoin)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white transition-colors"
          >
            Add
          </button>
        </div>
      </div>

      {/* Watchlist Items */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Your Watchlist</h3>
        {watchlist.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No items in watchlist</p>
        ) : (
          <div className="space-y-3">
            {watchlist.map(item => (
              <div
                key={item.id}
                className="flex items-center justify-between p-4 bg-gray-700/50 rounded hover:bg-gray-700 transition-colors"
              >
                <div className="flex-1">
                  <p className="font-semibold text-white">{item.symbol}</p>
                  <p className="text-sm text-gray-400">{item.coin_name}</p>
                </div>
                
                <div className="text-right mr-6">
                  <p className="font-semibold text-white">${item.current_price.toFixed(2)}</p>
                  <p className={`text-sm ${
                    item.price_change_24h >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {item.price_change_24h >= 0 ? '+' : ''}{item.price_change_24h.toFixed(2)}%
                  </p>
                </div>

                <button
                  onClick={() => handleRemoveFromWatchlist(item.id)}
                  className="px-3 py-1 bg-red-600/50 hover:bg-red-600 rounded text-red-300 hover:text-red-100 transition-colors text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Watchlist Statistics */}
      {watchlist.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <p className="text-gray-400 text-sm font-medium mb-2">Total Watchlist Items</p>
            <p className="text-3xl font-bold text-white">{watchlist.length}</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <p className="text-gray-400 text-sm font-medium mb-2">Average 24h Change</p>
            <p className={`text-3xl font-bold ${
              watchlist.reduce((sum, item) => sum + item.price_change_24h, 0) / watchlist.length >= 0
                ? 'text-green-400'
                : 'text-red-400'
            }`}>
              {(watchlist.reduce((sum, item) => sum + item.price_change_24h, 0) / watchlist.length).toFixed(2)}%
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default WatchlistManager;
