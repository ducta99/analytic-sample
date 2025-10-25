/**
 * Sentiment Redux Slice
 * 
 * Manages sentiment analysis data: sentiment scores, news, trends
 */

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { RootState } from '../index';

export interface SentimentNews {
  id: string;
  title: string;
  description: string;
  url: string;
  source: string;
  imageUrl: string;
  publishedAt: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentimentScore: number;
}

export interface CoinSentiment {
  coinId: string;
  symbol: string;
  name: string;
  overallScore: number; // -1 to +1
  positivePercent: number;
  negativePercent: number;
  neutralPercent: number;
  sourceCount: number;
  articlesCount: number;
  timestamp: string;
  news: SentimentNews[];
}

interface SentimentState {
  sentiment: Record<string, CoinSentiment>;
  isLoading: boolean;
  error: string | null;
  lastUpdate: string | null;
}

const initialState: SentimentState = {
  sentiment: {},
  isLoading: false,
  error: null,
  lastUpdate: null,
};

export const sentimentSlice = createSlice({
  name: 'sentiment',
  initialState,
  reducers: {
    // Fetch sentiment
    fetchSentimentStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchSentimentSuccess: (state, action: PayloadAction<CoinSentiment[]>) => {
      state.isLoading = false;
      action.payload.forEach((sentiment) => {
        state.sentiment[sentiment.coinId] = sentiment;
      });
      state.lastUpdate = new Date().toISOString();
      state.error = null;
    },

    fetchSentimentFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Fetch single coin sentiment
    fetchCoinSentimentStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },

    fetchCoinSentimentSuccess: (state, action: PayloadAction<CoinSentiment>) => {
      state.isLoading = false;
      state.sentiment[action.payload.coinId] = action.payload;
      state.error = null;
    },

    fetchCoinSentimentFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },

    // Update sentiment (WebSocket or real-time)
    updateSentiment: (state, action: PayloadAction<CoinSentiment>) => {
      state.sentiment[action.payload.coinId] = action.payload;
      state.lastUpdate = new Date().toISOString();
    },

    // Update sentiment news
    updateSentimentNews: (
      state,
      action: PayloadAction<{ coinId: string; news: SentimentNews[] }>
    ) => {
      const sentiment = state.sentiment[action.payload.coinId];
      if (sentiment) {
        sentiment.news = action.payload.news;
        sentiment.articlesCount = action.payload.news.length;
      }
    },

    // Clear sentiment
    clearSentiment: (state) => {
      state.sentiment = {};
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
  fetchSentimentStart,
  fetchSentimentSuccess,
  fetchSentimentFailure,
  fetchCoinSentimentStart,
  fetchCoinSentimentSuccess,
  fetchCoinSentimentFailure,
  updateSentiment,
  updateSentimentNews,
  clearSentiment,
  clearError,
} = sentimentSlice.actions;

// Selectors
export const selectAllSentiment = (state: RootState) =>
  Object.values(state.sentiment.sentiment);
export const selectCoinSentiment = (state: RootState, coinId: string) =>
  state.sentiment.sentiment[coinId];
export const selectSentimentLoading = (state: RootState) =>
  state.sentiment.isLoading;
export const selectSentimentError = (state: RootState) =>
  state.sentiment.error;
export const selectSentimentLastUpdate = (state: RootState) =>
  state.sentiment.lastUpdate;
export const selectCoinSentimentNews = (state: RootState, coinId: string) =>
  state.sentiment.sentiment[coinId]?.news || [];

export default sentimentSlice.reducer;
