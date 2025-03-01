"""
Single symbol dashboard generation
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import json
from datetime import datetime
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_header, format_profit, format_percentage, Colors
)
from trading.dashboard.dashboard_utils import (
    dollar_formatter, load_simulation_data, prepare_balance_dataframe,
    prepare_transaction_dataframe, calculate_trade_metrics,
    setup_figure, format_dates_on_axes
)
from trading.dashboard.dashboard_single_charts import (
    plot_performance_chart, plot_trade_distribution, plot_trade_frequency,
    plot_performance_metrics, plot_profit_distribution, plot_hourly_performance,
    plot_trade_size_distribution, generate_trade_activity_heatmap, generate_volatility_chart
)

def generate_dashboard(output_dir='simulation_data'):
    """
    Generate a comprehensive dashboard for the high frequency trading bot
    
    Parameters:
    output_dir (str): Directory to read data from and save charts to
    
    Returns:
    bool: Success indicator
    """
    try:
        # Extract symbol name from directory
        symbol = os.path.basename(output_dir).replace('_', '/')
        
        # Load data file
        data_file = os.path.join(output_dir, 'simulation_data.json')
        balance_history, transactions = load_simulation_data(data_file)
        
        if balance_history is None:
            return False
        
        # Prepare data frames
        balance_df = prepare_balance_dataframe(balance_history)
        trans_df = prepare_transaction_dataframe(transactions)
        
        # Calculate metrics
        initial_value = balance_df['total_value_in_quote'].iloc[0]
        current_value = balance_df['total_value_in_quote'].iloc[-1]
        absolute_return = current_value - initial_value
        percent_return = (absolute_return / initial_value) * 100
        max_drawdown = balance_df['drawdown'].min()
        
        # Calculate trade metrics
        trade_metrics = calculate_trade_metrics(transactions, initial_value)
        
        # Create a subdirectory for the dashboard
        dashboard_dir = os.path.join(output_dir, 'dashboard')
        os.makedirs(dashboard_dir, exist_ok=True)
        
        print_info(f"Generating high frequency dashboard for {symbol} from {len(balance_history)} data points...")
        
        # Create the main dashboard
        generate_main_dashboard(
            symbol, balance_df, trans_df, trade_metrics, 
            initial_value, current_value, absolute_return, 
            percent_return, max_drawdown, dashboard_dir
        )
        
        # Generate additional charts if we have enough data
        if trans_df is not None and len(trans_df) > 10:
            generate_trade_activity_heatmap(symbol, trans_df, dashboard_dir)
        
        if len(balance_df) > 10:
            generate_volatility_chart(symbol, balance_df, dashboard_dir)
        
        # Print summary in terminal
        print_header(f"High Frequency Trading Dashboard for {symbol} Generation Complete")
        print_info(f"Initial Balance: ${initial_value:.2f}")
        print_info(f"Current Balance: ${current_value:.2f}")
        print_info(f"Absolute Return: {format_profit(absolute_return)}")
        print_info(f"Percent Return: {format_percentage(percent_return)}")
        print_info(f"Max Drawdown: {format_percentage(max_drawdown, include_sign=False)}")
        print_info(f"Total Trades: {trade_metrics['num_trades']} (Buys: {trade_metrics['buy_count']}, Sells: {trade_metrics['sell_count']})")
        print_info(f"Trading Frequency: {trade_metrics['trades_per_minute']:.2f} trades per minute")
        print_info(f"Win Rate: {format_percentage(trade_metrics['win_rate'], include_sign=False)}")
        print_info(f"Avg Profit per Trade: {format_percentage(trade_metrics['avg_profit'])}")
        
        return True
        
    except Exception as e:
        print_error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_main_dashboard(
    symbol, balance_df, trans_df, trade_metrics, 
    initial_value, current_value, absolute_return, 
    percent_return, max_drawdown, dashboard_dir
):
    """Generate the main dashboard with multiple panels"""
    
    # Create a multi-panel dashboard
    fig = setup_figure(f'High Frequency Trading Bot Simulation Dashboard - {symbol}')
    gs = fig.add_gridspec(4, 3)
    
    # 1. Total Value Over Time
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(balance_df['timestamp'], balance_df['total_value_in_quote'], 'b-', linewidth=2)
    ax1.set_title('Total Portfolio Value')
    ax1.set_ylabel('Value (USDT)')
    ax1.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
    ax1.grid(True)
    
    # Add buy/sell markers if transactions exist
    if trans_df is not None:
        add_trade_markers(ax1, trans_df, balance_df, initial_value)
    
    ax1.legend()
    
    # 2. Price History
    ax2 = fig.add_subplot(gs[1, 0:2])
    ax2.plot(balance_df['timestamp'], balance_df['price'], 'r-', linewidth=2)
    ax2.set_title(f'Price History - {symbol}')
    ax2.set_ylabel('Price (USDT)')
    ax2.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
    ax2.grid(True)
    
    # 3. Performance (%)
    ax3 = fig.add_subplot(gs[1, 2])
    plot_performance_chart(ax3, balance_df)
    
    # 4. Trade distribution
    ax4 = fig.add_subplot(gs[2, 0])
    plot_trade_distribution(ax4, trans_df)
    
    # 5. Trade Frequency Over Time
    ax5 = fig.add_subplot(gs[2, 1])
    plot_trade_frequency(ax5, trans_df)
    
    # 6. Performance metrics
    ax6 = fig.add_subplot(gs[2, 2])
    plot_performance_metrics(
        ax6, symbol, initial_value, current_value, 
        absolute_return, percent_return, max_drawdown, 
        trade_metrics, balance_df
    )
    
    # 7. Trade profit distribution
    ax7 = fig.add_subplot(gs[3, 0])
    plot_profit_distribution(ax7, trade_metrics['profits'])
    
    # 8. Hourly performance
    ax8 = fig.add_subplot(gs[3, 1])
    plot_hourly_performance(ax8, balance_df)
    
    # 9. Trade size distribution
    ax9 = fig.add_subplot(gs[3, 2])
    plot_trade_size_distribution(ax9, trans_df)
    
    # Format dates on x-axis
    format_dates_on_axes([ax1, ax2, ax3, ax5])
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save the dashboard
    dashboard_path = os.path.join(dashboard_dir, 'hft_dashboard.png')
    plt.savefig(dashboard_path)
    plt.close()
    
    print_success(f"High frequency trading dashboard for {symbol} saved to: {dashboard_path}")

def add_trade_markers(ax, trans_df, balance_df, initial_value):
    """Add buy/sell markers to the chart"""
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
                ax.scatter(t['timestamp'], price, marker='^', color='g', s=80, zorder=5, label='Buy' if 'Buy' not in ax.get_legend_handles_labels()[1] else "")
        
        for _, t in sell_markers.iterrows():
            price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
            if price is not None:
                ax.scatter(t['timestamp'], price, marker='v', color='r', s=80, zorder=5, label='Sell' if 'Sell' not in ax.get_legend_handles_labels()[1] else "")
    else:
        # If we have fewer trades, show them all
        for _, t in trans_df.iterrows():
            if t['action'] == 'buy':
                price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                if price is not None:
                    ax.scatter(t['timestamp'], price, marker='^', color='g', s=80, zorder=5, label='Buy' if 'Buy' not in ax.get_legend_handles_labels()[1] else "")
            else:  # sell
                price = balance_df.loc[balance_df['timestamp'] > t['timestamp'], 'total_value_in_quote'].iloc[0] if not balance_df.loc[balance_df['timestamp'] > t['timestamp']].empty else None
                if price is not None:
                    ax.scatter(t['timestamp'], price, marker='v', color='r', s=80, zorder=5, label='Sell' if 'Sell' not in ax.get_legend_handles_labels()[1] else "")