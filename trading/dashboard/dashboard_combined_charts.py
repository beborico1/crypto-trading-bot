"""
Chart plotting functions for combined multi-symbol dashboard
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import json
from trading.dashboard.dashboard_utils import load_simulation_data

def plot_trading_activity_by_symbol(ax, symbol_dirs, output_dir):
    """Plot trading activity breakdown by symbol"""
    # Count trades by symbol
    trade_counts = {}
    trade_buys = {}
    trade_sells = {}
    
    for symbol_dir in symbol_dirs:
        symbol = symbol_dir.replace('_', '/')
        data_file = os.path.join(output_dir, symbol_dir, 'simulation_data.json')
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
            transactions = data.get('transactions', [])
            
            trade_counts[symbol] = len(transactions)
            trade_buys[symbol] = sum(1 for t in transactions if t.get('action') == 'buy')
            trade_sells[symbol] = sum(1 for t in transactions if t.get('action') == 'sell')
    
    # Sort by trade count
    symbols_by_trades = sorted(trade_counts.keys(), key=lambda x: trade_counts[x], reverse=True)
    
    # Plot stacked bar chart
    if symbols_by_trades:
        buys = [trade_buys.get(s, 0) for s in symbols_by_trades]
        sells = [trade_sells.get(s, 0) for s in symbols_by_trades]
        
        ax.bar(symbols_by_trades, buys, label='Buy', color='g', alpha=0.7)
        ax.bar(symbols_by_trades, sells, bottom=buys, label='Sell', color='r', alpha=0.7)
        
        ax.set_title('Trading Activity by Symbol')
        ax.set_ylabel('Number of Trades')
        ax.set_xticklabels(symbols_by_trades, rotation=45)
        ax.legend()
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, 'No trading activity data', horizontalalignment='center',
                verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Trading Activity by Symbol')

def plot_aggregate_metrics(ax, combined_df, symbol_dirs, output_dir, symbols):
    """Plot aggregate performance metrics"""
    ax.axis('off')  # Turn off axis
    
    # Calculate aggregate metrics
    total_initial_value = 0
    total_current_value = 0
    total_trades = 0
    best_symbol = None
    best_performance = -float('inf')
    worst_symbol = None
    worst_performance = float('inf')
    
    for symbol_dir in symbol_dirs:
        symbol = symbol_dir.replace('_', '/')
        data_file = os.path.join(output_dir, symbol_dir, 'simulation_data.json')
        
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            balance_history = data.get('balance_history', [])
            transactions = data.get('transactions', [])
            
            if balance_history:
                initial = balance_history[0].get('total_value_in_quote', 0)
                current = balance_history[-1].get('total_value_in_quote', 0)
                performance = (current / initial - 1) * 100 if initial > 0 else 0
                
                total_initial_value += initial
                total_current_value += current
                total_trades += len(transactions)
                
                if performance > best_performance:
                    best_performance = performance
                    best_symbol = symbol
                
                if performance < worst_performance:
                    worst_performance = performance
                    worst_symbol = symbol
    
    # Calculate aggregate return
    aggregate_return = total_current_value - total_initial_value
    aggregate_return_pct = (aggregate_return / total_initial_value) * 100 if total_initial_value > 0 else 0
    
    # Format metrics with colors
    if aggregate_return >= 0:
        agg_return_str = f"+${aggregate_return:.2f}"
        agg_return_color = "green"
    else:
        agg_return_str = f"-${abs(aggregate_return):.2f}"
        agg_return_color = "red"
        
    if aggregate_return_pct >= 0:
        pct_return_str = f"+{aggregate_return_pct:.2f}%"
        pct_return_color = "green"
    else:
        pct_return_str = f"{aggregate_return_pct:.2f}%"
        pct_return_color = "red"
    
    # Add text with metrics
    metrics_text = (
        f"Total Initial Balance: ${total_initial_value:.2f}\n"
        f"Total Current Balance: ${total_current_value:.2f}\n"
        f"Aggregate Return: {agg_return_str} ({agg_return_color})\n"
        f"Percent Return: {pct_return_str} ({pct_return_color})\n"
        f"Total Number of Trades: {total_trades}\n"
        f"Best Performing Symbol: {best_symbol} ({best_performance:.2f}%)\n"
        f"Worst Performing Symbol: {worst_symbol} ({worst_performance:.2f}%)\n"
        f"Number of Symbols: {len(symbols)}\n"
        f"Start Date: {combined_df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"End Date: {combined_df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes, va='top', fontsize=11, linespacing=1.5)
    ax.set_title('Aggregate Performance Metrics')

def plot_price_correlation(ax, combined_df, symbols):
    """Plot price correlation heatmap between symbols"""
    # Create price correlation matrix if we have enough symbols
    if len(symbols) > 1:
        # Create a dataframe with prices for each symbol
        price_data = {}
        
        for symbol in symbols:
            symbol_data = combined_df[combined_df['symbol'] == symbol]
            # Resample to a common time grid (1 minute intervals)
            symbol_data.set_index('timestamp', inplace=True)
            resampled = symbol_data['price'].resample('1min').last().fillna(method='ffill')
            price_data[symbol] = resampled
        
        # Create a DataFrame with all prices
        price_df = pd.DataFrame(price_data)
        
        # Calculate correlation matrix
        corr_matrix = price_df.corr()
        
        # Plot correlation heatmap
        im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
        plt.colorbar(im, ax=ax)
        
        # Set ticks and labels
        ax.set_xticks(np.arange(len(symbols)))
        ax.set_yticks(np.arange(len(symbols)))
        ax.set_xticklabels(symbols, rotation=45, ha='right')
        ax.set_yticklabels(symbols)
        
        # Loop over data dimensions and create text annotations
        for i in range(len(symbols)):
            for j in range(len(symbols)):
                text = ax.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}",
                            ha="center", va="center", color="black" if abs(corr_matrix.iloc[i, j]) < 0.7 else "white")
        
        ax.set_title('Price Correlation Between Symbols')
    else:
        ax.text(0.5, 0.5, 'Price correlation requires multiple symbols', 
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax.set_title('Price Correlation Matrix')

def plot_volatility_comparison(ax, combined_df, symbols):
    """Plot volatility comparison across symbols"""
    # Calculate and plot volatility for each symbol
    for symbol in symbols:
        symbol_data = combined_df[combined_df['symbol'] == symbol]
        if len(symbol_data) > 10 and 'price' in symbol_data.columns:
            # Calculate rolling volatility
            symbol_data = symbol_data.sort_values('timestamp')
            symbol_data['price_pct_change'] = symbol_data['price'].pct_change() * 100
            symbol_data['volatility'] = symbol_data['price_pct_change'].rolling(10).std()
            
            # Plot volatility
            ax.plot(symbol_data['timestamp'], symbol_data['volatility'], label=symbol)
    
    ax.set_title('Price Volatility Comparison')
    ax.set_ylabel('Volatility (% Std Dev)')
    ax.grid(True)
    ax.legend(loc='best', fontsize='small')