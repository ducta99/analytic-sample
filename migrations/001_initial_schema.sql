-- ============================================================================
-- Migration 001: Initial Database Schema
-- Created: 2025-10-25
-- Description: Create initial tables for cryptocurrency analytics dashboard
-- ============================================================================

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================================================
-- COINS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS coins (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    market_cap_rank INT,
    description TEXT,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_coins_symbol ON coins(symbol);
CREATE INDEX idx_coins_market_cap_rank ON coins(market_cap_rank);

-- ============================================================================
-- PRICES TABLE (Time-Series)
-- ============================================================================
CREATE TABLE IF NOT EXISTS prices (
    id BIGSERIAL PRIMARY KEY,
    coin_id INT NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 2),
    market_cap DECIMAL(20, 2),
    timestamp TIMESTAMP NOT NULL,
    exchange VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prices_coin_timestamp ON prices(coin_id, timestamp DESC);
CREATE INDEX idx_prices_timestamp ON prices(timestamp DESC);
CREATE INDEX idx_prices_coin_exchange ON prices(coin_id, exchange);

-- Partition prices by month for better performance
-- Note: This can be done using table inheritance or native partitioning depending on PostgreSQL version

-- ============================================================================
-- PORTFOLIOS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_portfolios_user_is_active ON portfolios(user_id, is_active);

-- ============================================================================
-- PORTFOLIO ASSETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS portfolio_assets (
    id SERIAL PRIMARY KEY,
    portfolio_id INT NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    coin_id INT NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    quantity DECIMAL(20, 8) NOT NULL,
    purchase_price DECIMAL(20, 8) NOT NULL,
    purchase_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, coin_id)
);

CREATE INDEX idx_portfolio_assets_portfolio_id ON portfolio_assets(portfolio_id);
CREATE INDEX idx_portfolio_assets_coin_id ON portfolio_assets(coin_id);

-- ============================================================================
-- SENTIMENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS sentiments (
    id SERIAL PRIMARY KEY,
    coin_id INT NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    score FLOAT CHECK (score >= -1 AND score <= 1),
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,
    positive_pct FLOAT DEFAULT 0,
    negative_pct FLOAT DEFAULT 0,
    neutral_pct FLOAT DEFAULT 0,
    source VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sentiments_coin_timestamp ON sentiments(coin_id, timestamp DESC);
CREATE INDEX idx_sentiments_timestamp ON sentiments(timestamp DESC);
CREATE INDEX idx_sentiments_coin_source ON sentiments(coin_id, source);

-- ============================================================================
-- ANALYTICS METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS analytics_metrics (
    id SERIAL PRIMARY KEY,
    coin_id INT NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,  -- 'SMA', 'EMA', 'VOLATILITY', 'RSI'
    period INT NOT NULL,  -- 7, 14, 30, etc.
    value DECIMAL(20, 8) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_coin_type_period ON analytics_metrics(coin_id, metric_type, period);
CREATE INDEX idx_analytics_timestamp ON analytics_metrics(timestamp DESC);
CREATE INDEX idx_analytics_coin_timestamp ON analytics_metrics(coin_id, timestamp DESC);

-- ============================================================================
-- USER PREFERENCES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark',  -- 'light', 'dark'
    notifications_enabled BOOLEAN DEFAULT true,
    email_alerts BOOLEAN DEFAULT true,
    price_alert_threshold DECIMAL(10, 2) DEFAULT 5,  -- percentage
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- ============================================================================
-- WATCHLIST TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_watchlists_user_id ON watchlists(user_id);

CREATE TABLE IF NOT EXISTS watchlist_coins (
    id SERIAL PRIMARY KEY,
    watchlist_id INT NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    coin_id INT NOT NULL REFERENCES coins(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(watchlist_id, coin_id)
);

CREATE INDEX idx_watchlist_coins_watchlist_id ON watchlist_coins(watchlist_id);
CREATE INDEX idx_watchlist_coins_coin_id ON watchlist_coins(coin_id);

-- ============================================================================
-- NEWS ARTICLES TABLE (for sentiment analysis)
-- ============================================================================
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    coin_id INT REFERENCES coins(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(2048) NOT NULL UNIQUE,
    source VARCHAR(100),
    author VARCHAR(255),
    content TEXT,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_articles_coin_published ON news_articles(coin_id, published_at DESC);
CREATE INDEX idx_news_articles_published_at ON news_articles(published_at DESC);

-- ============================================================================
-- REFRESH TOKENS TABLE (for JWT management)
-- ============================================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    is_revoked BOOLEAN DEFAULT false,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================================
-- Create Seed Data for Common Cryptocurrencies
-- ============================================================================
INSERT INTO coins (symbol, name, market_cap_rank, description) VALUES
    ('BTC', 'Bitcoin', 1, 'The first and most well-known cryptocurrency'),
    ('ETH', 'Ethereum', 2, 'The leading smart contract platform'),
    ('BNB', 'Binance Coin', 3, 'Native token of Binance exchange'),
    ('XRP', 'Ripple', 4, 'Digital payment protocol'),
    ('ADA', 'Cardano', 5, 'Proof-of-stake blockchain platform'),
    ('SOL', 'Solana', 6, 'High-speed blockchain network'),
    ('DOGE', 'Dogecoin', 7, 'Community-driven cryptocurrency'),
    ('USDT', 'Tether', 8, 'USD stablecoin'),
    ('POLKADOT', 'Polkadot', 9, 'Multi-chain networking protocol'),
    ('AVAX', 'Avalanche', 10, 'Proof-of-stake blockchain')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Apply Row-Level Security (RLS) if needed
-- ============================================================================
-- Note: RLS can be enabled for additional security
-- ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE portfolio_assets ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Migration Complete
-- ============================================================================
