"""
Signal processing module for the trading bot.
Handles calculation of signal strength and position sizing.
"""

import time
from datetime import datetime
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_simulation, 
    format_profit, format_percentage, Colors
)

def calculate_signal_strength(df, use_enhanced_strategy=True, use_scalping_strategy=False):
    """
    Calculate the strength of a trading signal on a scale of 0.0 to 1.0
    
    Parameters:
    df (pandas.DataFrame): DataFrame with indicators and signals
    use_enhanced_strategy (bool): Whether to use enhanced strategy indicators
    use_scalping_strategy (bool): Whether to use scalping strategy indicators
    
    Returns:
    float: Signal strength from 0.0 (weak) to 1.0 (strong)
    """
    if df is None or len(df) < 2:
        return 0.0
    
    latest = df.iloc[-1]
    strength_components = []
    
    # Common strength components
    # 1. Moving Average spread
    if 'short_ma' in latest and 'long_ma' in latest and latest['short_ma'] is not None and latest['long_ma'] is not None:
        ma_spread = (latest['short_ma'] / latest['long_ma'] - 1) * 100
        # Normalize to 0-1 range (5% spread would be very significant)
        ma_strength = min(abs(ma_spread) / 5.0, 1.0) * (1 if ma_spread > 0 else -1)
        strength_components.append(max(0, ma_strength))
    
    if use_scalping_strategy:
        # EMA crossover strength
        if 'ema3' in latest and 'ema8' in latest and latest['ema3'] is not None and latest['ema8'] is not None:
            ema_spread = (latest['ema3'] / latest['ema8'] - 1) * 100
            ema_strength = min(abs(ema_spread) / 3.0, 1.0) * (1 if ema_spread > 0 else -1)
            strength_components.append(max(0, ema_strength))
        
        # RSI strength (normalized, higher is stronger buy)
        if 'fast_rsi' in latest and latest['fast_rsi'] is not None:
            # RSI below 30 is strong buy, scale from 0-30 to 1.0-0.0
            if latest['fast_rsi'] < 30:
                rsi_strength = (30 - latest['fast_rsi']) / 30.0
                strength_components.append(rsi_strength)
            else:
                strength_components.append(0.0)
        
        # Stochastic crossover strength
        if ('stoch_k' in latest and 'stoch_d' in latest and 
            latest['stoch_k'] is not None and latest['stoch_d'] is not None):
            stoch_spread = latest['stoch_k'] - latest['stoch_d']
            # Normalize and adjust for buy signals (positive spread)
            stoch_strength = min(abs(stoch_spread) / 20.0, 1.0) * (1 if stoch_spread > 0 else -1)
            strength_components.append(max(0, stoch_strength))
            
    elif use_enhanced_strategy:
        # RSI strength 
        if 'rsi' in latest and latest['rsi'] is not None:
            if latest['rsi'] < 30:  # Oversold territory
                rsi_strength = (30 - latest['rsi']) / 30.0
                strength_components.append(rsi_strength)
            else:
                strength_components.append(0.0)
        
        # MACD strength
        if ('macd' in latest and 'macd_signal' in latest and 'close' in latest and
            latest['macd'] is not None and latest['macd_signal'] is not None and latest['close'] is not None):
            macd_spread = latest['macd'] - latest['macd_signal']
            # Normalize based on price - MACD of 10 on a $50 asset is more significant than on a $5000 asset
            price_factor = 1000.0 / latest['close'] if latest['close'] > 0 else 0.2
            macd_strength = min(abs(macd_spread * price_factor) / 2.0, 1.0) * (1 if macd_spread > 0 else -1)
            strength_components.append(max(0, macd_strength))
    
    # Bollinger Band strength (common to all strategies)
    if ('bb_lower' in latest and 'bb_upper' in latest and 'close' in latest and
        latest['bb_lower'] is not None and latest['bb_upper'] is not None and latest['close'] is not None and
        latest['bb_upper'] > latest['bb_lower']):  # Avoid division by zero
        # Calculate distance from price to lower band as percentage
        bb_distance = (latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower'])
        # Distance of 0 means we're at lower band (strong buy), 1 means upper band (weak buy)
        bb_strength = 1.0 - min(bb_distance, 1.0)
        strength_components.append(bb_strength)
    
    # Calculate final strength (if we have any components)
    if strength_components:
        # Weight recent price action more heavily
        if len(df) >= 3:
            price_momentum = 1.0 if df.iloc[-1]['close'] > df.iloc[-2]['close'] else 0.0
            strength_components.append(price_momentum)
        
        # Average all components
        return sum(strength_components) / len(strength_components)
    
    return 0.0

def calculate_position_increment(bot, signal_strength):
    """
    Calculate position increment size based on signal strength
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    signal_strength (float): Signal strength from 0.0 to 1.0
    
    Returns:
    float: Position increment factor
    """
    # Only increment if signal is strong enough
    if signal_strength < bot.min_signal_strength_for_increment:
        return 0.0
    
    # Scale increment size based on signal strength
    # Start with minimum 1.0 increment at threshold, scale up to 2.0 at full strength
    increment_factor = 1.0 + signal_strength
    
    # Limit increments based on current position
    current_increments = bot.current_position_size / bot.base_position_size
    remaining_increments = bot.max_position_increments - current_increments
    
    # If we have less than 1 increment remaining, scale down the increment factor
    if remaining_increments < 1.0:
        increment_factor *= remaining_increments
    
    return increment_factor

def calculate_sell_amount(bot, signal_strength):
    """
    Calculate sell amount based on signal strength
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    signal_strength (float): Signal strength from 0.0 to 1.0
    
    Returns:
    float: Amount to sell
    """
    # For very strong sell signals, sell the entire position
    if signal_strength > 0.8:
        return bot.current_position_size
    
    # For moderate signals, sell a portion based on strength
    # Sell between 25% and 75% of position based on signal strength
    sell_percentage = 0.25 + (signal_strength * 0.5)
    sell_amount = bot.current_position_size * sell_percentage
    
    # Ensure minimum sell size (at least base position size)
    if sell_amount < bot.base_position_size and bot.current_position_size >= bot.base_position_size:
        sell_amount = bot.base_position_size
    elif sell_amount < bot.current_position_size:
        # If we can't sell a full base position size but have some position,
        # just sell what we have
        sell_amount = bot.current_position_size
    
    # Ensure we don't sell more than we have
    return min(sell_amount, bot.current_position_size)