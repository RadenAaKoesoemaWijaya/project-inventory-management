import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple, Union

# Try to import advanced libraries
try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False

logger = logging.getLogger(__name__)

class BaseForecaster:
    """Base class for forecasters"""
    def fit(self, data: pd.Series):
        raise NotImplementedError
        
    def forecast(self, periods: int) -> pd.DataFrame:
        raise NotImplementedError

class ARIMAForecaster(BaseForecaster):
    """ARIMA Forecaster"""
    def __init__(self):
        self.model = None
        self.fit_result = None
        self.last_date = None
        
    def fit(self, data: pd.Series):
        if not STATS_AVAILABLE:
            return False
            
        try:
            self.last_date = data.index[-1]
            # Simple auto-arima like logic or fixed order for stability
            # Using (1,1,1) as a safe default for general purpose
            self.model = ARIMA(data, order=(1, 1, 1))
            self.fit_result = self.model.fit()
            return True
        except Exception as e:
            logger.error(f"Error fitting ARIMA: {e}")
            return False
            
    def forecast(self, periods: int) -> pd.DataFrame:
        if not self.fit_result:
            return pd.DataFrame()
            
        try:
            forecast_result = self.fit_result.get_forecast(steps=periods)
            forecast_values = forecast_result.predicted_mean
            conf_int = forecast_result.conf_int()
            
            dates = pd.date_range(start=self.last_date + timedelta(days=1), periods=periods, freq=self.last_date.freq or 'D')
            
            df = pd.DataFrame({
                'date': dates,
                'forecast': forecast_values.values,
                'confidence_lower': conf_int.iloc[:, 0].values,
                'confidence_upper': conf_int.iloc[:, 1].values
            })
            
            # Ensure no negative values for physical quantities
            df['forecast'] = df['forecast'].apply(lambda x: max(0, x))
            df['confidence_lower'] = df['confidence_lower'].apply(lambda x: max(0, x))
            df['confidence_upper'] = df['confidence_upper'].apply(lambda x: max(0, x))
            
            return df
        except Exception as e:
            logger.error(f"Error forecasting ARIMA: {e}")
            return pd.DataFrame()

class ExponentialSmoothingForecaster(BaseForecaster):
    """Holt-Winters Exponential Smoothing"""
    def __init__(self):
        self.model = None
        self.fit_result = None
        self.last_date = None
        
    def fit(self, data: pd.Series, seasonal_periods=12):
        if not STATS_AVAILABLE:
            return False
            
        try:
            self.last_date = data.index[-1]
            # Additive trend and seasonality
            if len(data) >= seasonal_periods * 2:
                self.model = ExponentialSmoothing(
                    data, 
                    trend='add', 
                    seasonal='add', 
                    seasonal_periods=seasonal_periods
                )
            else:
                # Fallback to simple smoothing if not enough data
                self.model = ExponentialSmoothing(data, trend='add')
                
            self.fit_result = self.model.fit()
            return True
        except Exception as e:
            logger.error(f"Error fitting Exponential Smoothing: {e}")
            return False
            
    def forecast(self, periods: int) -> pd.DataFrame:
        if not self.fit_result:
            return pd.DataFrame()
            
        try:
            forecast_values = self.fit_result.forecast(periods)
            
            dates = pd.date_range(start=self.last_date + timedelta(days=1), periods=periods, freq=self.last_date.freq or 'D')
            
            # Simple confidence intervals (ES doesn't provide them natively easily in statsmodels)
            # Using 10% margin as placeholder or standard deviation of residuals if available
            std_resid = np.std(self.fit_result.resid) if hasattr(self.fit_result, 'resid') else forecast_values.mean() * 0.1
            
            df = pd.DataFrame({
                'date': dates,
                'forecast': forecast_values.values,
                'confidence_lower': forecast_values.values - 1.96 * std_resid,
                'confidence_upper': forecast_values.values + 1.96 * std_resid
            })
            
            # Ensure no negative values
            df['forecast'] = df['forecast'].apply(lambda x: max(0, x))
            df['confidence_lower'] = df['confidence_lower'].apply(lambda x: max(0, x))
            df['confidence_upper'] = df['confidence_upper'].apply(lambda x: max(0, x))
            
            return df
        except Exception as e:
            logger.error(f"Error forecasting ES: {e}")
            return pd.DataFrame()

class EnsembleForecaster(BaseForecaster):
    """Ensemble of available forecasters"""
    def __init__(self):
        self.forecasters = []
        self.weights = []
        
    def fit(self, data: pd.Series):
        if not STATS_AVAILABLE:
            return False
            
        self.forecasters = [
            ARIMAForecaster(),
            ExponentialSmoothingForecaster()
        ]
        
        valid_forecasters = []
        for f in self.forecasters:
            if f.fit(data):
                valid_forecasters.append(f)
        
        self.forecasters = valid_forecasters
        return len(self.forecasters) > 0
        
    def forecast(self, periods: int) -> pd.DataFrame:
        if not self.forecasters:
            return pd.DataFrame()
            
        results = []
        for f in self.forecasters:
            res = f.forecast(periods)
            if not res.empty:
                results.append(res)
        
        if not results:
            return pd.DataFrame()
            
        # Average forecasts
        final_df = results[0].copy()
        for col in ['forecast', 'confidence_lower', 'confidence_upper']:
            final_df[col] = np.mean([r[col].values for r in results], axis=0)
            
        return final_df

def calculate_forecast_metrics(actual, predicted):
    """Calculate accuracy metrics"""
    if not STATS_AVAILABLE:
        return {}
        
    try:
        # Ensure same length
        min_len = min(len(actual), len(predicted))
        actual = actual[:min_len]
        predicted = predicted[:min_len]
        
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # Handle zero division for MAPE
        with np.errstate(divide='ignore', invalid='ignore'):
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            mape = np.nan_to_num(mape, nan=0.0, posinf=0.0, neginf=0.0)
            
        r2 = r2_score(actual, predicted)
        
        return {
            'mae': mae,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return {}
