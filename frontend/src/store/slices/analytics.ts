/**
 * Analytics Redux Slice
 * 
 * Manages technical analysis data: moving averages, volatility, correlations
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../index';

export interface MovingAverage {
  period: number;
  type: 'SMA' | 'EMA';
  value: number;
  timestamp: string;
}

export interface CoinAnalytics {
  coinId: string;
  symbol: string;
  name: string;
  currentPrice: number;
  sma50: number;
  sma200: number;
  ema12: number;
  ema26: number;
  macd: number;
  signal: number;
  histogram: number;
  rsi: number;
  volatility24h: number;
  volatility7d: number;
  volatility30d: number;
  beta: number;
  sharpeRatio: number;
  timestamp: string;
}

export interface Correlation {
  coin1Id: string;
  coin2Id: string;
  correlation: number;
  timestamp: string;
}

interface AnalyticsState {
  analytics: Record<string, CoinAnalytics>;
  correlations: Correlation[];
  selectedMetrics: string[];
  isLoading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

const initialState: AnalyticsState = {
  analytics: {},
  correlations: [],
  selectedMetrics: ['SMA50', 'SMA200', 'RSI', 'MACD', 'VOLATILITY'],
  isLoading: false,
  error: null,
  lastUpdate: null,
};

export const analyticsSlice = createSlice({
  name: 'analytics',
  initialState,
  reducers: {
    // Fetch analytics
    fetchAnalyticsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchAnalyticsSuccess: (state, action: PayloadAction<CoinAnalytics[]>) => {
      state.isLoading = false;
      action.payload.forEach((analytic) => {
        state.analytics[analytic.coinId] = analytic;
      });
      state.lastUpdate = new Date().toISOString();
      state.error = null;
    },

    fetchAnalyticsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Fetch single coin analytics
    fetchCoinAnalyticsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchCoinAnalyticsSuccess: (state, action: PayloadAction<CoinAnalytics>) => {
      state.isLoading = false;
      state.analytics[action.payload.coinId] = action.payload;
      state.error = null;
    },

    fetchCoinAnalyticsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update analytics (real-time)
    updateAnalytics: (state, action: PayloadAction<CoinAnalytics>) => {
      state.analytics[action.payload.coinId] = action.payload;
      state.lastUpdate = new Date().toISOString();
    },

    // Fetch correlations
    fetchCorrelationsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchCorrelationsSuccess: (state, action: PayloadAction<Correlation[]>) => {
      state.isLoading = false;
      state.correlations = action.payload;
      state.error = null;
    },

    fetchCorrelationsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update correlation
    updateCorrelation: (state, action: PayloadAction<Correlation>) => {
      const index = state.correlations.findIndex(
        (c) =>
          (c.coin1Id === action.payload.coin1Id &&
            c.coin2Id === action.payload.coin2Id) ||
          (c.coin1Id === action.payload.coin2Id &&
            c.coin2Id === action.payload.coin1Id)
      );

      if (index >= 0) {
        state.correlations[index] = action.payload;
      } else {
        state.correlations.push(action.payload);
      }
    },

    // Select metrics to display
    setSelectedMetrics: (state, action: PayloadAction<string[]>) => {
      state.selectedMetrics = action.payload;
    },

    // Add metric to display
    addSelectedMetric: (state, action: PayloadAction<string>) => {
      if (!state.selectedMetrics.includes(action.payload)) {
        state.selectedMetrics.push(action.payload);
      }
    },

    // Remove metric from display
    removeSelectedMetric: (state, action: PayloadAction<string>) => {
      state.selectedMetrics = state.selectedMetrics.filter(
        (m) => m !== action.payload
      );
    },

    // Clear analytics
    clearAnalytics: (state) => {
      state.analytics = {};
      state.correlations = [];
      state.lastUpdate = null;
    },

    // Clear error
    clearError: (state) => {
      state.error = null;
    },
  },
});

// Actions
export const {
  fetchAnalyticsStart,
  fetchAnalyticsSuccess,
  fetchAnalyticsFailure,
  fetchCoinAnalyticsStart,
  fetchCoinAnalyticsSuccess,
  fetchCoinAnalyticsFailure,
  updateAnalytics,
  fetchCorrelationsStart,
  fetchCorrelationsSuccess,
  fetchCorrelationsFailure,
  updateCorrelation,
  setSelectedMetrics,
  addSelectedMetric,
  removeSelectedMetric,
  clearAnalytics,
  clearError,
} = analyticsSlice.actions;

// Selectors
export const selectAllAnalytics = (state: RootState) =>
  Object.values(state.analytics.analytics);
export const selectCoinAnalytics = (state: RootState, coinId: string) =>
  state.analytics.analytics[coinId];
export const selectCorrelations = (state: RootState) =>
  state.analytics.correlations;
export const selectCoinCorrelations = (state: RootState, coinId: string) =>
  state.analytics.correlations.filter(
    (c) => c.coin1Id === coinId || c.coin2Id === coinId
  );
export const selectAnalyticsLoading = (state: RootState) =>
  state.analytics.isLoading;
export const selectAnalyticsError = (state: RootState) =>
  state.analytics.error;
export const selectSelectedMetrics = (state: RootState) =>
  state.analytics.selectedMetrics;
export const selectAnalyticsLastUpdate = (state: RootState) =>
  state.analytics.lastUpdate;

export default analyticsSlice.reducer;
