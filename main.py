#!/usr/bin/env python3
"""
Crypto Trading Bot - Entry Point
"""

import os
import argparse
import config
from trading.bot import CryptoTradingBot
from trading.order import check_balance
from trading.dashboard import generate_dashboard
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, Colors
)

def main():
    """Main entry point for the application"""
    
    print_header("Cryptocurrency Trading Bot")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Cryptocurrency Trading Bot')
    parser.add_argument('--symbol', type=str, default=config.DEFAULT_SYMBOL,
                        help=f'Trading pair symbol (default: {config.DEFAULT_SYMBOL})')
    parser.add_argument('--timeframe', type=str, default=config.DEFAULT_TIMEFRAME,
                        help=f'Candle timeframe (default: {config.DEFAULT_TIMEFRAME})')
    parser.add_argument('--amount', type=float, default=config.DEFAULT_TRADE_AMOUNT,
                        help=f'Amount to trade (default: {config.DEFAULT_TRADE_AMOUNT})')
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
                        help='Use standard MA crossover strategy instead of enhanced strategy')
    
    args = parser.parse_args()
    
    # Handle dashboard-only mode
    if args.dashboard_only:
        print_info("Dashboard generation mode")
        generate_dashboard()
        return
    
    # Determine simulation mode
    simulation_mode = args.simulation or config.SIMULATION_MODE
    
    # Display configuration
    print_info("Bot Configuration:")
    print_info(f"  Symbol: {Colors.CYAN}{args.symbol}{Colors.RESET}")
    print_info(f"  Timeframe: {Colors.CYAN}{args.timeframe}{Colors.RESET}")
    print_info(f"  Trade Amount: {Colors.CYAN}{args.amount}{Colors.RESET}")
    print_info(f"  Check Interval: {Colors.CYAN}{args.interval} seconds{Colors.RESET}")
    print_info(f"  MA Windows: {Colors.CYAN}{args.short_window}/{args.long_window}{Colors.RESET}")
    print_info(f"  Simulation Mode: {Colors.YELLOW if simulation_mode else Colors.GREEN}{simulation_mode}{Colors.RESET}")
    print_info(f"  Strategy: {Colors.MAGENTA}{'Enhanced' if not args.standard_strategy else 'Standard MA Crossover'}{Colors.RESET}")
    
    # Determine which strategy to use (enhanced by default)
    use_enhanced_strategy = not args.standard_strategy
    
    # Initialize the bot with configuration
    try:
        bot = CryptoTradingBot(
            symbol=args.symbol,
            timeframe=args.timeframe,
            api_key=config.API_KEY,
            base_url=config.BASE_URL,
            amount=args.amount,
            short_window=args.short_window,
            long_window=args.long_window,
            simulation_mode=simulation_mode,
            use_enhanced_strategy=use_enhanced_strategy
        )
        
        # Check balance before starting (if credentials are available and not in simulation mode)
        if config.API_KEY and not simulation_mode:
            check_balance(config.BASE_URL, config.API_KEY, args.symbol)
        
        # Run the bot
        bot.run_bot(interval=args.interval)
    
    except Exception as e:
        print_error(f"Error initializing bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\nBot stopped by user. Generating final dashboard...")
        generate_dashboard()
        print_success("Goodbye!")