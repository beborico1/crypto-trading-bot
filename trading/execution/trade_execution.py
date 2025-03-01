"""
Trade execution module for the trading bot.
Handles signal processing and order execution for high frequency trading.
"""

from datetime import datetime
from trading.order import execute_trade
from trading.market_analysis import get_signal_info, get_high_frequency_signal
from trading.execution.signal_processing import calculate_signal_strength, calculate_position_increment, calculate_sell_amount
from trading.execution.position_management import update_position_entry_prices, handle_risk_management
from trading.execution.simulation_reporting import log_simulation_state, log_simulation_trade_detail
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_simulation, Colors
)

def process_signals(bot, df, current_price):
    """
    Process trading signals and execute trades with enhanced high frequency logic
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    df (pandas.DataFrame): DataFrame with signals
    current_price (float): Current market price
    
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
        risk_action_taken = handle_high_frequency_risk_management(bot, current_price, df)
        if risk_action_taken:
            return True
    
    # Check for buy signal
    if position_change == 1:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print_buy(f"BUY SIGNAL at {timestamp} - Price: ${current_price:.2f}")
        
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
                        print_success(f"Added {buy_amount} to position at ${current_price:.2f}. Current size: {bot.current_position_size}")
                        
                        # Log detailed simulation information
                        log_simulation_trade_detail(bot, 'buy', buy_amount, current_price, current_price)
                        log_simulation_state(bot, current_price, 'buy', buy_amount, current_price)
                        
                        # Generate and save performance chart
                        bot.sim_tracker.plot_performance()
                elif not bot.in_simulation_mode:
                    # Execute real trade
                    if execute_trade('buy', bot.base_url, bot.api_key, bot.symbol, buy_amount):
                        bot.current_position_size += buy_amount
                        bot.position_entry_prices.append((buy_amount, current_price))
                        print_success(f"Added {buy_amount} to position at ${current_price:.2f}. Current size: {bot.current_position_size}")
            else:
                print_warning(f"Buy amount {buy_amount} too small - skipping")
        else:
            print_warning(f"Maximum position size reached ({bot.current_position_size}) - skipping buy")
        return True
    
    # Check for sell signal
    elif position_change == -1:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print_sell(f"SELL SIGNAL at {timestamp} - Price: ${current_price:.2f}")
        
        if bot.current_position_size > 0:
            # For high frequency trading, be more aggressive with sells
            sell_amount = min(bot.current_position_size, bot.base_position_size)
            
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated trade
                if bot.sim_tracker.execute_trade('sell', sell_amount, current_price):
                    bot.current_position_size -= sell_amount
                    # Update entry prices list (remove oldest entries first)
                    update_position_entry_prices(bot, sell_amount)
                    print_success(f"Sold {sell_amount} at ${current_price:.2f}. Remaining position: {bot.current_position_size}")
                    
                    # Log detailed simulation information
                    log_simulation_trade_detail(bot, 'sell', sell_amount, current_price, current_price)
                    log_simulation_state(bot, current_price, 'sell', sell_amount, current_price)
                    
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real trade
                if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, sell_amount):
                    bot.current_position_size -= sell_amount
                    # Update entry prices list
                    update_position_entry_prices(bot, sell_amount)
                    print_success(f"Sold {sell_amount} at ${current_price:.2f}. Remaining position: {bot.current_position_size}")
        else:
            print_warning("No position to sell")
        return True
    
    # No signal
    else:
        # For high frequency trading, we don't need to print "no signal" every time
        # as it would flood the output
        return False

def handle_high_frequency_risk_management(bot, current_price, df):
    """
    Handle risk management for high frequency trading with tighter thresholds
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    df (pandas.DataFrame): DataFrame with indicators
    
    Returns:
    bool: True if any risk management action was taken
    """
    if bot.current_position_size <= 0 or not bot.position_entry_prices:
        return False
    
    action_taken = False
    positions_to_close = []
    
    # Check for micro-trend reversal
    if len(df) >= 3:
        # Check for a short-term downtrend when we have a position
        micro_downtrend = (df['close'].iloc[-1] < df['close'].iloc[-2]) and (df['close'].iloc[-2] < df['close'].iloc[-3])
        
        # If we have a downtrend and a position, consider closing part of it
        if micro_downtrend:
            print_sell(f"MICRO TREND REVERSAL detected at ${current_price:.2f}")
            
            # Close oldest position
            if len(bot.position_entry_prices) > 0:
                positions_to_close.append(0)  # Close the oldest position
                action_taken = True
    
    # Check each position individually for take profit/stop loss with tighter thresholds
    for i, (position_amount, entry_price) in enumerate(bot.position_entry_prices):
        # Skip positions with zero entry price (recovered from existing simulation)
        if entry_price <= 0:
            continue
            
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Take profit - tighter for high frequency trading (e.g., 0.5% instead of 1.5%)
        if price_change_pct >= 0.5:  # Reduced from bot.take_profit_percentage
            print_sell(f"QUICK TAKE PROFIT triggered for position {i+1} at ${current_price:.2f} (+{price_change_pct:.2f}%)")
            positions_to_close.append(i)
            action_taken = True
        
        # Stop loss - also tighter for high frequency trading (e.g., 0.3% instead of 1.0%)
        elif price_change_pct <= -0.3:  # Reduced from bot.stop_loss_percentage
            print_sell(f"QUICK STOP LOSS triggered for position {i+1} at ${current_price:.2f} ({price_change_pct:.2f}%)")
            positions_to_close.append(i)
            action_taken = True
    
    # Close positions that hit TP/SL (starting from the end to avoid index shifts)
    for i in sorted(positions_to_close, reverse=True):
        position_amount = bot.position_entry_prices[i][0]
        
        if bot.in_simulation_mode and bot.sim_tracker:
            # Execute simulated sell for take profit/stop loss
            if bot.sim_tracker.execute_trade('sell', position_amount, current_price):
                print_success(f"Closed position of {position_amount} at ${current_price:.2f}")
                bot.current_position_size -= position_amount
                bot.position_entry_prices.pop(i)
                
                # Log detailed simulation information for risk management trades
                log_simulation_trade_detail(bot, 'sell', position_amount, current_price, current_price)
                log_simulation_state(bot, current_price, 'sell', position_amount, current_price)
                
                # Generate and save performance chart
                bot.sim_tracker.plot_performance()
        elif not bot.in_simulation_mode:
            # Execute real sell for take profit/stop loss
            if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, position_amount):
                print_success(f"Closed position of {position_amount} at ${current_price:.2f}")
                bot.current_position_size -= position_amount
                bot.position_entry_prices.pop(i)
    
    return action_taken