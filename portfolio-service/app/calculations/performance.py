"""
Portfolio performance calculations.
"""
import logging
from typing import List, Optional, Dict, Union, Any
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class PortfolioPerformance:
    """Portfolio performance metrics."""
    
    def __init__(
        self,
        total_value: Decimal,
        total_cost: Decimal,
        total_gain_loss: Decimal,
        roi_pct: float,
        num_assets: int
    ):
        """Initialize performance metrics.
        
        Args:
            total_value: Current portfolio value
            total_cost: Total cost basis
            total_gain_loss: Gain or loss amount
            roi_pct: Return on investment percentage
            num_assets: Number of assets
        """
        self.total_value = total_value
        self.total_cost = total_cost
        self.total_gain_loss = total_gain_loss
        self.roi_pct = roi_pct
        self.num_assets = num_assets
        self.calculated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_value": float(self.total_value),
            "total_cost": float(self.total_cost),
            "total_gain_loss": float(self.total_gain_loss),
            "roi_pct": round(self.roi_pct, 2),
            "num_assets": self.num_assets,
            "calculated_at": self.calculated_at.isoformat()
        }


class PerformanceCalculator:
    """Calculate portfolio performance metrics."""
    
    @staticmethod
    def _to_asset_dict(asset: Union[Dict, Any]) -> Dict:
        """Convert asset (dict or ORM object) to dictionary.
        
        Args:
            asset: Asset as dict or ORM object
        
        Returns:
            Asset as dictionary
        """
        if isinstance(asset, dict):
            return asset
        
        # ORM object - convert to dict
        return {
            'coin_id': asset.coin_id,
            'quantity': asset.quantity,
            'purchase_price': asset.purchase_price,
        }
    
    @staticmethod
    def calculate_portfolio_performance(
        assets: List[Union[Dict, Any]],
        current_prices: Dict[str, Decimal]
    ) -> Dict:
        """Calculate overall portfolio performance.
        
        Args:
            assets: List of portfolio assets with quantity, purchase_price
            current_prices: Dict mapping coin_id to current price
        
        Returns:
            Dictionary with performance metrics
        """
        if not assets:
            return {
                "total_value": Decimal('0'),
                "total_cost": Decimal('0'),
                "total_gain_loss": Decimal('0'),
                "roi_pct": Decimal('0.00'),
                "num_assets": 0
            }
        
        total_value = Decimal('0')
        total_cost = Decimal('0')
        
        for asset in assets:
            asset_dict = PerformanceCalculator._to_asset_dict(asset)
            
            coin_id = asset_dict['coin_id']
            quantity = Decimal(str(asset_dict['quantity']))
            purchase_price = Decimal(str(asset_dict['purchase_price']))
            
            # Cost basis for this asset
            cost = quantity * purchase_price
            total_cost += cost
            
            # Current value of this asset
            current_price = current_prices.get(coin_id)
            if current_price:
                current_price = Decimal(str(current_price))
                value = quantity * current_price
                total_value += value
        
        # Calculate gain/loss
        total_gain_loss = total_value - total_cost
        
        # Calculate ROI percentage
        roi_pct = Decimal('0.00')
        if total_cost > 0:
            roi_pct = Decimal('0.00')
            roi_pct = round((total_gain_loss / total_cost) * Decimal('100'), 2)
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain_loss": total_gain_loss,
            "roi_pct": roi_pct,
            "num_assets": len(assets)
        }
    
    @staticmethod
    def calculate_asset_performance(
        asset: Union[Dict, Any],
        current_price: Decimal
    ) -> Dict:
        """Calculate performance for a single asset.
        
        Args:
            asset: Asset as dict or ORM object
            current_price: Current price per unit
        
        Returns:
            Dictionary with asset performance metrics
        """
        asset_dict = PerformanceCalculator._to_asset_dict(asset)
        
        coin_id = asset_dict['coin_id']
        quantity = Decimal(str(asset_dict['quantity']))
        purchase_price = Decimal(str(asset_dict['purchase_price']))
        current_price = Decimal(str(current_price))
        
        # Cost and current value
        cost_basis = quantity * purchase_price
        current_value = quantity * current_price
        
        # Gain/loss
        gain_loss = current_value - cost_basis
        gain_loss_pct = Decimal('0.00')
        if cost_basis > 0:
            gain_loss_pct = round((gain_loss / cost_basis) * Decimal('100'), 2)
        
        # Days held
        purchase_date = asset_dict.get('purchase_date', datetime.utcnow())
        days_held = (datetime.utcnow() - purchase_date).days
        
        # Annualized return (estimated)
        annualized_return = Decimal('0.00')
        if days_held > 0:
            daily_return = gain_loss_pct / Decimal(str(days_held))
            annualized_return = round(daily_return * Decimal('365'), 2)
        
        return {
            "coin_id": coin_id,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "cost_basis": cost_basis,
            "current_value": current_value,
            "gain_loss": gain_loss,
            "gain_loss_pct": gain_loss_pct,
            "days_held": days_held,
            "annualized_return_pct": annualized_return
        }
    
    @staticmethod
    def calculate_asset_allocation(
        assets: List[Union[Dict, Any]],
        current_prices: Dict[str, Decimal]
    ) -> List[Dict]:
        """Calculate portfolio asset allocation.
        
        Args:
            assets: List of portfolio assets
            current_prices: Dict mapping coin_id to current price
        
        Returns:
            List of asset allocation with percentage
        """
        if not assets:
            return []
        
        # Calculate total value
        total_value = Decimal('0')
        asset_values = []
        
        for asset in assets:
            asset_dict = PerformanceCalculator._to_asset_dict(asset)
            
            coin_id = asset_dict['coin_id']
            quantity = Decimal(str(asset_dict['quantity']))
            current_price = current_prices.get(coin_id)
            
            if current_price:
                current_price = Decimal(str(current_price))
                value = quantity * current_price
                total_value += value
                asset_values.append({
                    'coin_id': coin_id,
                    'value': value
                })
        
        # Calculate percentages
        allocations = []
        for item in asset_values:
            pct = Decimal('0.00')
            if total_value > 0:
                pct = round((item['value'] / total_value) * Decimal('100'), 2)
            
            allocations.append({
                'coin_id': item['coin_id'],
                'value': item['value'],
                'percentage': pct
            })
        
        # Sort by percentage (highest first)
        allocations.sort(key=lambda x: x['percentage'], reverse=True)
        
        return allocations
    
    @staticmethod
    def identify_best_performers(
        assets: List[Union[Dict, Any]],
        current_prices: Dict[str, Decimal],
        top_n: int = 5,
        reverse: bool = False
    ) -> List[Dict]:
        """Identify best and worst performing assets.
        
        Args:
            assets: List of portfolio assets
            current_prices: Dict mapping coin_id to current price
            top_n: Number of top/bottom to return
            reverse: If True, return worst performers
        
        Returns:
            List of best/worst performers
        """
        performances = []
        
        for asset in assets:
            asset_dict = PerformanceCalculator._to_asset_dict(asset)
            
            perf = PerformanceCalculator.calculate_asset_performance(
                asset,
                current_prices.get(
                    asset_dict['coin_id'],
                    asset_dict['purchase_price']
                )
            )
            performances.append(perf)
        
        # Sort by gain/loss percentage
        performances.sort(
            key=lambda x: x['gain_loss_pct'],
            reverse=(not reverse)
        )
        
        return performances[:top_n]
