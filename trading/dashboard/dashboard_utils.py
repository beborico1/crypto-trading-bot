"""
Utility functions for dashboard generation
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend that doesn't require a GUI window
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import os
import json
from utils.terminal_colors import print_success, print_error, print_warning, print_info

def dollar_formatter(x, pos):
    """Format y-axis values as dollars"""
    return f'${x:.2f}'

def load_simulation_data(data_file):
    """
    Load simulation data from a JSON file
    
    Parameters:
    data_file (str): Path to the JSON file
    
    Returns:
    tuple: (balance_history, transactions) or (None, None) if error
    """
    try:
        if not os.path.exists(data_file):
            print_error(f"Data file not found at {data_file}")
            return None, None
        
        # Load simulation data
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        balance_history = data.get('balance_history', [])
        transactions = data.get('transactions', [])
        
        if not balance_history:
            print_error("No balance history found in data file")
            return None, None
            
        return balance_history, transactions
    
    except Exception as e:
        print_error(f"Error loading simulation data: {e}")
        return None, None

def prepare_balance_dataframe(balance_history, symbol=None):
    """
    Prepare a DataFrame from balance history
    
    Parameters:
    balance_history (list): List of balance history records
    symbol (str, optional): Symbol to add to the DataFrame
    
    Returns:
    pandas.DataFrame: Processed DataFrame
    """
    # Convert to DataFrame
    balance_df = pd.DataFrame(balance_history)
    balance_df['timestamp'] = pd.to_datetime(balance_df['timestamp'])
    
    # Add symbol if provided
    if symbol:
        balance_df['symbol'] = symbol
    
    # Add performance metrics
    initial_value = balance_df['total_value_in_quote'].iloc[0]
    balance_df['performance'] = (balance_df['total_value_in_quote'] / initial_value - 1) * 100
    balance_df['initial_value'] = initial_value
    
    # Calculate drawdown
    balance_df['rolling_max'] = balance_df['total_value_in_quote'].cummax()
    balance_df['drawdown'] = (balance_df['total_value_in_quote'] / balance_df['rolling_max'] - 1) * 100
    
    return balance_df

def prepare_transaction_dataframe(transactions):
    """
    Prepare a DataFrame from transaction history
    
    Parameters:
    transactions (list): List of transaction records
    
    Returns:
    pandas.DataFrame: Processed DataFrame or None if empty
    """
    if not transactions:
        return None
        
    # Convert to DataFrame
    trans_df = pd.DataFrame(transactions)
    trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
    
    return trans_df

def calculate_trade_metrics(transactions, initial_value):
    """
    Calculate trade metrics from transaction history
    
    Parameters:
    transactions (list): List of transaction records
    initial_value (float): Initial portfolio value
    
    Returns:
    dict: Dictionary of trade metrics
    """
    if not transactions:
        return {
            'num_trades': 0,
            'buy_count': 0,
            'sell_count': 0,
            'trades_per_minute': 0,
            'win_rate': 0,
            'avg_profit': 0,
            'profits': []
        }
    
    # Create DataFrame
    trans_df = pd.DataFrame(transactions)
    
    # Basic counts
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
    
    return {
        'num_trades': num_trades,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'trades_per_minute': trades_per_minute,
        'win_rate': win_rate,
        'avg_profit': avg_profit,
        'profits': profits
    }

def setup_figure(title, figsize=(18, 14)):
    """Create and setup a figure with title"""
    fig = plt.figure(figsize=figsize)
    fig.suptitle(title, fontsize=18)
    return fig

def format_dates_on_axes(axes_list):
    """Format dates on x-axis for multiple axes"""
    for ax in axes_list:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)