"""
Main entry point for dashboard generation
"""

import os
import argparse
from trading.dashboard.dashboard_single import generate_dashboard
from trading.dashboard.dashboard_combined import generate_combined_dashboard
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, format_profit, format_percentage, Colors
)

def dashboard_command():
    """Command-line entry point for generating the dashboard"""
    parser = argparse.ArgumentParser(description="Generate a high frequency trading bot dashboard")
    parser.add_argument('--dir', type=str, default='simulation_data', 
                        help="Directory containing simulation data (default: simulation_data)")
    parser.add_argument('--combined', action='store_true',
                        help="Generate combined dashboard for all symbols")
    parser.add_argument('--symbol', type=str, default=None,
                        help="Generate dashboard for specific symbol only")
    
    args = parser.parse_args()
    
    print_header("Generating High Frequency Trading Dashboard")
    
    try:
        if args.combined:
            if generate_combined_dashboard(args.dir):
                print_success("Combined dashboard generated successfully!")
            else:
                print_error("Failed to generate combined dashboard.")
        elif args.symbol:
            symbol_dir = os.path.join(args.dir, args.symbol.replace('/', '_'))
            if generate_dashboard(symbol_dir):
                print_success(f"Dashboard for {args.symbol} generated successfully!")
            else:
                print_error(f"Failed to generate dashboard for {args.symbol}.")
        else:
            # Generate dashboards for all symbols
            symbol_dirs = [d for d in os.listdir(args.dir) 
                         if os.path.isdir(os.path.join(args.dir, d)) and d != 'dashboard' and d != 'combined_dashboard']
            
            for symbol_dir in symbol_dirs:
                full_dir = os.path.join(args.dir, symbol_dir)
                symbol = symbol_dir.replace('_', '/')
                print_info(f"Generating dashboard for {symbol}...")
                generate_dashboard(full_dir)
            
            print_success("All individual dashboards generated successfully!")
            
            # Also generate the combined dashboard
            if generate_combined_dashboard(args.dir):
                print_success("Combined dashboard generated successfully!")
            else:
                print_error("Failed to generate combined dashboard.")
    
    except Exception as e:
        print_error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    dashboard_command()