#!/usr/bin/env python3
"""
High Frequency Crypto Trading Bot - Entry Point
"""

import os
import argparse
import config
from trading.bot import CryptoTradingBot
from trading.order import check_balance
from trading.dashboard.dashboard_main import generate_dashboard, generate_combined_dashboard
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, Colors
)
from concurrent.futures import ThreadPoolExecutor
import threading

# Global list to track all trading bots
active_bots = []

def main():
    """Main entry point for the high frequency trading bot application"""
    
    print_header("High Frequency Multi-Cryptocurrency Trading Bot")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='High Frequency Cryptocurrency Trading Bot')
    parser.add_argument('--symbols', type=str, default=','.join(config.DEFAULT_SYMBOLS),
                        help=f'Trading pair symbols (default: {",".join(config.DEFAULT_SYMBOLS)})')
    parser.add_argument('--timeframe', type=str, default=config.DEFAULT_TIMEFRAME,
                        help=f'Candle timeframe (default: {config.DEFAULT_TIMEFRAME}) - use 30s for high frequency')
    parser.add_argument('--amount', type=float, default=config.DEFAULT_TRADE_AMOUNT,
                        help=f'Base amount to trade (default: {config.DEFAULT_TRADE_AMOUNT})')
    parser.add_argument('--interval', type=int, default=config.CHECK_INTERVAL,
                        help=f'Check interval in seconds (default: {config.CHECK_INTERVAL})')
    parser.add_argument('--short-window', type=int, default=config.SHORT_WINDOW,
                        help=f'Short moving average window (default: {config.SHORT_WINDOW})')
    parser.add_argument('--long-window', type=int, default=config.LONG_WINDOW,
                        help=f'Long moving average window (default: {config.LONG_WINDOW})')
    parser.add_argument('--simulation', action='store_true',
                        help='Force simulation mode even if credentials exist')
    parser.add_argument('--dashboard-only', action='store_true',
                        help='Generate dashboard from existing simulation data and exit')
    parser.add_argument('--standard-strategy', action='store_true',
                        help='Use standard MA crossover strategy instead of high frequency')
    parser.add_argument('--enhanced-strategy', action='store_true',
                        help='Use enhanced strategy instead of high frequency')
    parser.add_argument('--scalping-strategy', action='store_true',
                        help='Use scalping strategy instead of high frequency')
    parser.add_argument('--high-frequency', action='store_true',
                        help='Use high frequency trading strategy (default)')
    parser.add_argument('--take-profit', type=float, default=0.5,
                        help='Take profit percentage (default: 0.5% for high frequency)')
    parser.add_argument('--stop-loss', type=float, default=0.3,
                        help='Stop loss percentage (default: 0.3% for high frequency)')
    parser.add_argument('--max-position-size', type=float, default=15.0,
                        help='Maximum position size as multiple of base amount (default: 15.0)')
    parser.add_argument('--trade-limit', type=int, default=20,
                        help='Maximum trades per minute (default: 20)')
    parser.add_argument('--max-threads', type=int, default=10,
                        help='Maximum number of concurrent trading threads (default: 10)')
    
    args = parser.parse_args()
    
    # Parse symbols list
    symbols = [symbol.strip() for symbol in args.symbols.split(',')]
    
    # Handle dashboard-only mode
    if args.dashboard_only:
        print_info("Dashboard generation mode")
        # Generate individual dashboards
        for symbol in symbols:
            symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
            if os.path.exists(symbol_dir):
                print_info(f"Generating dashboard for {symbol}...")
                generate_dashboard(output_dir=symbol_dir)
        
        # Generate combined dashboard
        generate_combined_dashboard(output_dir=config.DATA_DIR)
        return
    
    # Determine simulation mode
    simulation_mode = args.simulation or config.SIMULATION_MODE
    
    # Determine strategy mode (priority: standard > enhanced > scalping > high-frequency)
    use_standard_strategy = args.standard_strategy
    use_enhanced_strategy = args.enhanced_strategy and not use_standard_strategy
    use_scalping_strategy = args.scalping_strategy and not use_standard_strategy and not use_enhanced_strategy
    use_high_frequency = (args.high_frequency or (not use_standard_strategy and not use_enhanced_strategy and not use_scalping_strategy))
    
    # Display configuration
    print_info("Bot Configuration:")
    print_info(f"  Symbols: {Colors.CYAN}{', '.join(symbols)}{Colors.RESET}")
    print_info(f"  Timeframe: {Colors.CYAN}{args.timeframe}{Colors.RESET}")
    print_info(f"  Base Trade Amount: {Colors.CYAN}{args.amount}{Colors.RESET}")
    print_info(f"  Max Position Size: {Colors.CYAN}{args.max_position_size}x base amount{Colors.RESET}")
    print_info(f"  Check Interval: {Colors.CYAN}{args.interval} seconds{Colors.RESET}")
    print_info(f"  MA Windows: {Colors.CYAN}{args.short_window}/{args.long_window}{Colors.RESET}")
    print_info(f"  Simulation Mode: {Colors.YELLOW if simulation_mode else Colors.GREEN}{simulation_mode}{Colors.RESET}")
    print_info(f"  Max Trading Threads: {Colors.CYAN}{args.max_threads}{Colors.RESET}")
    
    # Show strategy info
    if use_high_frequency:
        strategy_name = "High Frequency"
        strategy_color = Colors.RED
    elif use_scalping_strategy:
        strategy_name = "Scalping"
        strategy_color = Colors.MAGENTA
    elif use_enhanced_strategy:
        strategy_name = "Enhanced"
        strategy_color = Colors.BLUE
    else:
        strategy_name = "Standard MA Crossover"
        strategy_color = Colors.GREEN
    
    print_info(f"  Strategy: {strategy_color}{strategy_name}{Colors.RESET}")
    
    # Show take profit/stop loss settings based on strategy
    if use_high_frequency:
        print_info(f"  Take Profit: {Colors.GREEN}{args.take_profit}%{Colors.RESET} (High Frequency)")
        print_info(f"  Stop Loss: {Colors.RED}{args.stop_loss}%{Colors.RESET} (High Frequency)")
        print_info(f"  Max Trades Per Minute: {Colors.CYAN}{args.trade_limit}{Colors.RESET}")
    else:
        print_info(f"  Take Profit: {Colors.GREEN}{args.take_profit}%{Colors.RESET}")
        print_info(f"  Stop Loss: {Colors.RED}{args.stop_loss}%{Colors.RESET}")
    
    # Create data directories for each symbol
    for symbol in symbols:
        symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
        os.makedirs(symbol_dir, exist_ok=True)
    
    # Create and start a bot for each symbol using thread pool
    try:
        with ThreadPoolExecutor(max_workers=min(len(symbols), args.max_threads)) as executor:
            for symbol in symbols:
                print_header(f"Starting bot for {symbol}...")
                
                # Create data directory for this symbol
                symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
                
                # Initialize the bot with configuration
                bot = CryptoTradingBot(
                    symbol=symbol,
                    timeframe=args.timeframe,
                    api_key=config.API_KEY,
                    base_url=config.BASE_URL,
                    amount=args.amount,
                    short_window=args.short_window,
                    long_window=args.long_window,
                    simulation_mode=simulation_mode,
                    use_enhanced_strategy=use_enhanced_strategy,
                    use_scalping_strategy=use_scalping_strategy,
                    take_profit_percentage=args.take_profit,
                    stop_loss_percentage=args.stop_loss,
                    max_position_size=args.max_position_size,
                    high_frequency_mode=use_high_frequency,
                    data_dir=symbol_dir
                )
                
                # If high frequency mode, set the trade limit
                if use_high_frequency:
                    bot.minute_trade_limit = args.trade_limit
                
                # Add to global list of active bots
                active_bots.append(bot)
                
                # Check balance before starting (if credentials are available and not in simulation mode)
                if config.API_KEY and not simulation_mode:
                    check_balance(config.BASE_URL, config.API_KEY, symbol)
                
                # Submit bot to thread pool
                executor.submit(bot.run_bot, args.interval)
    
    except Exception as e:
        print_error(f"Error initializing bots: {e}")
        import traceback
        traceback.print_exc()
    
    # Wait for KeyboardInterrupt
    try:
        # Keep main thread alive
        main_thread = threading.current_thread()
        for thread in threading.enumerate():
            if thread is not main_thread:
                thread.join()
    except KeyboardInterrupt:
        print_warning("\nBots stopped by user. Generating final dashboards...")
        for symbol in symbols:
            symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
            generate_dashboard(output_dir=symbol_dir)
        
        # Generate combined dashboard
        generate_combined_dashboard(output_dir=config.DATA_DIR)
        print_success("Goodbye!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nBot stopped by user. Generating final dashboard...")
        for bot in active_bots:
            symbol_dir = os.path.join(config.DATA_DIR, bot.symbol.replace('/', '_'))
            generate_dashboard(output_dir=symbol_dir)
        
        # Generate combined dashboard
        generate_combined_dashboard(output_dir=config.DATA_DIR)
        print_success("Goodbye!")