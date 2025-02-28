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
        # Shorter periods for more frequent signals
        macd, macd_signal, macd_hist = ta.MACD(
            df['close'].values, 
            fastperiod=8,     # Changed from 12 to 8
            slowperiod=17,    # Changed from 26 to 17
            signalperiod=6    # Changed from 9 to 6
        )
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
    
    # 3. Bollinger Bands
    if 'close' in df.columns:
        upper, middle, lower = ta.BBANDS(
            df['close'].values,
            timeperiod=15,    # Changed from 20 to 15
            nbdevup=1.8,      # Changed from 2 to 1.8
            nbdevdn=1.8,      # Changed from 2 to 1.8
            matype=0
        )
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        
        # Add Bollinger Band Width for volatility measurements
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
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
    
    # Add RSI oversold/overbought signals with more sensitive thresholds
    # Buy when RSI is below 35 (moderately oversold)
    df.loc[valid_rows & (df['rsi'] < 35), 'enhanced_signal'] = 1
    # Sell when RSI is above 65 (moderately overbought)
    df.loc[valid_rows & (df['rsi'] > 65), 'enhanced_signal'] = 0
    
    # Add MACD crossover signals
    # Buy when MACD crosses above signal line
    macd_cross_up = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
    df.loc[valid_rows & macd_cross_up, 'enhanced_signal'] = 1
    
    # Sell when MACD crosses below signal line
    macd_cross_down = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
    df.loc[valid_rows & macd_cross_down, 'enhanced_signal'] = 0
    
    # Add Bollinger Band signals with percentage-based entries
    # Buy when price is within 0.5% of lower band (not just touching)
    close_to_lower = ((df['bb_lower'] - df['close']) / df['close']).abs() < 0.005
    df.loc[valid_rows & close_to_lower, 'enhanced_signal'] = 1
    
    # Sell when price is within 0.5% of upper band
    close_to_upper = ((df['bb_upper'] - df['close']) / df['close']).abs() < 0.005
    df.loc[valid_rows & close_to_upper, 'enhanced_signal'] = 0
    
    # Add price momentum signals
    if len(df) >= 3:
        # Short-term price momentum (positive)
        short_momentum_up = (df['close'] > df['close'].shift(1)) & (df['close'].shift(1) > df['close'].shift(2))
        df.loc[valid_rows & short_momentum_up & (df['rsi'] < 60), 'enhanced_signal'] = 1
        
        # Short-term price momentum (negative)
        short_momentum_down = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2))
        df.loc[valid_rows & short_momentum_down & (df['rsi'] > 40), 'enhanced_signal'] = 0
    
    # Calculate enhanced position changes
    df['enhanced_position'] = df['enhanced_signal'].diff()
    
    return df

