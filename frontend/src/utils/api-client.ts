import axios, { AxiosInstance, AxiosError } from 'axios';
import { AuthToken } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use((config) => {
      const storedToken = this.getStoredToken();
      if (storedToken) {
        config.headers.Authorization = `Bearer ${storedToken}`;
      }
      return config;
    });

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Redirect to login
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
        return Promise.reject(error);
      }
    );

    // Initialize token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  private getStoredToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return this.token;
  }

  private setStoredToken(token: string): void {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  private clearToken(): void {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
    }
  }

  // Auth endpoints
  async register(username: string, email: string, password: string) {
    const response = await this.client.post<AuthToken>('/api/users/register', {
      username,
      email,
      password,
    });
    this.setStoredToken(response.data.access_token);
    return response.data;
  }

  async login(username: string, password: string) {
    const response = await this.client.post<AuthToken>('/api/users/login', {
      username,
      password,
    });
    this.setStoredToken(response.data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', response.data.refresh_token);
    }
    return response.data;
  }

  async refreshToken() {
    const refreshToken = typeof window !== 'undefined'
      ? localStorage.getItem('refresh_token')
      : null;
    if (!refreshToken) throw new Error('No refresh token');

    const response = await this.client.post<AuthToken>('/api/users/refresh', {
      refresh_token: refreshToken,
    });
    this.setStoredToken(response.data.access_token);
    return response.data;
  }

  logout(): void {
    this.clearToken();
  }

  // Market data endpoints
  async getPrice(coinId: string) {
    const response = await this.client.get(`/api/market/price/${coinId}`);
    return response.data;
  }

  async getMarketHealth() {
    const response = await this.client.get('/api/market/health');
    return response.data;
  }

  // Analytics endpoints
  async getMovingAverage(coinId: string, period: number = 20, method: string = 'sma') {
    const response = await this.client.get(
      `/api/analytics/moving-average/${coinId}`,
      { params: { period, method } }
    );
    return response.data;
  }

  async getVolatility(coinId: string, period: number = 20) {
    const response = await this.client.get(
      `/api/analytics/volatility/${coinId}`,
      { params: { period } }
    );
    return response.data;
  }

  async getCorrelation(coin1: string, coin2: string) {
    const response = await this.client.get(
      '/api/analytics/correlation',
      { params: { coin1, coin2 } }
    );
    return response.data;
  }

  // Portfolio endpoints (placeholder - assuming endpoints exist)
  async getPortfolios() {
    const response = await this.client.get('/api/portfolio');
    return response.data;
  }

  async getPortfolio(portfolioId: string) {
    const response = await this.client.get(`/api/portfolio/${portfolioId}`);
    return response.data;
  }

  async createPortfolio(name: string) {
    const response = await this.client.post('/api/portfolio', { name });
    return response.data;
  }

  async getPortfolioPerformance(portfolioId: string) {
    const response = await this.client.get(`/api/portfolio/${portfolioId}/performance`);
    return response.data;
  }

  // Sentiment endpoints
  async getSentiment(coinId: string) {
    const response = await this.client.get(`/api/sentiment/${coinId}`);
    return response.data;
  }

  async getSentimentTrend(coinId: string) {
    const response = await this.client.get(`/api/sentiment/${coinId}/trend`);
    return response.data;
  }

  // WebSocket connection
  connectWebSocket(path: string): WebSocket {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}${path}`;
    return new WebSocket(wsUrl);
  }
}

export const apiClient = new APIClient();
export default apiClient;
