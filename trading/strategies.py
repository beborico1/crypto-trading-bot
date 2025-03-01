import numpy as np
import pandas as pd
import talib as ta

def calculate_ma_crossover_signals(df, short_window=3, long_window=10):
    """
    Calculate basic moving average crossover signals
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with crossover signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return df
    
    # Ensure we have the moving averages
    if 'short_ma' not in df.columns or 'long_ma' not in df.columns:
        # Calculate moving averages if not already calculated
        df['short_ma'] = df['close'].rolling(window=short_window).mean()
        df['long_ma'] = df['close'].rolling(window=long_window).mean()
    
    # Initialize signals
    df['signal'] = 0
    
    # Generate buy/sell signals
    df['signal'] = np.where(df['short_ma'] > df['long_ma'], 1, 0)
    
    # Calculate position changes (1 = buy, -1 = sell, 0 = hold)
    df['position_change'] = df['signal'].diff()
    
    return df

def calculate_enhanced_signals(df, short_window=3, long_window=10):
    """
    Calculate enhanced trading signals using multiple indicators
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame with indicators
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with enhanced signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return df
    
    # First, calculate basic MA crossover signals
    df = calculate_ma_crossover_signals(df, short_window, long_window)
    
    # Ensure we have all the required indicators
    required_indicators = ['rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower', 'bb_middle', 'stoch_k', 'stoch_d']
    for indicator in required_indicators:
        if indicator not in df.columns:
            print(f"Warning: Missing indicator {indicator}")
    
    # Initialize enhanced signals
    df['enhanced_signal'] = df['signal'].copy()
    
    # Generate enhanced buy signals
    if 'rsi' in df.columns:
        # RSI oversold condition (stronger buy signal)
        df.loc[df['rsi'] < 30, 'enhanced_signal'] = 1
    
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        # MACD crossover (buy signal)
        macd_cross_above = (df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        df.loc[macd_cross_above, 'enhanced_signal'] = 1
    
    if 'bb_lower' in df.columns:
        # Price near lower Bollinger Band (buy signal)
        near_lower_band = df['close'] <= df['bb_lower'] * 1.01  # Within 1% of lower band
        df.loc[near_lower_band, 'enhanced_signal'] = 1
    
    if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
        # Stochastic oversold and crossover (buy signal)
        stoch_oversold_cross = (df['stoch_k'] < 20) & (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1))
        df.loc[stoch_oversold_cross, 'enhanced_signal'] = 1
    
    # Generate enhanced sell signals
    if 'rsi' in df.columns:
        # RSI overbought condition (sell signal)
        df.loc[df['rsi'] > 70, 'enhanced_signal'] = 0
    
    if 'macd' in df.columns and 'macd_signal' in df.columns:
        # MACD crossover (sell signal)
        macd_cross_below = (df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        df.loc[macd_cross_below, 'enhanced_signal'] = 0
    
    if 'bb_upper' in df.columns:
        # Price near upper Bollinger Band (sell signal)
        near_upper_band = df['close'] >= df['bb_upper'] * 0.99  # Within 1% of upper band
        df.loc[near_upper_band, 'enhanced_signal'] = 0
    
    if 'stoch_k' in df.columns and 'stoch_d' in df.columns:
        # Stochastic overbought and crossover (sell signal)
        stoch_overbought_cross = (df['stoch_k'] > 80) & (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1))
        df.loc[stoch_overbought_cross, 'enhanced_signal'] = 0
    
    # Calculate position changes for enhanced signals
    df['enhanced_position_change'] = df['enhanced_signal'].diff()
    
    return df

