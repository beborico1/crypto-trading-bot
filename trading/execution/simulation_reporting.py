"""
Enhanced simulation reporting module for the trading bot.
Handles detailed logging of simulation state for high frequency trading.
"""

from datetime import datetime
from utils.terminal_colors import (
    print_simulation, print_success, print_info, 
    format_profit, format_percentage, Colors
)

def log_simulation_state(bot, current_price, action=None, amount=None, price=None):
    """
    Log detailed information about the current simulation state for high frequency trading

    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    action (str, optional): Trade action ('buy' or 'sell')
    amount (float, optional): Amount traded 
    price (float, optional): Price at which the trade occurred
    """
    if not bot.in_simulation_mode or not bot.sim_tracker:
        return
        
    # Get current balance information
    balance = bot.sim_tracker.get_current_balance(current_price)
    base_currency = bot.symbol.split('/')[0]
    quote_currency = bot.symbol.split('/')[1]
    
    # Get current timestamp for high-frequency display
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # Print action header if this is after a trade
    if action and amount and price:
        print_simulation(f"=== HF TRADE {timestamp}: {action.upper()} {amount} {base_currency} @ ${price:.2f} ===")
    else:
        print_simulation(f"=== BALANCE UPDATE {timestamp} ===")
    
    # Print core balance information
    print_simulation(f"Balance: {balance['quote_balance']:.2f} {quote_currency} | "
                   f"{balance['base_balance']:.6f} {base_currency}")
    
    # Calculate value of holdings
    base_value = balance['base_balance'] * current_price
    total_value = balance['total_value_in_quote']
    base_pct = (base_value / total_value * 100) if total_value > 0 else 0
    quote_pct = (balance['quote_balance'] / total_value * 100) if total_value > 0 else 0
    
    # Print value distribution
    print_simulation(f"Value: {total_value:.2f} {quote_currency} @ ${current_price:.2f}")
    
    # Print profit/loss if available
    if 'profit_loss' in balance and 'profit_loss_pct' in balance:
        profit_formatted = format_profit(balance['profit_loss'])
        pct_formatted = format_percentage(balance['profit_loss_pct'])
        print_simulation(f"P/L: {profit_formatted} {quote_currency} ({pct_formatted})")
    
    # Print trade counts if available
    if hasattr(bot.sim_tracker, 'transaction_history'):
        trade_count = len(bot.sim_tracker.transaction_history)
        buy_count = sum(1 for t in bot.sim_tracker.transaction_history if t['action'] == 'buy')
        sell_count = sum(1 for t in bot.sim_tracker.transaction_history if t['action'] == 'sell')
        
        # For high frequency trading, show recent trade rate
        recent_trades = 0
        if trade_count > 0:
            # Count trades in the last minute
            now = datetime.now()
            recent_trades = sum(1 for t in bot.sim_tracker.transaction_history 
                              if (now - datetime.fromisoformat(t['timestamp'])).total_seconds() < 60)
        
        print_simulation(f"Trades: {trade_count} total | {recent_trades}/min rate | {buy_count} buys | {sell_count} sells")

def log_simulation_trade_detail(bot, action, amount, price, current_price):
    """
    Log detailed information about a specific simulation trade for high frequency trading

    Parameters:
    bot (CryptoTradingBot): Bot instance
    action (str): Trade action ('buy' or 'sell')
    amount (float): Amount traded
    price (float): Price at which the trade occurred
    current_price (float): Current market price
    """
    if not bot.in_simulation_mode or not bot.sim_tracker:
        return
    
    base_currency = bot.symbol.split('/')[0]
    quote_currency = bot.symbol.split('/')[1]
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    if action.lower() == 'buy':
        cost = amount * price * 1.001  # Including 0.1% fee
        print_simulation(f"[{timestamp}] Bought {amount} {base_currency} at ${price:.2f}")
        print_simulation(f"Cost: {cost:.4f} {quote_currency} (with 0.1% fee)")
        
        # Show position information
        if bot.position_entry_prices:
            avg_entry = sum(p[0] * p[1] for p in bot.position_entry_prices) / sum(p[0] for p in bot.position_entry_prices)
            print_simulation(f"Avg entry: ${avg_entry:.2f} | Position: {bot.current_position_size} {base_currency} "
                           f"({bot.current_position_size / (bot.max_position_size * bot.base_position_size) * 100:.1f}% of max)")
        
    elif action.lower() == 'sell':
        proceeds = amount * price * 0.999  # After 0.1% fee
        print_simulation(f"[{timestamp}] Sold {amount} {base_currency} at ${price:.2f}")
        print_simulation(f"Proceeds: {proceeds:.4f} {quote_currency} (after 0.1% fee)")
        
        # Calculate profit/loss
        if hasattr(bot, 'position_entry_prices') and bot.position_entry_prices:
            # Calculate profit for this specific sale if possible
            # For simplicity, use FIFO approach (first in, first out)
            entry_price = 0
            for pos_amount, pos_price in bot.position_entry_prices:
                if pos_amount > 0 and pos_price > 0:
                    entry_price = pos_price
                    break
                    
            if entry_price > 0:
                profit_pct = ((price / entry_price) - 1) * 100
                profit_formatted = format_percentage(profit_pct)
                print_simulation(f"Trade P/L: {profit_formatted}")
        
        # Print remaining position
        print_simulation(f"Remaining: {bot.current_position_size} {base_currency} "
                       f"({bot.current_position_size / (bot.max_position_size * bot.base_position_size) * 100:.1f}% of max)")