"""
Dashboard for the cryptocurrency trading bot.
Provides visualization of performance and trading history.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import json
from datetime import datetime
import numpy as np
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, format_profit, format_percentage, Colors
)

def dollar_formatter(x, pos):
    """Format y-axis values as dollars"""
    return f'${x:.2f}'

def generate_dashboard(output_dir='simulation_data'):
    """
    Generate a comprehensive dashboard for the trading bot
    
    Parameters:
    output_dir (str): Directory to read data from and save charts to
    
    Returns:
    bool: Success indicator
    """
    try:
        # Check if data files exist
        data_file = os.path.join(output_dir, 'simulation_data.json')
        if not os.path.exists(data_file):
            print_error(f"Data file not found at {data_file}")
            return False
        
        # Load simulation data
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        balance_history = data.get('balance_history', [])
        transactions = data.get('transactions', [])
        
        if not balance_history:
            print_error("No balance history found in data file")
            return False
        
        # Convert to DataFrame
        balance_df = pd.DataFrame(balance_history)
        balance_df['timestamp'] = pd.to_datetime(balance_df['timestamp'])
        
        # Add performance metrics
        initial_value = balance_df['total_value_in_quote'].iloc[0]
        balance_df['performance'] = (balance_df['total_value_in_quote'] / initial_value - 1) * 100
        
        # Create a subdirectory for the dashboard
        dashboard_dir = os.path.join(output_dir, 'dashboard')
        os.makedirs(dashboard_dir, exist_ok=True)
        
        print_info(f"Generating dashboard from {len(balance_history)} data points...")
        
        # Create a multi-panel dashboard
        fig = plt.figure(figsize=(15, 12))
        fig.suptitle('Trading Bot Simulation Dashboard', fontsize=16)
        
        gs = fig.add_gridspec(3, 2)
        
        # 1. Total Value Over Time
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(balance_df['timestamp'], balance_df['total_value_in_quote'], 'b-', linewidth=2)
        ax1.set_title('Total Portfolio Value')
        ax1.set_ylabel('Value (USDT)')
        ax1.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
        ax1.grid(True)
        
        # Add buy/sell markers if transactions exist
        if transactions:
            trans_df = pd.DataFrame(transactions)
            trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
            
            for _, t in trans_df.iterrows():
                if t['action'] == 'buy':
                    price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                    if price is not None:
                        ax1.scatter(t['timestamp'], price, marker='^', color='g', s=100, zorder=5, label='Buy' if 'Buy' not in ax1.get_legend_handles_labels()[1] else "")
                else:  # sell
                    price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                    if price is not None:
                        ax1.scatter(t['timestamp'], price, marker='v', color='r', s=100, zorder=5, label='Sell' if 'Sell' not in ax1.get_legend_handles_labels()[1] else "")
        
        ax1.legend()
        
        # 2. Price History
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(balance_df['timestamp'], balance_df['price'], 'r-', linewidth=2)
        ax2.set_title(f'Price History')
        ax2.set_ylabel('Price (USDT)')
        ax2.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
        ax2.grid(True)
        
        # 3. Performance (%)
        ax3 = fig.add_subplot(gs[1, 1])
        # Color positive returns green and negative returns red
        positive_mask = balance_df['performance'] >= 0
        negative_mask = balance_df['performance'] < 0
        
        ax3.plot(balance_df.loc[positive_mask, 'timestamp'], 
                balance_df.loc[positive_mask, 'performance'], 
                'g-', linewidth=2)
        ax3.plot(balance_df.loc[negative_mask, 'timestamp'], 
                balance_df.loc[negative_mask, 'performance'], 
                'r-', linewidth=2)
        
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax3.set_title('Performance (%)')
        ax3.set_ylabel('Return (%)')
        ax3.grid(True)
        
        # 4. Trade distribution
        ax4 = fig.add_subplot(gs[2, 0])
        if transactions:
            trans_df = pd.DataFrame(transactions)
            trade_types = trans_df['action'].value_counts()
            colors = ['g' if x == 'buy' else 'r' for x in trade_types.index]
            ax4.bar(trade_types.index, trade_types.values, color=colors)
            ax4.set_title('Trade Distribution')
            ax4.set_ylabel('Number of Trades')
            ax4.grid(axis='y')
        else:
            ax4.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax4.transAxes)
            ax4.set_title('Trade Distribution')
        
        # 5. Performance metrics
        ax5 = fig.add_subplot(gs[2, 1])
        ax5.axis('off')  # Turn off axis
        
        # Calculate metrics
        current_value = balance_df['total_value_in_quote'].iloc[-1]
        absolute_return = current_value - initial_value
        percent_return = (absolute_return / initial_value) * 100
        
        # Calculate drawdown
        balance_df['rolling_max'] = balance_df['total_value_in_quote'].cummax()
        balance_df['drawdown'] = (balance_df['total_value_in_quote'] / balance_df['rolling_max'] - 1) * 100
        max_drawdown = balance_df['drawdown'].min()
        
        # Calculate win rate
        if transactions:
            buy_prices = []
            sell_prices = []
            profits = []
            
            for t in transactions:
                if t['action'] == 'buy':
                    buy_prices.append(t['price'])
                elif t['action'] == 'sell' and buy_prices:
                    sell_prices.append(t['price'])
                    # Calculate profit/loss for completed trades
                    if buy_prices and sell_prices:
                        buy_price = buy_prices.pop(0)  # FIFO
                        sell_price = sell_prices[-1]
                        profit = (sell_price / buy_price - 1) * 100
                        profits.append(profit)
            
            win_rate = sum(1 for p in profits if p > 0) / len(profits) * 100 if profits else 0
            avg_profit = sum(profits) / len(profits) if profits else 0
            num_trades = len(transactions)
        else:
            win_rate = 0
            avg_profit = 0
            num_trades = 0
        
        # Format metrics with colors
        if absolute_return >= 0:
            abs_return_str = f"${absolute_return:.2f}"
            abs_return_color = "green"
        else:
            abs_return_str = f"-${abs(absolute_return):.2f}"
            abs_return_color = "red"
            
        if percent_return >= 0:
            pct_return_str = f"+{percent_return:.2f}%"
            pct_return_color = "green"
        else:
            pct_return_str = f"{percent_return:.2f}%"
            pct_return_color = "red"
            
        win_rate_color = "green" if win_rate > 50 else "red"
        avg_profit_color = "green" if avg_profit > 0 else "red"
        
        # Add text with metrics - using HTML-like formatting for colors in matplotlib
        metrics_text = (
            f"Initial Balance: ${initial_value:.2f}\n"
            f"Current Balance: ${current_value:.2f}\n"
            f"Absolute Return: {abs_return_str} ({abs_return_color})\n"
            f"Percent Return: {pct_return_str} ({pct_return_color})\n"
            f"Max Drawdown: {max_drawdown:.2f}%\n"
            f"Number of Trades: {num_trades}\n"
            f"Win Rate: {win_rate:.1f}% ({win_rate_color})\n"
            f"Avg Profit per Trade: {avg_profit:.2f}% ({avg_profit_color})\n"
            f"Start Date: {balance_df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M')}\n"
            f"End Date: {balance_df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M')}"
        )
        
        ax5.text(0.05, 0.95, metrics_text, transform=ax5.transAxes, va='top', fontsize=11, linespacing=1.5)
        ax5.set_title('Performance Metrics')
        
        # Format dates on x-axis
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # Save the dashboard
        dashboard_path = os.path.join(dashboard_dir, 'trading_dashboard.png')
        plt.savefig(dashboard_path)
        plt.close()
        
        print_success(f"Dashboard saved to: {dashboard_path}")
        
        # Create a daily performance chart
        daily_data = balance_df.copy()
        daily_data['date'] = daily_data['timestamp'].dt.date
        daily_performance = daily_data.groupby('date')['total_value_in_quote'].last().reset_index()
        daily_performance['performance'] = daily_performance['total_value_in_quote'].pct_change() * 100
        
        if len(daily_performance) > 1:
            fig, ax = plt.subplots(figsize=(12, 6))
            colors = ['g' if x >= 0 else 'r' for x in daily_performance['performance'].iloc[1:]]
            ax.bar(range(len(daily_performance) - 1), daily_performance['performance'].iloc[1:], color=colors)
            ax.set_xticks(range(len(daily_performance) - 1))
            ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in daily_performance['date'].iloc[1:]], rotation=45)
            ax.set_title('Daily Performance (%)')
            ax.set_ylabel('Daily Return (%)')
            ax.grid(axis='y')
            
            daily_path = os.path.join(dashboard_dir, 'daily_performance.png')
            plt.tight_layout()
            plt.savefig(daily_path)
            plt.close()
            
            print_success(f"Daily performance chart saved to: {daily_path}")
        
        # Print summary in terminal
        print_header("Dashboard Generation Complete")
        print_info(f"Initial Balance: ${initial_value:.2f}")
        print_info(f"Current Balance: ${current_value:.2f}")
        print_info(f"Absolute Return: {format_profit(absolute_return)}")
        print_info(f"Percent Return: {format_percentage(percent_return)}")
        print_info(f"Max Drawdown: {format_percentage(max_drawdown, include_sign=False)}")
        print_info(f"Win Rate: {format_percentage(win_rate, include_sign=False)}")
        
        return True
        
    except Exception as e:
        print_error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def dashboard_command():
    """Command-line entry point for generating the dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a trading bot dashboard")
    parser.add_argument('--dir', type=str, default='simulation_data', 
                        help="Directory containing simulation data (default: simulation_data)")
    
    args = parser.parse_args()
    
    print_header("Generating Trading Dashboard")
    
    if generate_dashboard(args.dir):
        print_success("Dashboard generated successfully!")
    else:
        print_error("Failed to generate dashboard.")

if __name__ == "__main__":
    dashboard_command()