"""
Chart plotting functions for single symbol dashboard
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
from utils.terminal_colors import print_success

def plot_performance_chart(ax, balance_df):
    """Plot performance chart with positive/negative coloring"""
    # Color positive returns green and negative returns red
    positive_mask = balance_df['performance'] >= 0
    negative_mask = balance_df['performance'] < 0
    
    ax.plot(balance_df.loc[positive_mask, 'timestamp'], 
            balance_df.loc[positive_mask, 'performance'], 
            'g-', linewidth=2)
    ax.plot(balance_df.loc[negative_mask, 'timestamp'], 
            balance_df.loc[negative_mask, 'performance'], 
            'r-', linewidth=2)
    
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax.set_title('Performance (%)')
    ax.set_ylabel('Return (%)')
    ax.grid(True)

def plot_trade_distribution(ax, trans_df):
    """Plot trade distribution (buy/sell counts)"""
    if trans_df is not None:
        trade_types = trans_df['action'].value_counts()
        colors = ['g' if x == 'buy' else 'r' for x in trade_types.index]
        ax.bar(trade_types.index, trade_types.values, color=colors)
        ax.set_title('Trade Distribution')
        ax.set_ylabel('Number of Trades')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Trade Distribution')

def plot_trade_frequency(ax, trans_df):
    """Plot trade frequency over time"""
    if trans_df is not None:
        # Resample to get trade counts by minute
        df_copy = trans_df.copy()
        df_copy.set_index('timestamp', inplace=True)
        trade_freq = df_copy.resample('1T').size().reset_index()
        trade_freq.columns = ['timestamp', 'trades_per_minute']
        
        # Plot trade frequency
        ax.bar(trade_freq['timestamp'], trade_freq['trades_per_minute'], color='blue', alpha=0.7)
        ax.set_title('Trade Frequency (per minute)')
        ax.set_ylabel('Trades')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Trade Frequency')

def plot_performance_metrics(ax, symbol, initial_value, current_value, 
                           absolute_return, percent_return, max_drawdown, 
                           trade_metrics, balance_df):
    """Plot performance metrics text box"""
    ax.axis('off')  # Turn off axis
    
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
        
    win_rate_color = "green" if trade_metrics['win_rate'] > 50 else "red"
    avg_profit_color = "green" if trade_metrics['avg_profit'] > 0 else "red"
    
    # Add text with metrics
    metrics_text = (
        f"Symbol: {symbol}\n"
        f"Initial Balance: ${initial_value:.2f}\n"
        f"Current Balance: ${current_value:.2f}\n"
        f"Absolute Return: {abs_return_str} ({abs_return_color})\n"
        f"Percent Return: {pct_return_str} ({pct_return_color})\n"
        f"Max Drawdown: {max_drawdown:.2f}%\n"
        f"Number of Trades: {trade_metrics['num_trades']}\n"
        f"Trade Frequency: {trade_metrics['trades_per_minute']:.2f} per minute\n"
        f"Win Rate: {trade_metrics['win_rate']:.1f}% ({win_rate_color})\n"
        f"Avg Profit per Trade: {trade_metrics['avg_profit']:.2f}% ({avg_profit_color})\n"
        f"Start Date: {balance_df['timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"End Date: {balance_df['timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes, va='top', fontsize=11, linespacing=1.5)
    ax.set_title('Performance Metrics')

def plot_profit_distribution(ax, profits):
    """Plot trade profit distribution histogram"""
    if profits:
        profit_bins = np.linspace(min(profits), max(profits), 20)
        ax.hist(profits, bins=profit_bins, color='blue', alpha=0.7)
        ax.axvline(x=0, color='k', linestyle='--', alpha=0.5)
        ax.set_title('Trade Profit Distribution (%)')
        ax.set_xlabel('Profit/Loss (%)')
        ax.set_ylabel('Number of Trades')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, 'No completed trades yet', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Trade Profit Distribution')

def plot_hourly_performance(ax, balance_df):
    """Plot performance breakdown by hour"""
    if len(balance_df) > 1:
        # Calculate hourly returns
        balance_df['hour'] = balance_df['timestamp'].dt.hour
        hourly_data = balance_df.groupby('hour')['performance'].mean().reset_index()
        
        bars = ax.bar(hourly_data['hour'], hourly_data['performance'], color=[
            'g' if x >= 0 else 'r' for x in hourly_data['performance']
        ])
        
        # Add value labels to bars
        for bar in bars:
            height = bar.get_height()
            if height >= 0:
                y_pos = height + 0.05
            else:
                y_pos = height - 0.1
            ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                    f'{height:.2f}%', ha='center', va='bottom', fontsize=8)
        
        ax.set_title('Average Performance by Hour')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Avg Return (%)')
        ax.set_xticks(range(0, 24))
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, 'Not enough data yet', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Hourly Performance')

def plot_trade_size_distribution(ax, trans_df):
    """Plot trade size distribution histogram"""
    if trans_df is not None:
        if 'amount' in trans_df.columns:
            # Create histogram of trade sizes
            ax.hist(trans_df['amount'], bins=20, color='purple', alpha=0.7)
            ax.set_title('Trade Size Distribution')
            ax.set_xlabel('Trade Size')
            ax.set_ylabel('Number of Trades')
            ax.grid(axis='y')
        else:
            ax.text(0.5, 0.5, 'Trade size data not available', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
            ax.set_title('Trade Size Distribution')
    else:
        ax.text(0.5, 0.5, 'No trades executed yet', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Trade Size Distribution')

def generate_trade_activity_heatmap(symbol, trans_df, dashboard_dir):
    """Generate a heatmap of trading activity by hour and minute"""
    plt.figure(figsize=(15, 8))
    
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
    plt.title(f'Trade Activity Heatmap by Hour and Minute - {symbol}')
    plt.xlabel('Minute')
    plt.ylabel('Hour')
    
    # Set x-ticks to show every 5 minutes
    plt.xticks(np.arange(0, 60, 5), np.arange(0, 60, 5))
    plt.yticks(np.arange(0, 24), np.arange(0, 24))
    
    heatmap_path = os.path.join(dashboard_dir, 'trade_activity_heatmap.png')
    plt.tight_layout()
    plt.savefig(heatmap_path)
    plt.close()
    
    print_success(f"Trade activity heatmap for {symbol} saved to: {heatmap_path}")

def generate_volatility_chart(symbol, balance_df, dashboard_dir):
    """Generate a price volatility chart for intraday analysis"""
    plt.figure(figsize=(15, 6))
    
    # Calculate price volatility (rolling std of price changes)
    if 'price' in balance_df.columns:
        balance_df['price_pct_change'] = balance_df['price'].pct_change() * 100
        balance_df['volatility'] = balance_df['price_pct_change'].rolling(10).std()
        
        # Plot volatility
        plt.plot(balance_df['timestamp'], balance_df['volatility'], 'b-', linewidth=2)
        plt.fill_between(balance_df['timestamp'], balance_df['volatility'], color='blue', alpha=0.2)
        plt.title(f'Price Volatility (10-period Rolling Standard Deviation) - {symbol}')
        plt.ylabel('Volatility (%)')
        plt.grid(True)
        
        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(plt.gca().xaxis.get_majorticklabels(), rotation=45)
        
        volatility_path = os.path.join(dashboard_dir, 'price_volatility.png')
        plt.tight_layout()
        plt.savefig(volatility_path)
        plt.close()
        
        print_success(f"Price volatility chart for {symbol} saved to: {volatility_path}")