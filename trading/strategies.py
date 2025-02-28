import numpy as np
import pandas as pd
import talib as ta

def calculate_ma_crossover_signals(df, short_window, long_window):
    """
    Calculate trading signals based on moving average crossover
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated moving averages
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return None
    
    # Ensure the moving averages are calculated
    if 'short_ma' not in df.columns or 'long_ma' not in df.columns:
        print("Moving averages not found in DataFrame")
        return None
    
    # Initialize the signal column
    df['signal'] = 0
    
    # Create a boolean mask for valid rows (after the moving average windows)
    valid_rows = df['short_ma'].notna() & df['long_ma'].notna()
    
    # Use vectorized operations instead of loc slicing
    signal_values = np.where(df['short_ma'] > df['long_ma'], 1, 0)
    df.loc[valid_rows, 'signal'] = signal_values[valid_rows]
    
    # Calculate position changes
    df['position'] = df['signal'].diff()
    
    return df

def calculate_enhanced_signals(df, short_window, long_window):
    """
    Calculate enhanced trading signals that generate more frequent trades
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with enhanced signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return None
    
    # First, calculate the regular MA crossover signals
    df = calculate_ma_crossover_signals(df, short_window, long_window)
    
    # Calculate additional indicators
    # 1. RSI (Relative Strength Index)
    if 'close' in df.columns:
        df['rsi'] = ta.RSI(df['close'].values, timeperiod=14)
    
    # 2. MACD (Moving Average Convergence Divergence)
    if 'close' in df.columns:
        macd, macd_signal, macd_hist = ta.MACD(
            df['close'].values, 
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
    
    # 3. Bollinger Bands
    if 'close' in df.columns:
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
    
    # Define enhanced signals that trade more frequently
    df['enhanced_signal'] = df['signal'].copy()  # Start with MA crossover signals
    
    # Valid rows for calculations (where indicators are available)
    valid_rows = (
        df['rsi'].notna() &
        df['macd'].notna() &
        df['macd_signal'].notna() &
        df['bb_upper'].notna() &
        df['bb_lower'].notna()
    )
    
    # Add RSI oversold/overbought signals
    # Buy when RSI is below 30 (oversold)
    df.loc[valid_rows & (df['rsi'] < 30), 'enhanced_signal'] = 1
    # Sell when RSI is above 70 (overbought)
    df.loc[valid_rows & (df['rsi'] > 70), 'enhanced_signal'] = 0
    
    # Add MACD crossover signals
    # Buy when MACD crosses above signal line
    macd_cross_up = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df.loc[valid_rows & macd_cross_up, 'enhanced_signal'] = 1
    
    # Sell when MACD crosses below signal line
    macd_cross_down = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
    df.loc[valid_rows & macd_cross_down, 'enhanced_signal'] = 0
    
    # Add Bollinger Band signals
    # Buy when price touches lower band
    df.loc[valid_rows & (df['close'] <= df['bb_lower']), 'enhanced_signal'] = 1
    # Sell when price touches upper band
    df.loc[valid_rows & (df['close'] >= df['bb_upper']), 'enhanced_signal'] = 0
    
    # Calculate enhanced position changes
    df['enhanced_position'] = df['enhanced_signal'].diff()
    
    return df

def get_latest_signal(df, use_enhanced=True):
    """
    Get the latest trading signal from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated signals
    use_enhanced (bool): Whether to use enhanced signals for more frequent trading
    
    Returns:
    tuple: (position_change, current_price, short_ma, long_ma)
    """
    if df is None or len(df) == 0:
        return None, None, None, None
    
    latest = df.iloc[-1]
    
    if use_enhanced and 'enhanced_position' in df.columns:
        position_change = latest.get('enhanced_position', 0)
    elif 'position' in df.columns:
        position_change = latest.get('position', 0)
    else:
        position_change = 0
    
    current_price = latest.get('close')
    short_ma = latest.get('short_ma')
    long_ma = latest.get('long_ma')
    
    return position_change, current_price, short_ma, long_ma