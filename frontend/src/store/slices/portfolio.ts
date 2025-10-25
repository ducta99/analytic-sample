/**
 * Portfolio Redux Slice
 * 
 * Manages portfolio data: user portfolios, assets, performance metrics
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../index';

export interface PortfolioAsset {
  id: string;
  coinId: string;
  symbol: string;
  name: string;
  quantity: number;
  purchasePrice: number;
  purchaseDate: string;
  currentPrice: number;
  totalCost: number;
  currentValue: number;
  gainLoss: number;
  gainLossPercent: number;
}

export interface Portfolio {
  id: string;
  userId: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  assets: PortfolioAsset[];
  totalValue: number;
  totalCost: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
}

interface PortfolioState {
  portfolios: Record<string, Portfolio>;
  selectedPortfolioId: string | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  portfolios: {},
  selectedPortfolioId: null,
  isLoading: false,
  error: null,
};

export const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    // Fetch portfolios
    fetchPortfoliosStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchPortfoliosSuccess: (state, action: PayloadAction<Portfolio[]>) => {
      state.isLoading = false;
      action.payload.forEach((portfolio) => {
        state.portfolios[portfolio.id] = portfolio;
      });
      // Set first portfolio as selected if none selected
      if (
        !state.selectedPortfolioId &&
        action.payload.length > 0
      ) {
        state.selectedPortfolioId = action.payload[0].id;
      }
      state.error = null;
    },

    fetchPortfoliosFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Get single portfolio
    fetchPortfolioStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchPortfolioSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.error = null;
    },

    fetchPortfolioFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Create portfolio
    createPortfolioStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    createPortfolioSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.selectedPortfolioId = action.payload.id;
      state.error = null;
    },

    createPortfolioFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update portfolio
    updatePortfolioStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    updatePortfolioSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.error = null;
    },

    updatePortfolioFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Delete portfolio
    deletePortfolioStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    deletePortfolioSuccess: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      delete state.portfolios[action.payload];
      if (state.selectedPortfolioId === action.payload) {
        const remaining = Object.keys(state.portfolios);
        state.selectedPortfolioId = remaining.length > 0 ? remaining[0] : null;
      }
      state.error = null;
    },

    deletePortfolioFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Add asset to portfolio
    addAssetStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    addAssetSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.error = null;
    },

    addAssetFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Remove asset from portfolio
    removeAssetStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    removeAssetSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.error = null;
    },

    removeAssetFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update asset in portfolio
    updateAssetStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    updateAssetSuccess: (state, action: PayloadAction<Portfolio>) => {
      state.isLoading = false;
      state.portfolios[action.payload.id] = action.payload;
      state.error = null;
    },

    updateAssetFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Select portfolio
    selectPortfolio: (state, action: PayloadAction<string>) => {
      state.selectedPortfolioId = action.payload;
    },

    // Update portfolio performance (for real-time updates)
    updatePortfolioPerformance: (
      state,
      action: PayloadAction<{
        portfolioId: string;
        totalValue: number;
        totalGainLoss: number;
        totalGainLossPercent: number;
      }>
    ) => {
      const portfolio = state.portfolios[action.payload.portfolioId];
      if (portfolio) {
        portfolio.totalValue = action.payload.totalValue;
        portfolio.totalGainLoss = action.payload.totalGainLoss;
        portfolio.totalGainLossPercent = action.payload.totalGainLossPercent;
      }
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    },

    // Clear portfolios
    clearPortfolios: (state) => {
      state.portfolios = {};
      state.selectedPortfolioId = null;
    },
  },
});

// Actions
export const {
  fetchPortfoliosStart,
  fetchPortfoliosSuccess,
  fetchPortfoliosFailure,
  fetchPortfolioStart,
  fetchPortfolioSuccess,
  fetchPortfolioFailure,
  createPortfolioStart,
  createPortfolioSuccess,
  createPortfolioFailure,
  updatePortfolioStart,
  updatePortfolioSuccess,
  updatePortfolioFailure,
  deletePortfolioStart,
  deletePortfolioSuccess,
  deletePortfolioFailure,
  addAssetStart,
  addAssetSuccess,
  addAssetFailure,
  removeAssetStart,
  removeAssetSuccess,
  removeAssetFailure,
  updateAssetStart,
  updateAssetSuccess,
  updateAssetFailure,
  selectPortfolio,
  updatePortfolioPerformance,
  clearError,
  clearPortfolios,
} = portfolioSlice.actions;

// Selectors
export const selectAllPortfolios = (state: RootState) =>
  Object.values(state.portfolio.portfolios);
export const selectPortfolio = (state: RootState, portfolioId: string) =>
  state.portfolio.portfolios[portfolioId];
export const selectSelectedPortfolioId = (state: RootState) =>
  state.portfolio.selectedPortfolioId;
export const selectSelectedPortfolio = (state: RootState) => {
  const id = state.portfolio.selectedPortfolioId;
  return id ? state.portfolio.portfolios[id] : null;
};
export const selectPortfolioAssets = (state: RootState, portfolioId: string) =>
  state.portfolio.portfolios[portfolioId]?.assets || [];
export const selectPortfolioLoading = (state: RootState) =>
  state.portfolio.isLoading;
export const selectPortfolioError = (state: RootState) =>
  state.portfolio.error;

export default portfolioSlice.reducer;
