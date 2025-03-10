"""
Simulation tracking module for the crypto trading bot.
Tracks balance and performance in simulation mode.
"""

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_simulation, Colors
)

class SimulationTracker:
    def __init__(self, initial_balance=100.0, base_currency='BTC', quote_currency='USDT', data_dir='simulation_data'):
        """
        Initialize the simulation tracker

        Parameters:
        initial_balance (float): Initial balance in quote currency (e.g., USDT)
        base_currency (str): Base currency (e.g., BTC)
        quote_currency (str): Quote currency (e.g., USDT)
        data_dir (str): Directory to store simulation data
        """
        self.quote_balance = initial_balance
        self.base_balance = 0.0
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.transaction_history = []
        self.balance_history = [{
            'timestamp': datetime.now().isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'total_value_in_quote': self.quote_balance
        }]
        
        # Store the data directory
        self.data_dir = data_dir
        
        # Create simulation data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        print_simulation(f"Started with {initial_balance} {quote_currency}")
    
    def execute_trade(self, action, amount, price):
        """
        Execute a simulated trade

        Parameters:
        action (str): 'buy' or 'sell'
        amount (float): Amount of base currency to trade
        price (float): Current price of base currency in quote currency

        Returns:
        bool: True if trade was successful, False otherwise
        """
        timestamp = datetime.now()
        
        if action.lower() == 'buy':
            # Calculate cost in quote currency (including a 0.1% fee to simulate real trading)
            cost = amount * price * 1.001
            
            # Check if we have enough quote currency
            if cost > self.quote_balance:
                print_error(f"SIMULATION: Insufficient {self.quote_currency} balance for buy")
                return False
            
            # Update balances
            self.quote_balance -= cost
            self.base_balance += amount
            
            print_buy(f"Bought {amount} {self.base_currency} at ${price:,.2f} {self.quote_currency}")
            
        elif action.lower() == 'sell':
            # Check if we have enough base currency
            if amount > self.base_balance:
                print_error(f"SIMULATION: Insufficient {self.base_currency} balance for sell")
                return False
            
            # Calculate proceeds in quote currency (including a 0.1% fee to simulate real trading)
            proceeds = amount * price * 0.999
            
            # Update balances
            self.base_balance -= amount
            self.quote_balance += proceeds
            
            print_sell(f"Sold {amount} {self.base_currency} at ${price:,.2f} {self.quote_currency}")
        
        else:
            print_error(f"SIMULATION: Unknown action {action}")
            return False
        
        # Record the transaction
        transaction = {
            'timestamp': timestamp.isoformat(),
            'action': action.lower(),
            'amount': amount,
            'price': price,
            'value': amount * price,
            'quote_balance_after': self.quote_balance,
            'base_balance_after': self.base_balance,
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency
        }
        self.transaction_history.append(transaction)
        
        # Update balance history
        current_total_value = self.quote_balance + (self.base_balance * price)
        balance_entry = {
            'timestamp': timestamp.isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'price': price,
            'total_value_in_quote': current_total_value
        }
        self.balance_history.append(balance_entry)
        
        # Save updated data
        self._save_data()
        
        return True
    
    def update_price(self, current_price):
        """
        Update the current price and record balance without trading

        Parameters:
        current_price (float): Current price of base currency in quote currency
        """
        timestamp = datetime.now()
        
        # Calculate current total value
        current_total_value = self.quote_balance + (self.base_balance * current_price)
        
        # Update balance history
        balance_entry = {
            'timestamp': timestamp.isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'price': current_price,
            'total_value_in_quote': current_total_value
        }
        self.balance_history.append(balance_entry)
        
        # Save updated data
        self._save_data()
    
    def get_current_balance(self, current_price):
        """
        Get the current balance in both currencies and total value

        Parameters:
        current_price (float): Current price of base currency in quote currency

        Returns:
        dict: Current balance details
        """
        total_value = self.quote_balance + (self.base_balance * current_price)
        initial_value = self.balance_history[0]['total_value_in_quote'] if self.balance_history else 0
        
        profit_loss = total_value - initial_value
        profit_loss_pct = (profit_loss / initial_value * 100) if initial_value > 0 else 0
        
        return {
            'quote_currency': self.quote_currency,
            'quote_balance': self.quote_balance,
            'base_currency': self.base_currency,
            'base_balance': self.base_balance,
            'current_price': current_price,
            'total_value_in_quote': total_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        }
    
    def _save_data(self):
        """Save simulation data to files"""
        # Convert data to DataFrames
        transactions_df = pd.DataFrame(self.transaction_history)
        balance_df = pd.DataFrame(self.balance_history)
        
        # Save to CSV files
        if not transactions_df.empty:
            transactions_df.to_csv(os.path.join(self.data_dir, 'transactions.csv'), index=False)
        
        if not balance_df.empty:
            balance_df.to_csv(os.path.join(self.data_dir, 'balance_history.csv'), index=False)
        
        # Also save as JSON for easier loading
        with open(os.path.join(self.data_dir, 'simulation_data.json'), 'w') as f:
            json.dump({
                'transactions': self.transaction_history,
                'balance_history': self.balance_history
            }, f, indent=2)
    
    def generate_performance_report(self, current_price):
        """
        Generate a performance report

        Parameters:
        current_price (float): Current price of base currency in quote currency

        Returns:
        dict: Performance metrics
        """
        if not self.balance_history:
            return {'error': 'No balance history available'}
        
        # Get first and last balance entries
        initial = self.balance_history[0]
        current = self.get_current_balance(current_price)
        
        # Calculate performance metrics
        initial_value = initial['total_value_in_quote']
        current_value = current['total_value_in_quote']
        
        absolute_return = current_value - initial_value
        percent_return = (absolute_return / initial_value) * 100 if initial_value > 0 else 0
        
        # Count trades
        buy_count = sum(1 for t in self.transaction_history if t['action'] == 'buy')
        sell_count = sum(1 for t in self.transaction_history if t['action'] == 'sell')
        
        # Get trade values
        if buy_count > 0:
            avg_buy_price = sum(t['price'] for t in self.transaction_history if t['action'] == 'buy') / buy_count
        else:
            avg_buy_price = 0
            
        if sell_count > 0:
            avg_sell_price = sum(t['price'] for t in self.transaction_history if t['action'] == 'sell') / sell_count
        else:
            avg_sell_price = 0
        
        return {
            'initial_balance': initial_value,
            'current_balance': current_value,
            'absolute_return': absolute_return,
            'percent_return': percent_return,
            'total_trades': buy_count + sell_count,
            'buy_trades': buy_count,
            'sell_trades': sell_count,
            'avg_buy_price': avg_buy_price,
            'avg_sell_price': avg_sell_price,
            'current_position': 'In market' if current['base_balance'] > 0 else 'In cash',
            'start_time': initial['timestamp'],
            'current_time': datetime.now().isoformat(),
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency
        }
    
    def plot_performance(self, save_path=None):
        """
        Generate and save a performance chart

        Parameters:
        save_path (str): Path to save the chart image
        
        Returns:
        str: Path to saved chart or error message
        """
        if not self.balance_history:
            return "No data to plot"
        
        # If no save path provided, use the data directory
        if save_path is None:
            save_path = os.path.join(self.data_dir, 'performance_chart.png')
        
        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(self.balance_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot total value
        ax1.plot(df['timestamp'], df['total_value_in_quote'], 'b-', label='Total Value')
        ax1.set_title(f'Simulation Performance: {self.base_currency}/{self.quote_currency}')
        ax1.set_ylabel(f'Value ({self.quote_currency})')
        ax1.grid(True)
        ax1.legend()
        
        # Plot price
        if 'price' in df.columns:
            ax2.plot(df['timestamp'], df['price'], 'r-', label=f'{self.base_currency} Price')
            ax2.set_ylabel(f'Price ({self.quote_currency})')
            ax2.set_xlabel('Time')
            ax2.grid(True)
            ax2.legend()
        
        # Add transactions to the chart
        if self.transaction_history:
            trans_df = pd.DataFrame(self.transaction_history)
            trans_df['timestamp'] = pd.to_datetime(trans_df['timestamp'])
            
            for _, t in trans_df.iterrows():
                if t['action'] == 'buy':
                    ax1.scatter(t['timestamp'], t['quote_balance_after'] + t['amount'] * t['price'], 
                              marker='^', color='g', s=100, alpha=0.7)
                    if 'price' in df.columns:
                        ax2.scatter(t['timestamp'], t['price'], marker='^', color='g', s=100, alpha=0.7)
                else:  # sell
                    ax1.scatter(t['timestamp'], t['quote_balance_after'], 
                              marker='v', color='r', s=100, alpha=0.7)
                    if 'price' in df.columns:
                        ax2.scatter(t['timestamp'], t['price'], marker='v', color='r', s=100, alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        
        print_success(f"Performance chart saved to: {save_path}")
        return save_path

def load_simulation_data(data_dir='simulation_data'):
    """
    Load existing simulation data from files
    
    Parameters:
    data_dir (str): Directory where simulation data is stored
    
    Returns:
    tuple: (SimulationTracker instance, success boolean)
    """
    # Check if simulation data file exists
    data_file = os.path.join(data_dir, 'simulation_data.json')
    if not os.path.exists(data_file):
        print(f"No existing simulation data found in {data_dir}.")
        return None, False
    
    try:
        # Load data from JSON file
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        transactions = data.get('transactions', [])
        balance_history = data.get('balance_history', [])
        
        if not balance_history:
            print("No balance history found in data file.")
            return None, False
        
        # Extract initial balance and currencies from the first balance entry
        initial_entry = balance_history[0]
        quote_balance = initial_entry.get('quote_balance', 0)
        
        # Determine base/quote currencies from transactions if available
        base_currency = 'BTC'  # Default
        quote_currency = 'USDT'  # Default
        
        # Try to extract currency info from transactions
        if transactions:
            for transaction in transactions:
                if transaction.get('base_currency') and transaction.get('quote_currency'):
                    base_currency = transaction.get('base_currency')
                    quote_currency = transaction.get('quote_currency')
                    break
            # If not in transaction, try to extract from the symbol directory name
            if base_currency == 'BTC' and quote_currency == 'USDT':
                dir_name = os.path.basename(data_dir)
                if '_' in dir_name:
                    symbol_parts = dir_name.split('_')
                    if len(symbol_parts) == 2:
                        base_currency = symbol_parts[0]
                        quote_currency = symbol_parts[1]
        
        # Create a new simulation tracker with the loaded initial balance
        sim_tracker = SimulationTracker(
            initial_balance=quote_balance,
            base_currency=base_currency,
            quote_currency=quote_currency,
            data_dir=data_dir
        )
        
        # Restore transaction history and balance history
        sim_tracker.transaction_history = transactions
        sim_tracker.balance_history = balance_history
        
        # Calculate current balances from the most recent balance entry
        if balance_history:
            latest_entry = balance_history[-1]
            sim_tracker.quote_balance = latest_entry.get('quote_balance', quote_balance)
            sim_tracker.base_balance = latest_entry.get('base_balance', 0)
        
        return sim_tracker, True
        
    except Exception as e:
        print(f"Error loading simulation data: {e}")
        import traceback
        traceback.print_exc()
        return None, False