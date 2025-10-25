/**
 * Prices Redux Slice
 * 
 * Manages cryptocurrency price data: current prices, historical data, updates
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../index';

export interface CoinPrice {
  coinId: string;
  symbol: string;
  name: string;
  price: number;
  priceChange24h: number;
  priceChangePercent24h: number;
  marketCap: number;
  marketCapRank: number;
  volume24h: number;
  timestamp: string;
}

interface PricesState {
  prices: Record<string, CoinPrice>;
  favoriteCoins: string[];
  isLoading: boolean;
  error: string | null;
  lastUpdate: string | null;
  updateInterval: number; // seconds
}

const initialState: PricesState = {
  prices: {},
  favoriteCoins: [],
  isLoading: false,
  error: null,
  lastUpdate: null,
  updateInterval: 10, // Update every 10 seconds
};

export const pricesSlice = createSlice({
  name: 'prices',
  initialState,
  reducers: {
    // Fetch prices
    fetchPricesStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchPricesSuccess: (state, action: PayloadAction<CoinPrice[]>) => {
      state.isLoading = false;
      action.payload.forEach((price) => {
        state.prices[price.coinId] = price;
      });
      state.lastUpdate = new Date().toISOString();
      state.error = null;
    },

    fetchPricesFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update single price (WebSocket)
    updatePrice: (state, action: PayloadAction<CoinPrice>) => {
      state.prices[action.payload.coinId] = action.payload;
      state.lastUpdate = new Date().toISOString();
    },

    // Update multiple prices (batch)
    updatePrices: (state, action: PayloadAction<CoinPrice[]>) => {
      action.payload.forEach((price) => {
        state.prices[price.coinId] = price;
      });
      state.lastUpdate = new Date().toISOString();
    },

    // Clear prices
    clearPrices: (state) => {
      state.prices = {};
      state.lastUpdate = null;
    },

    // Add favorite coin
    addFavoriteCoin: (state, action: PayloadAction<string>) => {
      if (!state.favoriteCoins.includes(action.payload)) {
        state.favoriteCoins.push(action.payload);
      }
    },

    // Remove favorite coin
    removeFavoriteCoin: (state, action: PayloadAction<string>) => {
      state.favoriteCoins = state.favoriteCoins.filter(
        (coin) => coin !== action.payload
      );
    },

    // Set favorite coins
    setFavoriteCoins: (state, action: PayloadAction<string[]>) => {
      state.favoriteCoins = action.payload;
    },

    // Set update interval
    setUpdateInterval: (state, action: PayloadAction<number>) => {
      state.updateInterval = action.payload;
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    },
  },
});

// Actions
export const {
  fetchPricesStart,
  fetchPricesSuccess,
  fetchPricesFailure,
  updatePrice,
  updatePrices,
  clearPrices,
  addFavoriteCoin,
  removeFavoriteCoin,
  setFavoriteCoins,
  setUpdateInterval,
  clearError,
} = pricesSlice.actions;

// Selectors
export const selectAllPrices = (state: RootState) => state.prices.prices;
export const selectPrice = (state: RootState, coinId: string) =>
  state.prices.prices[coinId];
export const selectPriceBySymbol =
  (symbol: string) => (state: RootState) => {
    return Object.values(state.prices.prices).find(
      (p) => p.symbol.toLowerCase() === symbol.toLowerCase()
    );
  };
export const selectFavoriteCoins = (state: RootState) =>
  state.prices.favoriteCoins;
export const selectFavoriteCoinPrices = (state: RootState) =>
  state.prices.favoriteCoins
    .map((coinId) => state.prices.prices[coinId])
    .filter(Boolean);
export const selectPricesLoading = (state: RootState) =>
  state.prices.isLoading;
export const selectPricesError = (state: RootState) => state.prices.error;
export const selectPricesLastUpdate = (state: RootState) =>
  state.prices.lastUpdate;
export const selectUpdateInterval = (state: RootState) =>
  state.prices.updateInterval;

export default pricesSlice.reducer;
