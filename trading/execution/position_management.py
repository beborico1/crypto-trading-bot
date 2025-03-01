"""
Position management module for the trading bot.
Handles entry price tracking and risk management.
"""

from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_simulation, format_profit, format_percentage, Colors
)
from trading.order import execute_trade
from trading.execution.simulation_reporting import log_simulation_state, log_simulation_trade_detail

def update_position_entry_prices(bot, sell_amount):
    """
    Update position entry prices after a sell
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    sell_amount (float): Amount sold
    """
    remaining_to_sell = sell_amount
    new_entry_prices = []
    
    # Loop through positions, starting from oldest (FIFO approach)
    for position_amount, entry_price in bot.position_entry_prices:
        if remaining_to_sell <= 0:
            # No more to sell, keep this position
            new_entry_prices.append((position_amount, entry_price))
        elif remaining_to_sell >= position_amount:
            # Sell entire position
            remaining_to_sell -= position_amount
        else:
            # Sell part of position
            new_amount = position_amount - remaining_to_sell
            new_entry_prices.append((new_amount, entry_price))
            remaining_to_sell = 0
    
    # Update the list of entry prices
    bot.position_entry_prices = new_entry_prices

def handle_risk_management(bot, current_price):
    """
    Handle risk management including take profit and stop loss
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    
    Returns:
    bool: True if any risk management action was taken
    """
    if bot.current_position_size <= 0 or not bot.position_entry_prices:
        return False
    
    action_taken = False
    positions_to_close = []
    
    # Check each position individually for take profit/stop loss
    for i, (position_amount, entry_price) in enumerate(bot.position_entry_prices):
        # Skip positions with zero entry price (recovered from existing simulation)
        if entry_price <= 0:
            continue
            
        price_change_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Take profit
        if price_change_pct >= bot.take_profit_percentage:
            print_sell(f"TAKE PROFIT triggered for position {i+1} at ${current_price:.2f} ({price_change_pct:.2f}%)")
            positions_to_close.append(i)
            action_taken = True
        
        # Stop loss
        elif price_change_pct <= -bot.stop_loss_percentage:
            print_sell(f"STOP LOSS triggered for position {i+1} at ${current_price:.2f} ({price_change_pct:.2f}%)")
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

def display_position_info(bot, current_price):
    """
    Display detailed position information
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    """
    if bot.current_position_size <= 0:
        print_info("No active positions")
        return
    
    print_info(f"Current position size: {bot.current_position_size} {bot.symbol.split('/')[0]}")
    print_info(f"Position utilization: {bot.current_position_size / (bot.max_position_size * bot.base_position_size) * 100:.2f}%")
    
    total_invested = 0
    current_value = bot.current_position_size * current_price
    
    print_info("----- POSITION DETAILS -----")
    for i, (position_amount, entry_price) in enumerate(bot.position_entry_prices):
        # Handle positions with unknown entry price
        if entry_price <= 0:
            print_info(f"Position {i+1}: {position_amount} @ unknown entry price")
            continue
            
        position_invested = position_amount * entry_price
        total_invested += position_invested
        
        position_value = position_amount * current_price
        position_pnl = position_value - position_invested
        position_pnl_pct = (position_pnl / position_invested) * 100
        
        pnl_formatted = format_profit(position_pnl)
        pnl_pct_formatted = format_percentage(position_pnl_pct)
        
        print_info(f"Position {i+1}: {position_amount} @ ${entry_price:.2f} | Current P/L: {pnl_formatted} ({pnl_pct_formatted})")
    
    # Overall P/L
    if total_invested > 0:
        total_pnl = current_value - total_invested
        total_pnl_pct = (total_pnl / total_invested) * 100
        
        total_pnl_formatted = format_profit(total_pnl)
        total_pnl_pct_formatted = format_percentage(total_pnl_pct)
        
        print_info(f"Overall Position: Cost basis: ${total_invested:.2f} | Value: ${current_value:.2f}")
        print_info(f"Overall P/L: {total_pnl_formatted} ({total_pnl_pct_formatted})")
    else:
        # If we don't have entry prices, just show current value
        print_info(f"Current value: ${current_value:.2f}")
    
    print_info("---------------------------")