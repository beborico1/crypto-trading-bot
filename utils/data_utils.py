import pandas as pd
import numpy as np
import talib as ta

def prepare_ohlcv_dataframe(ohlcv_data):
    """
    Convert OHLCV data to pandas DataFrame
    
    Parameters:
    ohlcv_data (list): OHLCV data from exchange
    
    Returns:
    pandas.DataFrame: OHLCV data as DataFrame
    """
    if not ohlcv_data:
        return None
        
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    return df

def calculate_moving_averages(df, short_window, long_window):
    """
    Calculate moving averages on OHLCV data
    
    Parameters:
    df (pandas.DataFrame): OHLCV data
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with moving averages
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate moving averages")
        return None
    
    # Calculate moving averages
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    
    # Add more indicators for enhanced trading signals
    try:
        # Calculate RSI (Relative Strength Index)
        df['rsi'] = ta.RSI(df['close'].values, timeperiod=14)
        
        # Calculate MACD (Moving Average Convergence Divergence)
        macd, macd_signal, macd_hist = ta.MACD(
            df['close'].values, 
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # Calculate Bollinger Bands
        upper, middle, lower = ta.BBANDS(
            df['close'].values,
            timeperiod=20,
            nbdevup=2,
            nbdevdn=2,
            matype=0
        )
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # Calculate Stochastic Oscillator
        slowk, slowd = ta.STOCH(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            fastk_period=5,
            slowk_period=3,
            slowk_matype=0,
            slowd_period=3,
            slowd_matype=0
        )
        df['stoch_k'] = slowk
        df['stoch_d'] = slowd
        
        # Add Average True Range (ATR) for volatility
        df['atr'] = ta.ATR(
            df['high'].values,
            df['low'].values,
            df['close'].values,
            timeperiod=14
        )
        
    except Exception as e:
        print(f"Error calculating additional indicators: {e}")
        print("Make sure TA-Lib is installed correctly")
    
    return df