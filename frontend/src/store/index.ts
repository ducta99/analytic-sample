/**
 * Redux Store Configuration
 * 
 * Combines all reducers and creates the Redux store with middleware
 */

import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/auth';
import portfolioReducer from './slices/portfolio';
import pricesReducer from './slices/prices';
import sentimentReducer from './slices/sentiment';
import analyticsReducer from './slices/analytics';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    portfolio: portfolioReducer,
    prices: pricesReducer,
    sentiment: sentimentReducer,
    analytics: analyticsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Allow non-serializable values for timestamps in specific paths
        ignoredActions: ['prices/updatePrices', 'sentiment/updateSentiment'],
        ignoredPaths: ['prices.lastUpdate', 'sentiment.lastUpdate'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
