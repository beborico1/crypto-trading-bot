"""
Enhanced dashboard for high frequency trading visualization
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import json
from datetime import datetime, timedelta
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
    Generate a comprehensive dashboard for the high frequency trading bot
    
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
        
        print_info(f"Generating high frequency dashboard from {len(balance_history)} data points...")
        
        # Create a multi-panel dashboard
        fig = plt.figure(figsize=(18, 14))
        fig.suptitle('High Frequency Trading Bot Simulation Dashboard', fontsize=18)
        
        gs = fig.add_gridspec(4, 3)
        
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
            
            # For high frequency trading, limit the number of markers to avoid crowding
            # Only show the most significant trades (e.g., those with largest impact)
            if len(trans_df) > 50:
                # Calculate trade impact as percentage change in value
                trans_df['impact'] = abs(trans_df['value'] / initial_value * 100)
                
                # Get the top trades by impact
                buy_markers = trans_df[trans_df['action'] == 'buy'].nlargest(25, 'impact')
                sell_markers = trans_df[trans_df['action'] == 'sell'].nlargest(25, 'impact')
                
                # Plot these significant trades
                for _, t in buy_markers.iterrows():
                    price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                    if price is not None:
                        ax1.scatter(t['timestamp'], price, marker='^', color='g', s=80, zorder=5, label='Buy' if 'Buy' not in ax1.get_legend_handles_labels()[1] else "")
                
                for _, t in sell_markers.iterrows():
                    price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                    if price is not None:
                        ax1.scatter(t['timestamp'], price, marker='v', color='r', s=80, zorder=5, label='Sell' if 'Sell' not in ax1.get_legend_handles_labels()[1] else "")
            else:
                # If we have fewer trades, show them all
                for _, t in trans_df.iterrows():
                    if t['action'] == 'buy':
                        price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                        if price is not None:
                            ax1.scatter(t['timestamp'], price, marker='^', color='g', s=80, zorder=5, label='Buy' if 'Buy' not in ax1.get_legend_handles_labels()[1] else "")
                    else:  # sell
                        price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                        if price is not None:
                            ax1.scatter(t['timestamp'], price, marker='v', color='r', s=80, zorder=5, label='Sell' if 'Sell' not in ax1.get_legend_handles_labels()[1] else "")
        
        ax1.legend()
        
        # 2. Price History
        ax2 = fig.add_subplot(gs[1, 0:2])
        ax2.plot(balance_df['timestamp'], balance_df['price'], 'r-', linewidth=2)
        ax2.set_title(f'Price History')
        ax2.set_ylabel('Price (USDT)')
        ax2.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
        ax2.grid(True)
        
        # 3. Performance (%)
        ax3 = fig.add_subplot(gs[1, 2])
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
        
        # 5. Trade Frequency Over Time
        ax5 = fig.add_subplot(gs[2, 1])
        if transactions:
            # Convert transaction timestamps to datetime
            trans_df = pd.DataFrame(transactions)
            trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
            
            # Resample to get trade counts by minute
            trans_df.set_index('timestamp', inplace=True)
            trade_freq = trans_df.resample('1T').size().reset_index()
            trade_freq.columns = ['timestamp', 'trades_per_minute']
            
            # Plot trade frequency
            ax5.bar(trade_freq['timestamp'], trade_freq['trades_per_minute'], color='blue', alpha=0.7)
            ax5.set_title('Trade Frequency (per minute)')
            ax5.set_ylabel('Trades')
            ax5.grid(axis='y')
        else:
            ax5.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax5.transAxes)
            ax5.set_title('Trade Frequency')
        
        # 6. Performance metrics
        ax6 = fig.add_subplot(gs[2, 2])
        ax6.axis('off')  # Turn off axis
        
        # Calculate metrics
        current_value = balance_df['total_value_in_quote'].iloc[-1]
        absolute_return = current_value - initial_value
        percent_return = (absolute_return / initial_value) * 100
        
        # Calculate drawdown
        balance_df['rolling_max'] = balance_df['total_value_in_quote'].cummax()
        balance_df['drawdown'] = (balance_df['total_value_in_quote'] / balance_df['rolling_max'] - 1) * 100
        max_drawdown = balance_df['drawdown'].min()
        
        # Calculate trade metrics
        if transactions:
            trans_df = pd.DataFrame(transactions)
            num_trades = len(transactions)
            buy_count = len(trans_df[trans_df['action'] == 'buy'])
            sell_count = len(trans_df[trans_df['action'] == 'sell'])
            
            # Calculate trades per minute
            if len(trans_df) >= 2:
                trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
                start_time = trans_df['timestamp'].min()
                end_time = trans_df['timestamp'].max()
                duration_minutes = (end_time - start_time).total_seconds() / 60
                
                if duration_minutes > 0:
                    trades_per_minute = num_trades / duration_minutes
                else:
                    trades_per_minute = num_trades  # Avoid division by zero
            else:
                trades_per_minute = 0
                
            # Calculate win rate for completed trade pairs
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
        else:
            num_trades = 0
            buy_count = 0
            sell_count = 0
            trades_per_minute = 0
            win_rate = 0
            avg_profit = 0
        
        # Format metrics with colors
        if absolute_return >= 0:
            abs_return_str = f"+${absolute_return:.2f}"
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
        
        # Add text with metrics
        metrics_text = (
            f"Initial Balance: ${initial_value:.2f}\n"
            f"Current Balance: ${current_value:.2f}\n"
            f"Absolute Return: {abs_return_str} ({abs_return_color})\n"
            f"Percent Return: {pct_return_str} ({pct_return_color})\n"
            f"Max Drawdown: {max_drawdown:.2f}%\n"
            f"Number of Trades: {num_trades}\n"
            f"Trade Frequency: {trades_per_minute:.2f} per minute\n"
            f"Win Rate: {win_rate:.1f}% ({win_rate_color})\n"
            f"Avg Profit per Trade: {avg_profit:.2f}% ({avg_profit_color})\n"
            f"Start Date: {balance_df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"End Date: {balance_df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        ax6.text(0.05, 0.95, metrics_text, transform=ax6.transAxes, va='top', fontsize=11, linespacing=1.5)
        ax6.set_title('Performance Metrics')
        
        # 7. Trade profit distribution
        ax7 = fig.add_subplot(gs[3, 0])
        if profits:
            profit_bins = np.linspace(min(profits), max(profits), 20)
            ax7.hist(profits, bins=profit_bins, color='blue', alpha=0.7)
            ax7.axvline(x=0, color='k', linestyle='--', alpha=0.5)
            ax7.set_title('Trade Profit Distribution (%)')
            ax7.set_xlabel('Profit/Loss (%)')
            ax7.set_ylabel('Number of Trades')
            ax7.grid(axis='y')
        else:
            ax7.text(0.5, 0.5, 'No completed trades yet', horizontalalignment='center', verticalalignment='center', transform=ax7.transAxes)
            ax7.set_title('Trade Profit Distribution')
            
        # 8. Hourly performance
        ax8 = fig.add_subplot(gs[3, 1])
        if len(balance_df) > 1:
            # Calculate hourly returns
            balance_df['hour'] = balance_df['timestamp'].dt.hour
            hourly_data = balance_df.groupby('hour')['performance'].mean().reset_index()
            
            bars = ax8.bar(hourly_data['hour'], hourly_data['performance'], color=[
                'g' if x >= 0 else 'r' for x in hourly_data['performance']
            ])
            
            # Add value labels to bars
            for bar in bars:
                height = bar.get_height()
                if height >= 0:
                    y_pos = height + 0.05
                else:
                    y_pos = height - 0.1
                ax8.text(bar.get_x() + bar.get_width()/2., y_pos,
                        f'{height:.2f}%', ha='center', va='bottom', fontsize=8)
            
            ax8.set_title('Average Performance by Hour')
            ax8.set_xlabel('Hour of Day')
            ax8.set_ylabel('Avg Return (%)')
            ax8.set_xticks(range(0, 24))
            ax8.grid(axis='y')
        else:
            ax8.text(0.5, 0.5, 'Not enough data yet', horizontalalignment='center', verticalalignment='center', transform=ax8.transAxes)
            ax8.set_title('Hourly Performance')
        
        # 9. Trade size distribution (specific to high frequency trading)
        ax9 = fig.add_subplot(gs[3, 2])
        if transactions:
            trans_df = pd.DataFrame(transactions)
            if 'amount' in trans_df.columns:
                # Create histogram of trade sizes
                ax9.hist(trans_df['amount'], bins=20, color='purple', alpha=0.7)
                ax9.set_title('Trade Size Distribution')
                ax9.set_xlabel('Trade Size')
                ax9.set_ylabel('Number of Trades')
                ax9.grid(axis='y')
            else:
                ax9.text(0.5, 0.5, 'Trade size data not available', horizontalalignment='center', verticalalignment='center', transform=ax9.transAxes)
                ax9.set_title('Trade Size Distribution')
        else:
            ax9.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax9.transAxes)
            ax9.set_title('Trade Size Distribution')
        
        # Format dates on x-axis
        for ax in [ax1, ax2, ax3, ax5]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        # Save the dashboard
        dashboard_path = os.path.join(dashboard_dir, 'hft_dashboard.png')
        plt.savefig(dashboard_path)
        plt.close()
        
        print_success(f"High frequency trading dashboard saved to: {dashboard_path}")
        
        # Create a separate trading activity heat map to visualize trade frequency
        if transactions and len(trans_df) > 10:
            plt.figure(figsize=(15, 8))
            
            # Convert transaction timestamps to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(trans_df['timestamp']):
                trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
            
            # Extract hour and minute
            trans_df['hour'] = trans_df['timestamp'].dt.hour
            trans_df['minute'] = trans_df['timestamp'].dt.minute
            
            # Create pivot table for heatmap
            heatmap_data = pd.pivot_table(
                trans_df,
                values='timestamp',
                index='hour',
                columns='minute',
                aggfunc='count',
                fill_value=0
            )
            
            # Plot heatmap
            plt.imshow(heatmap_data, cmap='viridis', aspect='auto', interpolation='nearest')
            plt.colorbar(label='Number of Trades')
            plt.title('Trade Activity Heatmap by Hour and Minute')
            plt.xlabel('Minute')
            plt.ylabel('Hour')
            
            # Set x-ticks to show every 5 minutes
            plt.xticks(np.arange(0, 60, 5), np.arange(0, 60, 5))
            plt.yticks(np.arange(0, 24), np.arange(0, 24))
            
            heatmap_path = os.path.join(dashboard_dir, 'trade_activity_heatmap.png')
            plt.tight_layout()
            plt.savefig(heatmap_path)
            plt.close()
            
            print_success(f"Trade activity heatmap saved to: {heatmap_path}")
            
        # Create a price volatility chart for intraday analysis
        if len(balance_df) > 10:
            plt.figure(figsize=(15, 6))
            
            # Calculate price volatility (rolling std of price changes)
            if 'price' in balance_df.columns:
                balance_df['price_pct_change'] = balance_df['price'].pct_change() * 100
                balance_df['volatility'] = balance_df['price_pct_change'].rolling(10).std()
                
                # Plot volatility
                plt.plot(balance_df['timestamp'], balance_df['volatility'], 'b-', linewidth=2)
                plt.fill_between(balance_df['timestamp'], balance_df['volatility'], color='blue', alpha=0.2)
                plt.title('Price Volatility (10-period Rolling Standard Deviation)')
                plt.ylabel('Volatility (%)')
                plt.grid(True)
                
                # Format x-axis dates
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=45)
                
                volatility_path = os.path.join(dashboard_dir, 'price_volatility.png')
                plt.tight_layout()
                plt.savefig(volatility_path)
                plt.close()
                
                print_success(f"Price volatility chart saved to: {volatility_path}")
        
        # Print summary in terminal
        print_header("High Frequency Trading Dashboard Generation Complete")
        print_info(f"Initial Balance: ${initial_value:.2f}")
        print_info(f"Current Balance: ${current_value:.2f}")
        print_info(f"Absolute Return: {format_profit(absolute_return)}")
        print_info(f"Percent Return: {format_percentage(percent_return)}")
        print_info(f"Max Drawdown: {format_percentage(max_drawdown, include_sign=False)}")
        print_info(f"Total Trades: {num_trades} (Buys: {buy_count}, Sells: {sell_count})")
        print_info(f"Trading Frequency: {trades_per_minute:.2f} trades per minute")
        print_info(f"Win Rate: {format_percentage(win_rate, include_sign=False)}")
        print_info(f"Avg Profit per Trade: {format_percentage(avg_profit)}")
        
        return True
        
    except Exception as e:
        print_error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def dashboard_command():
    """Command-line entry point for generating the dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a high frequency trading bot dashboard")
    parser.add_argument('--dir', type=str, default='simulation_data', 
                        help="Directory containing simulation data (default: simulation_data)")
    
    args = parser.parse_args()
    
    print_header("Generating High Frequency Trading Dashboard")
    
    if generate_dashboard(args.dir):
        print_success("Dashboard generated successfully!")
    else:
        print_error("Failed to generate dashboard.")

if __name__ == "__main__":
    dashboard_command()