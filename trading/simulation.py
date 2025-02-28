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
    def __init__(self, initial_balance=100.0, base_currency='BTC', quote_currency='USDT'):
        """
        Initialize the simulation tracker

        Parameters:
        initial_balance (float): Initial balance in quote currency (e.g., USDT)
        base_currency (str): Base currency (e.g., BTC)
        quote_currency (str): Quote currency (e.g., USDT)
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
        
        # Create simulation data directory if it doesn't exist
        os.makedirs('simulation_data', exist_ok=True)
        
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
            'base_balance_after': self.base_balance
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
            transactions_df.to_csv('simulation_data/transactions.csv', index=False)
        
        if not balance_df.empty:
            balance_df.to_csv('simulation_data/balance_history.csv', index=False)
        
        # Also save as JSON for easier loading
        with open('simulation_data/simulation_data.json', 'w') as f:
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
            'current_time': datetime.now().isoformat()
        }
    
    def plot_performance(self, save_path='simulation_data/performance_chart.png'):
        """
        Generate and save a performance chart

        Parameters:
        save_path (str): Path to save the chart image
        
        Returns:
        str: Path to saved chart or error message
        """
        if not self.balance_history:
            return "No data to plot"
        
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