"""
Bot execution module for the trading bot.
Coordinates the overall execution flow of the trading bot.
"""

import time
import config  # Import the config module directly
from datetime import datetime
from trading.dashboard import generate_dashboard
from trading.market_analysis import fetch_ohlcv_data, analyze_market
from trading.execution.trade_execution import process_signals
from trading.execution.market_display import display_market_info
from trading.execution.simulation_reporting import log_simulation_state
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, print_simulation, format_profit, format_percentage, Colors
)

def handle_market_update(bot, interval=config.CHECK_INTERVAL):
    """
    Handle regular market updates and trade execution with high frequency updates
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    interval (int): Seconds between each check
    """
    counter = 0
    
    # Print the high frequency trading info
    print_header("HIGH FREQUENCY TRADING MODE ACTIVATED")
    print_info(f"Checking market every {interval} seconds")
    print_info(f"Using ultra-short moving averages ({bot.short_window}/{bot.long_window})")
    print_info(f"Timeframe: {bot.timeframe}")
    
    while True:
        try:
            start_time = time.time()
            
            # Fetch the latest market data
            df = bot.analyze_market(limit=30)  # Reduced limit for faster processing
            
            if df is None or len(df) == 0:
                print_warning("Could not fetch market data. Retrying...")
                time.sleep(interval)
                continue
            
            # Get the current price
            current_price = df.iloc[-1]['close']
            
            # Always display balance info with each update
            if bot.in_simulation_mode and bot.sim_tracker:
                balance = bot.sim_tracker.get_current_balance(current_price)
                base_currency = bot.symbol.split('/')[0]
                quote_currency = bot.symbol.split('/')[1]
                
                print_header(f"BALANCE UPDATE ({datetime.now().strftime('%H:%M:%S')})")
                print_info(f"Balance: {balance['quote_balance']:.2f} {quote_currency} | "
                         f"{balance['base_balance']:.6f} {base_currency}")
                
                if 'profit_loss' in balance and 'profit_loss_pct' in balance:
                    profit_formatted = format_profit(balance['profit_loss'])
                    pct_formatted = format_percentage(balance['profit_loss_pct'])
                    print_info(f"P/L: {profit_formatted} {quote_currency} ({pct_formatted})")
            
            # Display market information
            display_market_info(bot, df, current_price)
            
            # Process trading signals
            process_signals(bot, df, current_price)
            
            # Update simulation tracker with current price
            if bot.in_simulation_mode and bot.sim_tracker:
                bot.sim_tracker.update_price(current_price)
                
                # Log simulation state every few updates
                if counter % config.UPDATE_DISPLAY_INTERVAL == 0:
                    log_simulation_state(bot, current_price)
                
                # Generate dashboard periodically
                if counter % config.GENERATE_DASHBOARD_INTERVAL == 0:
                    generate_dashboard()
            
            # Increment counter
            counter += 1
            
            # Calculate time taken for this update
            elapsed = time.time() - start_time
            
            # Print separator for next update
            wait_time = max(0.1, interval - elapsed)  # Ensure we wait at least 0.1 seconds
            print_info(f"Next update in {wait_time:.1f} seconds...")
            print_info("=" * 80)
            
            # Sleep until next update
            time.sleep(wait_time)
            
        except Exception as e:
            print_error(f"Error during market update: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(interval)