def calculate_scalping_signals(df, short_window=3, long_window=10):
    """
    Calculate scalping signals for very short-term trades
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame with indicators
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with scalping signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return df
    
    # First, ensure we have shorter EMAs for scalping
    df['ema3'] = ta.EMA(df['close'].values, timeperiod=3)
    df['ema5'] = ta.EMA(df['close'].values, timeperiod=5)
    df['ema8'] = ta.EMA(df['close'].values, timeperiod=8)
    
    # Ensure we have a faster RSI
    df['fast_rsi'] = ta.RSI(df['close'].values, timeperiod=7)
    
    # Initialize scalping signals
    df['scalp_signal'] = 0
    
    # Generate scalping buy signals
    
    # EMA crossovers (stronger, faster signal)
    ema_cross_up = (df['ema3'] > df['ema8']) & (df['ema3'].shift(1) <= df['ema8'].shift(1))
    df.loc[ema_cross_up, 'scalp_signal'] = 1
    
    # Fast RSI conditions
    if 'fast_rsi' in df.columns:
        # RSI oversold condition (buy signal)
        df.loc[df['fast_rsi'] < 30, 'scalp_signal'] = 1
        # RSI bullish divergence (price makes lower low, RSI makes higher low)
        if len(df) >= 3:
            price_lower_low = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2))
            rsi_higher_low = (df['fast_rsi'] > df['fast_rsi'].shift(1)) & (df['fast_rsi'].shift(1) < df['fast_rsi'].shift(2))
            df.loc[price_lower_low & rsi_higher_low, 'scalp_signal'] = 1
    
    # Bollinger Band signals
    if 'bb_lower' in df.columns and 'bb_middle' in df.columns:
        # Price bouncing off lower band
        bounce_off_lower = (df['close'].shift(1) <= df['bb_lower'].shift(1)) & (df['close'] > df['bb_lower'])
        df.loc[bounce_off_lower, 'scalp_signal'] = 1
    
    # Generate scalping sell signals
    
    # EMA crossovers
    ema_cross_down = (df['ema3'] < df['ema8']) & (df['ema3'].shift(1) >= df['ema8'].shift(1))
    df.loc[ema_cross_down, 'scalp_signal'] = 0
    
    # Fast RSI conditions
    if 'fast_rsi' in df.columns:
        # RSI overbought condition (sell signal)
        df.loc[df['fast_rsi'] > 70, 'scalp_signal'] = 0
        # RSI bearish divergence (price makes higher high, RSI makes lower high)
        if len(df) >= 3:
            price_higher_high = (df['close'] > df['close'].shift(1)) & (df['close'].shift(1) > df['close'].shift(2))
            rsi_lower_high = (df['fast_rsi'] < df['fast_rsi'].shift(1)) & (df['fast_rsi'].shift(1) > df['fast_rsi'].shift(2))
            df.loc[price_higher_high & rsi_lower_high, 'scalp_signal'] = 0
    
    # Bollinger Band signals
    if 'bb_upper' in df.columns and 'bb_middle' in df.columns:
        # Price rejection from upper band
        rejection_from_upper = (df['close'].shift(1) >= df['bb_upper'].shift(1)) & (df['close'] < df['bb_upper'])
        df.loc[rejection_from_upper, 'scalp_signal'] = 0
    
    # Calculate position changes for scalping signals
    df['scalp_position_change'] = df['scalp_signal'].diff()
    
    return df

def calculate_high_frequency_signals(df, short_window=2, long_window=5):
    """
    Calculate signals optimized for high frequency trading
    
    Parameters:
    df (pandas.DataFrame): OHLCV DataFrame
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    
    Returns:
    pandas.DataFrame: DataFrame with high frequency signals
    """
    if df is None or len(df) < long_window:
        print("Not enough data to calculate signals")
        return df
    
    # Calculate EMAs instead of SMAs for faster response
    # TA-Lib requires timeperiod to be at least 2 for EMA
    df['ema2'] = ta.EMA(df['close'].values, timeperiod=2)
    df['ema3'] = ta.EMA(df['close'].values, timeperiod=3)
    df['ema5'] = ta.EMA(df['close'].values, timeperiod=5)
    
    # For EMA1, we'll use a workaround - use the close price as a proxy for EMA1
    # or calculate it manually since timeperiod=1 is too small for TA-Lib
    df['ema1'] = df['close']  # Close price is effectively EMA with period 1
    
    # Ultra-fast RSI
    df['fast_rsi'] = ta.RSI(df['close'].values, timeperiod=5)
    
    # Fast stochastic oscillator
    fastk, fastd = ta.STOCHF(
        df['high'].values,
        df['low'].values,
        df['close'].values,
        fastk_period=3,
        fastd_period=2,
        fastd_matype=0
    )
    df['stoch_k'] = fastk
    df['stoch_d'] = fastd
    
    # Tight Bollinger Bands for quick signals
    upper, middle, lower = ta.BBANDS(
        df['close'].values,
        timeperiod=8,
        nbdevup=1.5,
        nbdevdn=1.5,
        matype=0
    )
    df['bb_upper'] = upper
    df['bb_middle'] = middle
    df['bb_lower'] = lower
    
    # Initialize signals
    df['hf_signal'] = 0  # High frequency signal
    
    # Valid rows for calculations
    valid_rows = (
        df['close'].notna() &  # Using close instead of ema1
        df['ema3'].notna() &
        df['ema5'].notna() &
        df['fast_rsi'].notna() &
        df['stoch_k'].notna() &
        df['stoch_d'].notna() &
        df['bb_upper'].notna() &
        df['bb_lower'].notna()
    )
    
    # Generate high frequency signals
    
    # 1. Instant EMA crossovers for ultra-fast reaction
    # Using close price for current candle and EMA3 for comparison
    ema_cross_up = (df['close'] > df['ema3']) & (df['close'].shift(1) <= df['ema3'].shift(1))
    df.loc[valid_rows & ema_cross_up, 'hf_signal'] = 1
    
    ema_cross_down = (df['close'] < df['ema3']) & (df['close'].shift(1) >= df['ema3'].shift(1))
    df.loc[valid_rows & ema_cross_down, 'hf_signal'] = 0
    
    # 2. RSI oversold/overbought with extreme thresholds
    df.loc[valid_rows & (df['fast_rsi'] < 25), 'hf_signal'] = 1  # More extreme oversold
    df.loc[valid_rows & (df['fast_rsi'] > 75), 'hf_signal'] = 0  # More extreme overbought
    
    # 3. Stochastic crossover signals with tighter thresholds
    stoch_cross_up = (df['stoch_k'] > df['stoch_d']) & (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1))
    df.loc[valid_rows & stoch_cross_up & (df['stoch_k'] < 40), 'hf_signal'] = 1
    
    stoch_cross_down = (df['stoch_k'] < df['stoch_d']) & (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1))
    df.loc[valid_rows & stoch_cross_down & (df['stoch_k'] > 60), 'hf_signal'] = 0
    
    # 4. Bollinger Band signals with tighter threshold
    close_to_lower = ((df['close'] - df['bb_lower']) / df['close']) < 0.0025  # 0.25% from lower band
    df.loc[valid_rows & close_to_lower, 'hf_signal'] = 1
    
    close_to_upper = ((df['bb_upper'] - df['close']) / df['close']) < 0.0025  # 0.25% from upper band
    df.loc[valid_rows & close_to_upper, 'hf_signal'] = 0
    
    # 5. Add very short-term price momentum signals (1-minute trends)
    if len(df) >= 3:
        # Detect micro-trends (last 3 candles)
        micro_uptrend = (df['close'] > df['close'].shift(1)) & (df['close'].shift(1) > df['close'].shift(2))
        micro_downtrend = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2))
        
        # Use micro-trends to enhance signals
        df.loc[valid_rows & micro_uptrend & (df['fast_rsi'] < 70), 'hf_signal'] = 1
        df.loc[valid_rows & micro_downtrend & (df['fast_rsi'] > 30), 'hf_signal'] = 0
    
    # Calculate position changes for high frequency signal
    df['hf_position'] = df['hf_signal'].diff()
    
    # Add volatility-based signal adjustment - increase sensitivity when volatility is high
    if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'close' in df.columns:
        # Calculate BB width as percentage of price
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close'] * 100
        
        # Calculate average BB width over the last 10 periods
        df['avg_bb_width'] = df['bb_width'].rolling(window=10).mean()
        
        # Identify high volatility periods (BB width > 1.2 * average)
        if 'avg_bb_width' in df.columns:
            high_volatility = df['bb_width'] > 1.2 * df['avg_bb_width']
            
            # During high volatility, make signals more sensitive
            small_moves_up = (df['close'] > df['close'].shift(1)) & high_volatility
            small_moves_down = (df['close'] < df['close'].shift(1)) & high_volatility
            
            # Generate more frequent signals during high volatility
            df.loc[valid_rows & small_moves_up, 'hf_signal'] = 1
            df.loc[valid_rows & small_moves_down, 'hf_signal'] = 0
            
            # Recalculate position after volatility adjustments
            df['hf_position'] = df['hf_signal'].diff()
    
    return df

def get_latest_signal(df, use_enhanced=True):
    """
    Get the latest signal from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated signals
    use_enhanced (bool): Whether to use enhanced signals
    
    Returns:
    tuple: (position_change, current_price, short_ma, long_ma)
    """
    if df is None or len(df) == 0:
        return None, None, None, None
    
    latest = df.iloc[-1]
    
    if use_enhanced and 'enhanced_position_change' in df.columns:
        position_change = latest.get('enhanced_position_change', 0)
    elif 'position_change' in df.columns:
        position_change = latest.get('position_change', 0)
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
    
    if 'scalp_position_change' in df.columns:
        position_change = latest.get('scalp_position_change', 0)
    else:
        position_change = 0
    
    current_price = latest.get('close')
    ema3 = latest.get('ema3')
    ema8 = latest.get('ema8')
    
    return position_change, current_price, ema3, ema8

def get_high_frequency_signal(df):
    """
    Get the latest high frequency signal from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated high frequency signals
    
    Returns:
    tuple: (position_change, current_price, ema1, ema3)
    """
    if df is None or len(df) == 0:
        return None, None, None, None
    
    latest = df.iloc[-1]
    
    if 'hf_position' in df.columns:
        position_change = latest.get('hf_position', 0)
    else:
        position_change = 0
    
    current_price = latest.get('close')
    ema1 = latest.get('ema1')
    ema3 = latest.get('ema3')
    
    return position_change, current_price, ema1, ema3