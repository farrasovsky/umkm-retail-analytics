"""Pure Python business analytics modules for retail operations."""

from .inventory import InventoryReport, compute_inventory_health
from .market_basket import MarketBasketReport, compute_market_basket_analysis
from .product import ProductPerformance, compute_product_performance
from .rfm import RFMReport, compute_rfm_segmentation
from .sales import SalesSummary, compute_channel_sales, compute_monthly_sales, compute_sales_summary

__all__ = [
    "SalesSummary",
    "compute_sales_summary",
    "compute_monthly_sales",
    "compute_channel_sales",
    "ProductPerformance",
    "compute_product_performance",
    "InventoryReport",
    "compute_inventory_health",
    "RFMReport",
    "compute_rfm_segmentation",
    "MarketBasketReport",
    "compute_market_basket_analysis",
]

