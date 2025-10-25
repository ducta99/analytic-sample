"""
Analytics Service - Calculations and metrics computation.
"""
import logging
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MovingAverageCalculator:
    """Calculate moving averages (SMA, EMA)."""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average.
        SMA = (P1 + P2 + ... + Pn) / n
        """
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        return sum(recent_prices) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Exponential Moving Average.
        EMA = P_today × K + EMA_yesterday × (1 - K), where K = 2/(n+1)
        """
        if len(prices) < period:
            return None
        
        prices_array = np.array(prices)
        k = 2 / (period + 1)
        
        ema = prices_array[0]
        for price in prices_array[1:]:
            ema = price * k + ema * (1 - k)
        
        return float(ema)


class VolatilityCalculator:
    """Calculate volatility metrics."""
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int) -> Optional[float]:
        """
        Calculate volatility as standard deviation from SMA.
        Volatility = sqrt(Σ(Price_i - SMA)² / n)
        """
        if len(prices) < period:
            return None
        
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        variance = sum((p - sma) ** 2 for p in recent_prices) / period
        return float(np.sqrt(variance))
    
    @staticmethod
    def calculate_std_dev(prices: List[float]) -> Optional[float]:
        """Calculate standard deviation."""
        if len(prices) < 2:
            return None
        return float(np.std(prices))


class CorrelationCalculator:
    """Calculate correlations between coins."""
    
    @staticmethod
    def calculate_correlation(
        prices1: List[float],
        prices2: List[float]
    ) -> Optional[float]:
        """
        Calculate Pearson correlation between two price series.
        Returns value between -1 and +1.
        """
        if len(prices1) < 2 or len(prices2) < 2:
            return None
        
        # Ensure same length
        min_len = min(len(prices1), len(prices2))
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        correlation = np.corrcoef(prices1, prices2)[0, 1]
        return float(correlation) if not np.isnan(correlation) else None


class RSICalculator:
    """Calculate Relative Strength Index (RSI)."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        Calculate RSI indicator.
        RSI = 100 - (100 / (1 + RS)) where RS = AvgGain / AvgLoss
        """
        if len(prices) < period + 1:
            return None
        
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
        gains = deltas.copy()
        losses = deltas.copy()
        
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 0.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)


class MACDCalculator:
    """Calculate MACD (Moving Average Convergence Divergence)."""
    
    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[Dict[str, float]]:
        """
        Calculate MACD indicator.
        """
        if len(prices) < slow_period:
            return None
        
        ema_fast = MovingAverageCalculator.calculate_ema(prices, fast_period)
        ema_slow = MovingAverageCalculator.calculate_ema(prices, slow_period)
        
        if not ema_fast or not ema_slow:
            return None
        
        macd_line = ema_fast - ema_slow
        
        # For signal line, we'd need historical MACD values
        # For now, return basic MACD
        return {
            "macd": macd_line,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow
        }
