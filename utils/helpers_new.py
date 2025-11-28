import pandas as pd
from .sqlite_database import (
    get_stock_status,
    get_items_low_stock,
    get_recent_transactions,
    get_warehouse_consumption,
    get_top_consumed_items
)
import logging

logger = logging.getLogger(__name__)

def get_stock_status():
    """Get overall stock status"""
    try:
        return get_stock_status()
    except Exception as e:
        logger.error(f"Error getting stock status: {e}")
        return {'total_items': 0, 'healthy_stock': 0, 'low_stock': 0, 'out_of_stock': 0}

def get_department_consumption(days=30):
    """Get department consumption for the last N days"""
    try:
        # Since this is for agricultural system, we'll return warehouse consumption
        df = get_warehouse_consumption(days)
        return df
    except Exception as e:
        logger.error(f"Error getting department consumption: {e}")
        return pd.DataFrame()

def get_top_consumed_items(limit=5, days=30):
    """Get top consumed items in the last N days"""
    try:
        return get_top_consumed_items(limit, days)
    except Exception as e:
        logger.error(f"Error getting top consumed items: {e}")
        return pd.DataFrame()
