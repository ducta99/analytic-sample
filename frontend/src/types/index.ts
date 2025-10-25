export type PriceData = {
  coin_id: string;
  price: number;
  volume: number;
  timestamp: string;
};

export type Portfolio = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  assets: PortfolioAsset[];
};

export type PortfolioAsset = {
  id: string;
  portfolio_id: string;
  coin_id: string;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
};

export type PortfolioPerformance = {
  total_value: number;
  total_cost: number;
  gain_loss: number;
  roi_percentage: number;
  last_updated: string;
};

export type Sentiment = {
  coin_id: string;
  score: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  timestamp: string;
};

export type SentimentTrend = {
  coin_id: string;
  trends: Sentiment[];
};

export type AnalyticsMetrics = {
  coin_id: string;
  sma_20: number;
  ema_20: number;
  volatility: number;
  correlation: Record<string, number>;
};

export type User = {
  id: string;
  username: string;
  email: string;
  created_at: string;
};

export type AuthToken = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};
