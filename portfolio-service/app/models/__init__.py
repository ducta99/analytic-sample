"""
Database models for portfolio service.
"""
from datetime import datetime
from decimal import Decimal as DecimalType
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from shared.utils.database import Base

# Export Base for testing
__all__ = ["Portfolio", "PortfolioAsset", "PortfolioHistory", "Watchlist", "Base"]


class Portfolio(Base):
    """User portfolio."""
    
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assets = relationship("PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_user_active", "user_id", "is_active"),
    )
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}')>"


class PortfolioAsset(Base):
    """Asset in a portfolio."""
    
    __tablename__ = "portfolio_assets"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    coin_id = Column(String(50), nullable=False, index=True)
    quantity = Column(Numeric(20, 8), nullable=False)  # Amount of coin
    purchase_price = Column(Numeric(20, 8), nullable=False)  # Price per unit at purchase
    purchase_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="assets")
    
    __table_args__ = (
        Index("idx_portfolio_coin", "portfolio_id", "coin_id"),
        UniqueConstraint("portfolio_id", "coin_id", name="uq_portfolio_coin"),
    )
    
    def __repr__(self):
        return f"<PortfolioAsset(portfolio_id={self.portfolio_id}, coin_id='{self.coin_id}', qty={self.quantity})>"


class PortfolioHistory(Base):
    """Historical portfolio snapshots."""
    
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    total_value = Column(Numeric(20, 2), nullable=False)
    total_cost = Column(Numeric(20, 2), nullable=False)
    total_gain_loss = Column(Numeric(20, 2), nullable=False)
    roi_pct = Column(Float, nullable=False)
    num_assets = Column(Integer, nullable=False)
    snapshot_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="history")
    
    __table_args__ = (
        Index("idx_portfolio_time", "portfolio_id", "snapshot_at"),
    )
    
    def __repr__(self):
        return f"<PortfolioHistory(portfolio_id={self.portfolio_id}, value={self.total_value}, roi={self.roi_pct}%)>"


class Watchlist(Base):
    """User watchlist for tracking coins."""
    
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    coin_id = Column(String(50), nullable=False, index=True)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("user_id", "coin_id", name="uq_watchlist_user_coin"),
        Index("idx_user_coins", "user_id", "added_at"),
    )
    
    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, coin_id='{self.coin_id}')>"
