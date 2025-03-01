"""
Combined multi-symbol dashboard generation
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import json
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info
)
from trading.dashboard.dashboard_utils import (
    dollar_formatter, load_simulation_data, prepare_balance_dataframe,
    setup_figure, format_dates_on_axes
)
from trading.dashboard.dashboard_combined_charts import (
    plot_trading_activity_by_symbol, plot_aggregate_metrics,
    plot_price_correlation, plot_volatility_comparison
)

def generate_combined_dashboard(output_dir='simulation_data'):
    """
    Generate a dashboard combining data from all symbols
    
    Parameters:
    output_dir (str): Main directory containing symbol subdirectories
    
    Returns:
    bool: Success indicator
    """
    try:
        # Find all symbol directories (exclude dashboard and other files)
        symbol_dirs = [d for d in os.listdir(output_dir) 
                     if os.path.isdir(os.path.join(output_dir, d)) and d != 'dashboard' and d != 'combined_dashboard']
        
        if not symbol_dirs:
            print_error("No symbol directories found")
            return False
        
        # Create a directory for the combined dashboard
        combined_dir = os.path.join(output_dir, 'combined_dashboard')
        os.makedirs(combined_dir, exist_ok=True)
        
        # Collect data from all symbols
        all_symbols_data = []
        
        for symbol_dir in symbol_dirs:
            symbol = symbol_dir.replace('_', '/') 
            
            # Load simulation data
            data_file = os.path.join(output_dir, symbol_dir, 'simulation_data.json')
            balance_history, transactions = load_simulation_data(data_file)
            
            if balance_history is None:
                print_warning(f"No valid data found for {symbol}, skipping")
                continue
            
            # Prepare DataFrame
            balance_df = prepare_balance_dataframe(balance_history, symbol)
            
            # Add to collection
            all_symbols_data.append(balance_df)
        
        if not all_symbols_data:
            print_error("No valid data found in any symbol directory")
            return False
        
        # Combine all data
        combined_df = pd.concat(all_symbols_data)
        
        print_info(f"Generating combined dashboard for {len(all_symbols_data)} symbols...")
        
        # Create the combined dashboard
        create_combined_dashboard(combined_df, symbol_dirs, output_dir, combined_dir)
        
        return True
        
    except Exception as e:
        print_error(f"Error generating combined dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_combined_dashboard(combined_df, symbol_dirs, output_dir, combined_dir):
    """Create and save the combined dashboard"""
    # Create multi-panel dashboard for combined data
    fig = setup_figure('Multi-Symbol High Frequency Trading Bot Dashboard')
    gs = fig.add_gridspec(4, 3)
    
    # Get unique symbols
    symbols = combined_df['symbol'].unique()
    
    # 1. Performance comparison across symbols
    ax1 = fig.add_subplot(gs[0, :])
    plot_performance_comparison(ax1, combined_df, symbols)
    
    # 2. Total Value across all symbols
    ax2 = fig.add_subplot(gs[1, :2])
    plot_total_value_by_symbol(ax2, combined_df, symbols)
    
    # 3. Aggregate portfolio value
    ax3 = fig.add_subplot(gs[1, 2])
    plot_aggregate_performance(ax3, combined_df)
    
    # 4. Symbol performance ranking
    ax4 = fig.add_subplot(gs[2, 0])
    plot_symbol_performance_ranking(ax4, combined_df, symbols)
    
    # 5. Trading activity by symbol
    ax5 = fig.add_subplot(gs[2, 1:])
    plot_trading_activity_by_symbol(ax5, symbol_dirs, output_dir)
    
    # 6. Performance metrics
    ax6 = fig.add_subplot(gs[3, 0])
    plot_aggregate_metrics(ax6, combined_df, symbol_dirs, output_dir, symbols)
    
    # 7. Price correlation heatmap
    ax7 = fig.add_subplot(gs[3, 1])
    plot_price_correlation(ax7, combined_df, symbols)
    
    # 8. Combined volatility comparison
    ax8 = fig.add_subplot(gs[3, 2])
    plot_volatility_comparison(ax8, combined_df, symbols)
    
    # Format dates on x-axis
    format_dates_on_axes([ax1, ax2, ax3, ax8])
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save the dashboard
    dashboard_path = os.path.join(combined_dir, 'combined_dashboard.png')
    plt.savefig(dashboard_path)
    plt.close()
    
    print_success(f"Combined dashboard for {len(symbols)} symbols saved to: {dashboard_path}")

def plot_performance_comparison(ax, combined_df, symbols):
    """Plot performance comparison across symbols"""
    for symbol in symbols:
        symbol_data = combined_df[combined_df['symbol'] == symbol]
        ax.plot(symbol_data['timestamp'], symbol_data['performance'], linewidth=2, label=symbol)
    
    ax.set_title('Performance Comparison (%)')
    ax.set_ylabel('Return (%)')
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax.grid(True)
    ax.legend(loc='best')

def plot_total_value_by_symbol(ax, combined_df, symbols):
    """Plot total portfolio value for each symbol"""
    for symbol in symbols:
        symbol_data = combined_df[combined_df['symbol'] == symbol]
        ax.plot(symbol_data['timestamp'], symbol_data['total_value_in_quote'], linewidth=2, label=symbol)
    
    ax.set_title('Total Portfolio Value by Symbol')
    ax.set_ylabel('Value (USDT)')
    ax.yaxis.set_major_formatter(FuncFormatter(dollar_formatter))
    ax.grid(True)
    ax.legend(loc='best')

def plot_aggregate_performance(ax, combined_df):
    """Plot aggregate portfolio performance"""
    # Group by timestamp and sum the values
    if 'timestamp' in combined_df.columns:
        # Resample to common timestamps (e.g., minute intervals)
        combined_df['minute'] = combined_df['timestamp'].dt.floor('1min')
        agg_data = combined_df.groupby('minute').agg({
            'total_value_in_quote': 'sum',
            'initial_value': 'sum'
        }).reset_index()
        
        # Calculate aggregate performance
        agg_data['agg_performance'] = (agg_data['total_value_in_quote'] / agg_data['initial_value'] - 1) * 100
        
        # Plot aggregate performance
        ax.plot(agg_data['minute'], agg_data['agg_performance'], 'k-', linewidth=3)
        ax.set_title('Aggregate Portfolio Performance (%)')
        ax.set_ylabel('Return (%)')
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax.grid(True)

def plot_symbol_performance_ranking(ax, combined_df, symbols):
    """Plot performance ranking of symbols"""
    # Calculate final performance for each symbol
    symbol_performance = []
    for symbol in symbols:
        symbol_data = combined_df[combined_df['symbol'] == symbol]
        if not symbol_data.empty:
            initial = symbol_data['total_value_in_quote'].iloc[0]
            final = symbol_data['total_value_in_quote'].iloc[-1]
            perf = (final / initial - 1) * 100
            symbol_performance.append((symbol, perf))
    
    # Sort by performance
    symbol_performance.sort(key=lambda x: x[1], reverse=True)
    
    # Plot as bar chart
    symbols_sorted = [x[0] for x in symbol_performance]
    performance_values = [x[1] for x in symbol_performance]
    
    bars = ax.bar(symbols_sorted, performance_values, color=['g' if x >= 0 else 'r' for x in performance_values])
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        if height >= 0:
            y_pos = height + 0.5
        else:
            y_pos = height - 1.5
        ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                f'{height:.2f}%', ha='center', va='bottom')
    
    ax.set_title('Symbol Performance Ranking')
    ax.set_ylabel('Return (%)')
    ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax.set_xticklabels(symbols_sorted, rotation=45)
    ax.grid(axis='y')