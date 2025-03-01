"""
Market analysis module for the trading bot.
Handles fetching and analyzing market data for high frequency trading.
"""

from utils.data_utils import prepare_ohlcv_dataframe, calculate_moving_averages
from trading.strategies import calculate_ma_crossover_signals, calculate_enhanced_signals, calculate_scalping_signals, get_latest_signal, get_latest_scalping_signal, calculate_high_frequency_signals, get_high_frequency_signal
from utils.terminal_colors import print_error, print_warning

def fetch_ohlcv_data(exchange, symbol, timeframe, limit=30):
    """
    Fetch candlestick data from the exchange with optimization for high frequency
    
    Parameters:
    exchange (ccxt.Exchange): Exchange instance
    symbol (str): The trading pair (e.g., 'BTC/USDT')
    timeframe (str): The candle timeframe (e.g., '30s', '1m')
    limit (int): Number of candles to fetch (reduced for faster processing)
    
    Returns:
    pandas.DataFrame: OHLCV data
    """
    try:
        # Fetch OHLCV data using CCXT (no authentication needed)
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = prepare_ohlcv_dataframe(ohlcv)
        
        return df
    except Exception as e:
        print_error(f"Error fetching data: {e}")
        return None

def analyze_market(exchange, symbol, timeframe, short_window, long_window, 
                   use_enhanced_strategy=False, use_scalping_strategy=False, limit=30):
    """
    Analyze market data and calculate signals with high frequency optimization
    
    Parameters:
    exchange (ccxt.Exchange): Exchange instance
    symbol (str): The trading pair (e.g., 'BTC/USDT')
    timeframe (str): The candle timeframe (e.g., '30s', '1m')
    short_window (int): Short moving average window
    long_window (int): Long moving average window
    use_enhanced_strategy (bool): Whether to use enhanced strategy
    use_scalping_strategy (bool): Whether to use scalping strategy
    limit (int): Number of candles to fetch
    
    Returns:
    pandas.DataFrame: OHLCV data with signals
    """
    # Fetch latest data
    df = fetch_ohlcv_data(exchange, symbol, timeframe, limit=limit)
    
    if df is None:
        return None
    
    if len(df) < long_window:
        print_warning(f"Not enough data ({len(df)} points, need {long_window}). Will try to process anyway.")
    
    # Calculate moving averages and other indicators
    df = calculate_moving_averages(df, short_window, long_window)
    
    # Always calculate high frequency signals regardless of strategy mode
    df = calculate_high_frequency_signals(df, short_window, long_window)
    
    # Also calculate regular strategy signals as a backup
    if use_scalping_strategy:
        df = calculate_scalping_signals(df, short_window, long_window)
    elif use_enhanced_strategy:
        df = calculate_enhanced_signals(df, short_window, long_window)
    else:
        df = calculate_ma_crossover_signals(df, short_window, long_window)
    
    return df

def get_current_price(df):
    """
    Get the current price from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with OHLCV data
    
    Returns:
    float: Current price
    """
    if df is None or len(df) == 0:
        return None
    
    return df.iloc[-1]['close']

def get_signal_info(df, use_enhanced_strategy=True, use_scalping_strategy=False):
    """
    Get signal information from the DataFrame
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated signals
    use_enhanced_strategy (bool): Whether to use enhanced signals
    use_scalping_strategy (bool): Whether to use scalping strategy
    
    Returns:
    tuple: Signal information depending on strategy
    """
    if df is None or len(df) == 0:
        return None, None, None, None
    
    # Always prefer the high frequency signal if available
    if 'hf_position' in df.columns:
        return get_high_frequency_signal(df)
    elif use_scalping_strategy:
        return get_latest_scalping_signal(df)
    else:
        return get_latest_signal(df, use_enhanced=use_enhanced_strategy)

def extract_high_frequency_indicators(df):
    """
    Extract high frequency technical indicators from the DataFrame for display
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated indicators
    
    Returns:
    dict: Technical indicators information optimized for high frequency trading
    """
    if df is None or len(df) == 0:
        return {}
    
    latest = df.iloc[-1]
    indicators = {}
    
    # Common indicators
    indicators['current_price'] = latest.get('close')
    
    # High frequency indicators
    indicators['ema1'] = latest.get('ema1')
    indicators['ema2'] = latest.get('ema2')
    indicators['ema3'] = latest.get('ema3')
    indicators['ema5'] = latest.get('ema5')
    indicators['fast_rsi'] = latest.get('fast_rsi')
    indicators['stoch_k'] = latest.get('stoch_k')
    indicators['stoch_d'] = latest.get('stoch_d')
    
    # Bollinger Bands
    if 'bb_lower' in df.columns and 'bb_upper' in df.columns:
        indicators['bb_lower'] = latest.get('bb_lower')
        indicators['bb_upper'] = latest.get('bb_upper')
        indicators['bb_middle'] = latest.get('bb_middle')
        
        # Add BB width as volatility indicator
        if 'bb_width' in df.columns:
            indicators['bb_width'] = latest.get('bb_width')
            
    # Add price change percentage from previous candle
    if len(df) > 1:
        prev_price = df.iloc[-2].get('close')
        if prev_price and prev_price > 0:
            indicators['price_change_pct'] = (latest.get('close') / prev_price - 1) * 100
    
    return indicators