def calculate_scalping_signals(df, short_window=3, long_window=10):
    """
    Calculate signals for scalping strategy - designed for very frequent trading
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with scalping signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return None
    
    # Ensure we have moving averages
    if 'short_ma' not in df.columns or 'long_ma' not in df.columns:
        df = calculate_moving_averages(df, short_window, long_window)
    
    # Initialize the signal column
    df['scalping_signal'] = 0
    
    # Calculate EMA for shorter timeframes
    df['ema3'] = ta.EMA(df['close'].values, timeperiod=3)
    df['ema5'] = ta.EMA(df['close'].values, timeperiod=5)
    df['ema8'] = ta.EMA(df['close'].values, timeperiod=8)
    
    # Calculate RSI with shorter period
    df['fast_rsi'] = ta.RSI(df['close'].values, timeperiod=7)
    
    # Calculate Stochastic oscillator with shorter periods
    fastk, fastd = ta.STOCHF(
        df['high'].values,
        df['low'].values,
        df['close'].values,
        fastk_period=5,
        fastd_period=3,
        fastd_matype=0
    )
    df['stoch_k'] = fastk
    df['stoch_d'] = fastd
    
    # Calculate Bollinger Bands with tighter settings
    upper, middle, lower = ta.BBANDS(
        df['close'].values,
        timeperiod=10,
        nbdevup=1.5,
        nbdevdn=1.5,
        matype=0
    )
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    
    # Valid rows for calculations
    valid_rows = (
        df['ema3'].notna() &
        df['ema5'].notna() &
        df['ema8'].notna() &
        df['fast_rsi'].notna() &
        df['stoch_k'].notna() &
        df['stoch_d'].notna() &
        df['bb_upper'].notna() &
        df['bb_lower'].notna()
    )
    
    # Generate scalping signals
    
    # 1. EMA crossover signals (faster reaction than SMA)
    ema_cross_up = (df['ema3'] > df['ema5']) & (df['ema3'].shift(1) <= df['ema5'].shift(1))
    df.loc[valid_rows & ema_cross_up, 'scalping_signal'] = 1
    
    ema_cross_down = (df['ema3'] < df['ema5']) & (df['ema3'].shift(1) >= df['ema5'].shift(1))
    df.loc[valid_rows & ema_cross_down, 'scalping_signal'] = 0
    
    # 2. RSI signals with moderate thresholds for more frequent trading
    df.loc[valid_rows & (df['fast_rsi'] < 30), 'scalping_signal'] = 1
    df.loc[valid_rows & (df['fast_rsi'] > 70), 'scalping_signal'] = 0
    
    # 3. Stochastic crossover signals
    stoch_cross_up = (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1))
    df.loc[valid_rows & stoch_cross_up & (df['stoch_k'] < 50), 'scalping_signal'] = 1
    
    stoch_cross_down = (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1))
    df.loc[valid_rows & stoch_cross_down & (df['stoch_k'] > 50), 'scalping_signal'] = 0
    
    # 4. Bollinger Band bounce signals
    # Buy when price touches or goes below lower band and then bounces up
    bb_bounce_up = (df['close'].shift(1) <= df['bb_lower'].shift(1)) & (df['close'] > df['close'].shift(1))
    df.loc[valid_rows & bb_bounce_up, 'scalping_signal'] = 1
    
    # Sell when price touches or goes above upper band and then bounces down
    bb_bounce_down = (df['close'].shift(1) >= df['bb_upper'].shift(1)) & (df['close'] < df['close'].shift(1))
    df.loc[valid_rows & bb_bounce_down, 'scalping_signal'] = 0
    
    # 5. Price action signals
    if len(df) >= 4:
        # Identify short-term trend reversals (up)
        reversal_up = (
            (df['close'].shift(3) > df['close'].shift(2)) &
            (df['close'].shift(2) > df['close'].shift(1)) &
            (df['close'] > df['close'].shift(1))
        )
        df.loc[valid_rows & reversal_up & (df['fast_rsi'] < 60), 'scalping_signal'] = 1
        
        # Identify short-term trend reversals (down)
        reversal_down = (
            (df['close'].shift(3) < df['close'].shift(2)) &
            (df['close'].shift(2) < df['close'].shift(1)) &
            (df['close'] < df['close'].shift(1))
        )
        df.loc[valid_rows & reversal_down & (df['fast_rsi'] > 40), 'scalping_signal'] = 0
    
    # Calculate position changes
    df['scalping_position'] = df['scalping_signal'].diff()
    
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

def get_latest_scalping_signal(df):
    """
    Get the latest scalping signal from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated scalping signals
    
    Returns:
    tuple: (position_change, current_price, ema3, ema8)
    """
    if df is None or len(df) == 0:
        return None, None, None, None
    
    latest = df.iloc[-1]
    
    if 'scalping_position' in df.columns:
        position_change = latest.get('scalping_position', 0)
    else:
        position_change = 0
    
    current_price = latest.get('close')
    ema3 = latest.get('ema3')
    ema8 = latest.get('ema8')
    
    return position_change, current_price, ema3, ema8