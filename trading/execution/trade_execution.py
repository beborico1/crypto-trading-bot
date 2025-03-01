"""
Trade execution module for the trading bot.
Handles signal processing and order execution for high frequency trading.
"""

from datetime import datetime
from trading.order import execute_trade
from trading.market_analysis import get_signal_info, get_high_frequency_signal
from trading.execution.signal_processing import calculate_signal_strength, calculate_position_increment, calculate_sell_amount
from trading.execution.position_management import update_position_entry_prices, handle_risk_management, handle_high_frequency_risk_management
from trading.execution.simulation_reporting import log_simulation_state, log_simulation_trade_detail
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_simulation, Colors
)

def process_signals(bot, df, current_price, symbol_prefix=""):
    """
    Process trading signals and execute trades with enhanced high frequency logic
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    df (pandas.DataFrame): DataFrame with signals
    current_price (float): Current market price
    symbol_prefix (str): Prefix to use in log messages
    
    Returns:
    bool: True if signals were processed, False otherwise
    """
    if df is None or len(df) == 0 or current_price is None:
        return False
    
    # Get the latest high frequency signal
    position_change, price, ema1, ema3 = get_high_frequency_signal(df)
    
    # Use a more aggressive signal strength calculation for high frequency trading
    signal_strength = 0.8  # Default to fairly strong signals for high frequency trading
    
    # Handle risk management but with tighter thresholds for faster exits
    if bot.current_position_size > 0:
        # For high frequency trading, use custom risk management with tighter stops
        if bot.high_frequency_mode:
            risk_action_taken = handle_high_frequency_risk_management(bot, current_price, df, symbol_prefix)
        else:
            risk_action_taken = handle_risk_management(bot, current_price, symbol_prefix)
            
        if risk_action_taken:
            return True
    
    # Check if we can make a trade (based on frequency limits)
    if not bot.can_make_trade():
        return False
    
    # Check for buy signal
    if position_change == 1:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print_buy(f"{symbol_prefix}BUY SIGNAL at {timestamp} - Price: ${current_price:.2f}")
        
        # Calculate position increment based on signal strength
        increment_size = calculate_position_increment(bot, signal_strength)
        
        # Check if we can add to our position
        if bot.current_position_size < bot.max_position_size * bot.base_position_size:
            # Determine the amount to buy for this increment
            buy_amount = min(
                bot.base_position_size * increment_size,
                (bot.max_position_size * bot.base_position_size) - bot.current_position_size
            )
            
            # Only execute if the buy amount is significant
            if buy_amount >= bot.base_position_size * 0.1:  # Min 10% of base size
                if bot.in_simulation_mode and bot.sim_tracker:
                    # Execute simulated trade
                    if bot.sim_tracker.execute_trade('buy', buy_amount, current_price):
                        bot.current_position_size += buy_amount
                        bot.position_entry_prices.append((buy_amount, current_price))
                        print_success(f"{symbol_prefix}Added {buy_amount} to position at ${current_price:.2f}. Current size: {bot.current_position_size}")
                        
                        # Log detailed simulation information
                        log_simulation_trade_detail(bot, 'buy', buy_amount, current_price, current_price, symbol_prefix)
                        log_simulation_state(bot, current_price, 'buy', buy_amount, current_price, symbol_prefix)
                        
                        # Generate and save performance chart
                        bot.sim_tracker.plot_performance()
                elif not bot.in_simulation_mode:
                    # Execute real trade
                    if execute_trade('buy', bot.base_url, bot.api_key, bot.symbol, buy_amount):
                        bot.current_position_size += buy_amount
                        bot.position_entry_prices.append((buy_amount, current_price))
                        print_success(f"{symbol_prefix}Added {buy_amount} to position at ${current_price:.2f}. Current size: {bot.current_position_size}")
            else:
                print_warning(f"{symbol_prefix}Buy amount {buy_amount} too small - skipping")
        else:
            print_warning(f"{symbol_prefix}Maximum position size reached ({bot.current_position_size}) - skipping buy")
        return True
    
    # Check for sell signal
    elif position_change == -1:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print_sell(f"{symbol_prefix}SELL SIGNAL at {timestamp} - Price: ${current_price:.2f}")
        
        if bot.current_position_size > 0:
            # For high frequency trading, be more aggressive with sells
            sell_amount = min(bot.current_position_size, bot.base_position_size)
            
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated trade
                if bot.sim_tracker.execute_trade('sell', sell_amount, current_price):
                    bot.current_position_size -= sell_amount
                    # Update entry prices list (remove oldest entries first)
                    update_position_entry_prices(bot, sell_amount)
                    print_success(f"{symbol_prefix}Sold {sell_amount} at ${current_price:.2f}. Remaining position: {bot.current_position_size}")
                    
                    # Log detailed simulation information
                    log_simulation_trade_detail(bot, 'sell', sell_amount, current_price, current_price, symbol_prefix)
                    log_simulation_state(bot, current_price, 'sell', sell_amount, current_price, symbol_prefix)
                    
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real trade
                if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, sell_amount):
                    bot.current_position_size -= sell_amount
                    # Update entry prices list
                    update_position_entry_prices(bot, sell_amount)
                    print_success(f"{symbol_prefix}Sold {sell_amount} at ${current_price:.2f}. Remaining position: {bot.current_position_size}")
        else:
            print_warning(f"{symbol_prefix}No position to sell")
        return True
    
    # No signal
    else:
        # For high frequency trading, we don't need to print "no signal" every time
        # as it would flood the output
        return False