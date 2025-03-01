"""
Market analysis module for the trading bot.
Handles fetching and analyzing market data.
"""

from utils.data_utils import prepare_ohlcv_dataframe, calculate_moving_averages
from trading.strategies import calculate_ma_crossover_signals, calculate_enhanced_signals, calculate_scalping_signals, get_latest_signal, get_latest_scalping_signal
from utils.terminal_colors import print_error

def fetch_ohlcv_data(exchange, symbol, timeframe, limit=100):
    """
    Fetch candlestick data from the exchange
    
    Parameters:
    exchange (ccxt.Exchange): Exchange instance
    symbol (str): The trading pair (e.g., 'BTC/USDT')
    timeframe (str): The candle timeframe (e.g., '1h')
    limit (int): Number of candles to fetch
    
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
                   use_enhanced_strategy=True, use_scalping_strategy=False, limit=100):
    """
    Analyze market data and calculate signals
    
    Parameters:
    exchange (ccxt.Exchange): Exchange instance
    symbol (str): The trading pair (e.g., 'BTC/USDT')
    timeframe (str): The candle timeframe (e.g., '1h')
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
    
    if df is None or len(df) < long_window:
        return None
    
    # Calculate moving averages and other indicators
    df = calculate_moving_averages(df, short_window, long_window)
    
    # Calculate signals based on strategy
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
    
    if use_scalping_strategy:
        return get_latest_scalping_signal(df)
    else:
        return get_latest_signal(df, use_enhanced=use_enhanced_strategy)

def extract_technical_indicators(df, use_enhanced_strategy=True, use_scalping_strategy=False):
    """
    Extract technical indicators from the DataFrame for display
    
    Parameters:
    df (pandas.DataFrame): DataFrame with calculated indicators
    use_enhanced_strategy (bool): Whether to use enhanced strategy
    use_scalping_strategy (bool): Whether to use scalping strategy
    
    Returns:
    dict: Technical indicators information
    """
    if df is None or len(df) == 0:
        return {}
    
    latest = df.iloc[-1]
    indicators = {}
    
    # Common indicators
    indicators['current_price'] = latest.get('close')
    
    if use_scalping_strategy:
        # Scalping strategy indicators
        indicators['ema3'] = latest.get('ema3')
        indicators['ema8'] = latest.get('ema8')
        indicators['fast_rsi'] = latest.get('fast_rsi')
        indicators['stoch_k'] = latest.get('stoch_k')
        indicators['stoch_d'] = latest.get('stoch_d')
    else:
        # Standard or enhanced strategy indicators
        indicators['short_ma'] = latest.get('short_ma')
        indicators['long_ma'] = latest.get('long_ma')
        
        if use_enhanced_strategy:
            indicators['rsi'] = latest.get('rsi')
            indicators['macd'] = latest.get('macd')
            indicators['macd_signal'] = latest.get('macd_signal')
    
    # Bollinger Bands (common to all strategies)
    if 'bb_lower' in df.columns and 'bb_upper' in df.columns:
        indicators['bb_lower'] = latest.get('bb_lower')
        indicators['bb_upper'] = latest.get('bb_upper')
        indicators['bb_middle'] = latest.get('bb_middle')
    
    return indicators