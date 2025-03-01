"""
Market display module for the trading bot.
Handles displaying market information and technical indicators for high frequency trading.
"""

from datetime import datetime
from utils.terminal_colors import (
    print_info, print_price, Colors
)
from trading.execution.position_management import display_position_info
from trading.market_analysis import extract_high_frequency_indicators

def display_market_info(bot, df, current_price, symbol_prefix=""):
    """
    Display market information and technical indicators optimized for high frequency trading
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    df (pandas.DataFrame): DataFrame with technical indicators
    current_price (float): Current market price
    symbol_prefix (str): Prefix to use in log messages
    """
    if df is None or len(df) == 0 or current_price is None:
        return
    
    # Get the current timestamp for high frequency display
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Extract high frequency indicators
    indicators = extract_high_frequency_indicators(df)
    
    # Print timestamp and price information
    print_price(f"{symbol_prefix}[{timestamp}] Current price: ${float(current_price):,.2f}")
    
    # Show price change since last update if available
    if 'price_change_pct' in indicators:
        change_pct = indicators['price_change_pct']
        if change_pct > 0:
            change_formatted = f"{Colors.GREEN}+{change_pct:.4f}%{Colors.RESET}"
        elif change_pct < 0:
            change_formatted = f"{Colors.RED}{change_pct:.4f}%{Colors.RESET}"
        else:
            change_formatted = f"{change_pct:.4f}%"
        print_price(f"{symbol_prefix}Change: {change_formatted}")
    
    # Print EMA values
    if 'ema1' in indicators and 'ema3' in indicators:
        print_price(f"{symbol_prefix}EMA1: ${indicators['ema1']:.2f}, EMA3: ${indicators['ema3']:.2f}")
    
    # Print RSI and Stochastic
    if 'fast_rsi' in indicators and 'stoch_k' in indicators and 'stoch_d' in indicators:
        # Color RSI based on extremes
        rsi_value = indicators['fast_rsi']
        if rsi_value > 70:
            rsi_formatted = f"{Colors.RED}{rsi_value:.1f}{Colors.RESET}"
        elif rsi_value < 30:
            rsi_formatted = f"{Colors.GREEN}{rsi_value:.1f}{Colors.RESET}"
        else:
            rsi_formatted = f"{rsi_value:.1f}"
        
        # Color Stochastic
        stoch_k = indicators['stoch_k']
        stoch_d = indicators['stoch_d']
        if stoch_k > stoch_d:
            stoch_formatted = f"{Colors.GREEN}K:{stoch_k:.1f} D:{stoch_d:.1f}{Colors.RESET}"
        else:
            stoch_formatted = f"{Colors.RED}K:{stoch_k:.1f} D:{stoch_d:.1f}{Colors.RESET}"
        
        print_info(f"{symbol_prefix}Fast RSI: {rsi_formatted}, Stochastic: {stoch_formatted}")
    
    # Print Bollinger Band information
    if 'bb_lower' in indicators and 'bb_upper' in indicators and current_price is not None:
        bb_lower = indicators['bb_lower']
        bb_upper = indicators['bb_upper']
        
        # Calculate distances to bands
        distance_to_lower = ((current_price - bb_lower) / current_price) * 100
        distance_to_upper = ((bb_upper - current_price) / current_price) * 100
        
        # For high frequency trading, use tighter thresholds
        threshold = 0.5  # 0.5% for high frequency
        
        # Color BB distances
        if distance_to_lower < threshold:  # Close to lower band (potential buy)
            lower_formatted = f"{Colors.GREEN}{distance_to_lower:.3f}%{Colors.RESET}"
        else:
            lower_formatted = f"{distance_to_lower:.3f}%"
            
        if distance_to_upper < threshold:  # Close to upper band (potential sell)
            upper_formatted = f"{Colors.RED}{distance_to_upper:.3f}%{Colors.RESET}"
        else:
            upper_formatted = f"{distance_to_upper:.3f}%"
            
        print_info(f"{symbol_prefix}BB Distance - Lower: {lower_formatted}, Upper: {upper_formatted}")
        
        # Show volatility if available
        if 'bb_width' in indicators:
            bb_width = indicators['bb_width']
            # Color based on volatility level
            if bb_width > 2.0:  # High volatility
                vol_formatted = f"{Colors.RED}Volatility: {bb_width:.3f}%{Colors.RESET} (High)"
            elif bb_width > 1.0:  # Medium volatility
                vol_formatted = f"{Colors.YELLOW}Volatility: {bb_width:.3f}%{Colors.RESET} (Medium)"
            else:  # Low volatility
                vol_formatted = f"{Colors.GREEN}Volatility: {bb_width:.3f}%{Colors.RESET} (Low)"
            print_info(f"{symbol_prefix}{vol_formatted}")
    
    # Display position information
    display_position_info(bot, current_price, symbol_prefix)