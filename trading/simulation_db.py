"""
trading/simulation_db.py - SQLite Database Storage for Simulation Data

This module provides a database-backed implementation for simulation data storage,
replacing the JSON file-based approach for better performance and data integrity.
"""

import os
import sqlite3
import json
import pandas as pd
from datetime import datetime
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info
)

class SimulationDatabase:
    """Database-backed storage for simulation data"""
    
    def __init__(self, data_dir):
        """
        Initialize the database
        
        Parameters:
        data_dir (str): Directory to store the database
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.db_path = os.path.join(data_dir, 'simulation_data.db')
        self.conn = None
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the database schema"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                base_currency TEXT NOT NULL,
                quote_currency TEXT NOT NULL,
                initial_balance REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                quote_balance REAL NOT NULL,
                base_balance REAL NOT NULL,
                price REAL NOT NULL,
                total_value_in_quote REAL NOT NULL,
                FOREIGN KEY (symbol_id) REFERENCES symbols (id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL,
                quote_balance_after REAL NOT NULL,
                base_balance_after REAL NOT NULL,
                FOREIGN KEY (symbol_id) REFERENCES symbols (id)
            )
            ''')
            
            self.conn.commit()
            print_info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            print_error(f"Database initialization error: {e}")
            if self.conn:
                self.conn.close()
                self.conn = None
    
    def ensure_connection(self):
        """Ensure database connection is active"""
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_path)
            except sqlite3.Error as e:
                print_error(f"Database connection error: {e}")
                return False
        return True
    
    def get_symbol_id(self, symbol, create_if_missing=False, base_currency=None, quote_currency=None, initial_balance=None):
        """
        Get the database ID for a symbol
        
        Parameters:
        symbol (str): Trading pair symbol
        create_if_missing (bool): Create the symbol entry if it doesn't exist
        base_currency (str): Base currency (required if create_if_missing is True)
        quote_currency (str): Quote currency (required if create_if_missing is True)
        initial_balance (float): Initial balance (required if create_if_missing is True)
        
        Returns:
        int: Symbol ID or None if not found and not created
        """
        if not self.ensure_connection():
            return None
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM symbols WHERE symbol = ?', (symbol,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            elif create_if_missing:
                if not all([base_currency, quote_currency, initial_balance]):
                    print_error("Missing required parameters to create symbol entry")
                    return None
                
                cursor.execute('''
                INSERT INTO symbols (symbol, base_currency, quote_currency, initial_balance, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (symbol, base_currency, quote_currency, initial_balance, datetime.now().isoformat()))
                
                self.conn.commit()
                return cursor.lastrowid
            else:
                return None
                
        except sqlite3.Error as e:
            print_error(f"Database error getting symbol ID: {e}")
            return None
    
    def add_balance_entry(self, symbol, quote_balance, base_balance, price, total_value_in_quote=None, timestamp=None):
        """
        Add a balance history entry
        
        Parameters:
        symbol (str): Trading pair symbol
        quote_balance (float): Quote currency balance
        base_balance (float): Base currency balance
        price (float): Current price
        total_value_in_quote (float): Total value in quote currency (calculated if None)
        timestamp (str): ISO formatted timestamp (current time if None)
        
        Returns:
        bool: Success indicator
        """
        if not self.ensure_connection():
            return False
        
        # Get symbol parts if needed for symbol creation
        if '/' in symbol:
            base_currency, quote_currency = symbol.split('/')
        else:
            base_currency, quote_currency = None, None
        
        symbol_id = self.get_symbol_id(
            symbol, 
            create_if_missing=True, 
            base_currency=base_currency, 
            quote_currency=quote_currency, 
            initial_balance=quote_balance
        )
        
        if not symbol_id:
            return False
        
        # Calculate total value if not provided
        if total_value_in_quote is None:
            total_value_in_quote = quote_balance + (base_balance * price)
        
        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO balance_history (symbol_id, timestamp, quote_balance, base_balance, price, total_value_in_quote)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (symbol_id, timestamp, quote_balance, base_balance, price, total_value_in_quote))
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print_error(f"Database error adding balance entry: {e}")
            return False
    
    def add_transaction(self, symbol, action, amount, price, value, quote_balance_after, base_balance_after, timestamp=None):
        """
        Add a transaction entry
        
        Parameters:
        symbol (str): Trading pair symbol
        action (str): Transaction action ('buy' or 'sell')
        amount (float): Transaction amount
        price (float): Transaction price
        value (float): Transaction value
        quote_balance_after (float): Quote balance after transaction
        base_balance_after (float): Base balance after transaction
        timestamp (str): ISO formatted timestamp (current time if None)
        
        Returns:
        bool: Success indicator
        """
        if not self.ensure_connection():
            return False
        
        # Get symbol ID
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return False
        
        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            INSERT INTO transactions 
            (symbol_id, timestamp, action, amount, price, value, quote_balance_after, base_balance_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol_id, timestamp, action, amount, price, value, 
                quote_balance_after, base_balance_after
            ))
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            print_error(f"Database error adding transaction: {e}")
            return False
    
    def get_balance_history(self, symbol, limit=None, offset=0):
        """
        Get balance history for a symbol
        
        Parameters:
        symbol (str): Trading pair symbol
        limit (int): Maximum number of entries to return
        offset (int): Offset for pagination
        
        Returns:
        list: Balance history entries as dictionaries
        """
        if not self.ensure_connection():
            return []
        
        # Get symbol ID
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            if limit:
                cursor.execute('''
                SELECT timestamp, quote_balance, base_balance, price, total_value_in_quote
                FROM balance_history
                WHERE symbol_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                ''', (symbol_id, limit, offset))
            else:
                cursor.execute('''
                SELECT timestamp, quote_balance, base_balance, price, total_value_in_quote
                FROM balance_history
                WHERE symbol_id = ?
                ORDER BY timestamp DESC
                ''', (symbol_id,))
            
            columns = ['timestamp', 'quote_balance', 'base_balance', 'price', 'total_value_in_quote']
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Reverse to get chronological order
            result.reverse()
            return result
            
        except sqlite3.Error as e:
            print_error(f"Database error getting balance history: {e}")
            return []
    
    def get_transactions(self, symbol, limit=None, offset=0):
        """
        Get transactions for a symbol
        
        Parameters:
        symbol (str): Trading pair symbol
        limit (int): Maximum number of entries to return
        offset (int): Offset for pagination
        
        Returns:
        list: Transaction entries as dictionaries
        """
        if not self.ensure_connection():
            return []
        
        # Get symbol ID
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return []
        
        try:
            cursor = self.conn.cursor()
            
            if limit:
                cursor.execute('''
                SELECT timestamp, action, amount, price, value, quote_balance_after, base_balance_after
                FROM transactions
                WHERE symbol_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                ''', (symbol_id, limit, offset))
            else:
                cursor.execute('''
                SELECT timestamp, action, amount, price, value, quote_balance_after, base_balance_after
                FROM transactions
                WHERE symbol_id = ?
                ORDER BY timestamp DESC
                ''', (symbol_id,))
            
            columns = ['timestamp', 'action', 'amount', 'price', 'value', 'quote_balance_after', 'base_balance_after']
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Reverse to get chronological order
            result.reverse()
            return result
            
        except sqlite3.Error as e:
            print_error(f"Database error getting transactions: {e}")
            return []
    
    def get_all_symbols(self):
        """
        Get all symbols in the database
        
        Returns:
        list: Symbol entries as dictionaries
        """
        if not self.ensure_connection():
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT id, symbol, base_currency, quote_currency, initial_balance, created_at
            FROM symbols
            ORDER BY symbol
            ''')
            
            columns = ['id', 'symbol', 'base_currency', 'quote_currency', 'initial_balance', 'created_at']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            print_error(f"Database error getting symbols: {e}")
            return []
    
    def get_symbol_performance(self, symbol):
        """
        Get performance metrics for a symbol
        
        Parameters:
        symbol (str): Trading pair symbol
        
        Returns:
        dict: Performance metrics
        """
        if not self.ensure_connection():
            return None
        
        # Get symbol ID
        symbol_id = self.get_symbol_id(symbol)
        if not symbol_id:
            return None
        
        try:
            cursor = self.conn.cursor()
            
            # Get symbol info
            cursor.execute('''
            SELECT base_currency, quote_currency, initial_balance, created_at
            FROM symbols
            WHERE id = ?
            ''', (symbol_id,))
            
            symbol_info = cursor.fetchone()
            if not symbol_info:
                return None
                
            base_currency, quote_currency, initial_balance, created_at = symbol_info
            
            # Get first and last balance entries
            cursor.execute('''
            SELECT quote_balance, base_balance, price, total_value_in_quote
            FROM balance_history
            WHERE symbol_id = ?
            ORDER BY timestamp ASC
            LIMIT 1
            ''', (symbol_id,))
            
            first_balance = cursor.fetchone()
            if not first_balance:
                return None
                
            cursor.execute('''
            SELECT quote_balance, base_balance, price, total_value_in_quote
            FROM balance_history
            WHERE symbol_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            ''', (symbol_id,))
            
            last_balance = cursor.fetchone()
            if not last_balance:
                return None
            
            # Get transaction counts
            cursor.execute('''
            SELECT COUNT(*) FROM transactions
            WHERE symbol_id = ? AND action = 'buy'
            ''', (symbol_id,))
            buy_count = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT COUNT(*) FROM transactions
            WHERE symbol_id = ? AND action = 'sell'
            ''', (symbol_id,))
            sell_count = cursor.fetchone()[0]
            
            # Calculate performance metrics
            initial_value = first_balance[3]  # total_value_in_quote
            current_value = last_balance[3]   # total_value_in_quote
            
            absolute_return = current_value - initial_value
            percent_return = (absolute_return / initial_value) * 100 if initial_value > 0 else 0
            
            return {
                'symbol': symbol,
                'base_currency': base_currency,
                'quote_currency': quote_currency,
                'initial_value': initial_value,
                'current_value': current_value,
                'absolute_return': absolute_return,
                'percent_return': percent_return,
                'trades': buy_count + sell_count,
                'buy_trades': buy_count,
                'sell_trades': sell_count,
                'current_quote_balance': last_balance[0],  # quote_balance
                'current_base_balance': last_balance[1],   # base_balance
                'current_price': last_balance[2],          # price
                'started_at': created_at
            }
            
        except sqlite3.Error as e:
            print_error(f"Database error getting symbol performance: {e}")
            return None
    
    def export_to_json(self, symbol, target_file=None):
        """
        Export symbol data to JSON format
        
        Parameters:
        symbol (str): Trading pair symbol
        target_file (str): Target JSON file path (default: simulation_data.json in symbol directory)
        
        Returns:
        bool: Success indicator
        """
        # Get balance history and transactions
        balance_history = self.get_balance_history(symbol)
        transactions = self.get_transactions(symbol)
        
        if not balance_history:
            print_warning(f"No balance history found for {symbol}")
            return False
        
        # Create JSON data
        json_data = {
            'balance_history': balance_history,
            'transactions': transactions
        }
        
        try:
            # Determine target file if not specified
            if target_file is None:
                symbol_dir = os.path.join(self.data_dir, symbol.replace('/', '_'))
                os.makedirs(symbol_dir, exist_ok=True)
                target_file = os.path.join(symbol_dir, 'simulation_data.json')
            
            # Write to file
            with open(target_file, 'w') as f:
                json.dump(json_data, f, indent=2)
                
            print_success(f"Exported {symbol} data to {target_file}")
            return True
            
        except Exception as e:
            print_error(f"Error exporting to JSON: {e}")
            return False
    
    def import_from_json(self, json_file, symbol=None):
        """
        Import data from JSON file
        
        Parameters:
        json_file (str): JSON file path
        symbol (str): Override symbol name (default: derive from file path)
        
        Returns:
        bool: Success indicator
        """
        try:
            # Load JSON data
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract symbol from file path if not provided
            if symbol is None:
                file_dir = os.path.basename(os.path.dirname(json_file))
                symbol = file_dir.replace('_', '/')
            
            # Get balance history and transactions
            balance_history = data.get('balance_history', [])
            transactions = data.get('transactions', [])
            
            if not balance_history:
                print_warning(f"No balance history found in {json_file}")
                return False
            
            # Extract symbol information from first entry
            first_entry = balance_history[0]
            quote_balance = first_entry.get('quote_balance', 0)
            initial_value = first_entry.get('total_value_in_quote', quote_balance)
            
            # Extract base/quote currency from symbol
            if '/' in symbol:
                base_currency, quote_currency = symbol.split('/')
            else:
                # Try to extract from transactions if available
                if transactions and 'base_currency' in transactions[0] and 'quote_currency' in transactions[0]:
                    base_currency = transactions[0]['base_currency']
                    quote_currency = transactions[0]['quote_currency']
                else:
                    # Default values
                    base_currency = 'UNKNOWN'
                    quote_currency = 'USDT'
            
            # Get or create symbol entry
            symbol_id = self.get_symbol_id(
                symbol,
                create_if_missing=True,
                base_currency=base_currency,
                quote_currency=quote_currency,
                initial_balance=initial_value
            )
            
            if not symbol_id:
                print_error(f"Failed to create symbol entry for {symbol}")
                return False
            
            # Import balance history
            for entry in balance_history:
                self.add_balance_entry(
                    symbol=symbol,
                    quote_balance=entry.get('quote_balance', 0),
                    base_balance=entry.get('base_balance', 0),
                    price=entry.get('price', 0),
                    total_value_in_quote=entry.get('total_value_in_quote', 0),
                    timestamp=entry.get('timestamp')
                )
            
            # Import transactions
            for tx in transactions:
                self.add_transaction(
                    symbol=symbol,
                    action=tx.get('action', 'unknown'),
                    amount=tx.get('amount', 0),
                    price=tx.get('price', 0),
                    value=tx.get('value', 0),
                    quote_balance_after=tx.get('quote_balance_after', 0),
                    base_balance_after=tx.get('base_balance_after', 0),
                    timestamp=tx.get('timestamp')
                )
            
            print_success(f"Imported {len(balance_history)} balance entries and {len(transactions)} transactions for {symbol}")
            return True
            
        except Exception as e:
            print_error(f"Error importing from JSON: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Utility function to migrate from JSON files to SQLite
def migrate_data_to_sqlite(data_dir='simulation_data'):
    """
    Migrate all simulation data from JSON files to SQLite database
    
    Parameters:
    data_dir (str): Root data directory
    
    Returns:
    bool: Success indicator
    """
    print_info(f"Starting migration from JSON files to SQLite database...")
    
    try:
        # Initialize database
        db = SimulationDatabase(data_dir)
        
        # Find all symbol directories
        symbol_dirs = [d for d in os.listdir(data_dir) 
                     if os.path.isdir(os.path.join(data_dir, d)) and d != 'dashboard' and d != 'combined_dashboard']
        
        successful_migrations = 0
        
        for symbol_dir in symbol_dirs:
            symbol = symbol_dir.replace('_', '/')
            json_file = os.path.join(data_dir, symbol_dir, 'simulation_data.json')
            
            if os.path.exists(json_file):
                print_info(f"Migrating {symbol} from {json_file}...")
                
                if db.import_from_json(json_file, symbol):
                    successful_migrations += 1
                    # Create a backup of the original file
                    backup_file = json_file + '.bak'
                    if not os.path.exists(backup_file):
                        import shutil
                        shutil.copy2(json_file, backup_file)
                        print_info(f"Created backup at {backup_file}")
        
        db.close()
        
        print_success(f"Migration completed. Successfully migrated {successful_migrations} out of {len(symbol_dirs)} symbols.")
        return successful_migrations > 0
        
    except Exception as e:
        print_error(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

# Adapt for compatibility with old implementation
class SimulationTracker:
    """
    Adapter class for compatibility with the original SimulationTracker
    Uses the new database-backed implementation
    """
    
    def __init__(self, initial_balance=100.0, base_currency='BTC', quote_currency='USDT', data_dir='simulation_data'):
        """
        Initialize the simulation tracker adapter
        
        Parameters:
        initial_balance (float): Initial balance in quote currency
        base_currency (str): Base currency
        quote_currency (str): Quote currency
        data_dir (str): Data directory
        """
        self.quote_balance = initial_balance
        self.base_balance = 0.0
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.symbol = f"{base_currency}/{quote_currency}"
        self.data_dir = data_dir
        self.transaction_history = []
        
        # Create a local cache of balance history
        self.balance_history = [{
            'timestamp': datetime.now().isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'price': 0.0,
            'total_value_in_quote': self.quote_balance
        }]
        
        # Initialize database
        self.db = SimulationDatabase(data_dir)
        
        # Add initial balance entry
        self.db.add_balance_entry(
            symbol=self.symbol,
            quote_balance=self.quote_balance,
            base_balance=self.base_balance,
            price=0.0,
            total_value_in_quote=self.quote_balance
        )
        
        print_info(f"Started simulation with {initial_balance} {quote_currency}")
    
    def execute_trade(self, action, amount, price):
        """
        Execute a simulated trade
        
        Parameters:
        action (str): 'buy' or 'sell'
        amount (float): Amount to trade
        price (float): Current price
        
        Returns:
        bool: Success indicator
        """
        timestamp = datetime.now()
        
        if action.lower() == 'buy':
            # Calculate cost with fee
            cost = amount * price * 1.001
            
            # Check if we have enough quote currency
            if cost > self.quote_balance:
                print_error(f"SIMULATION: Insufficient {self.quote_currency} balance for buy")
                return False
            
            # Update balances
            self.quote_balance -= cost
            self.base_balance += amount
            
        elif action.lower() == 'sell':
            # Check if we have enough base currency
            if amount > self.base_balance:
                print_error(f"SIMULATION: Insufficient {self.base_currency} balance for sell")
                return False
            
            # Calculate proceeds with fee
            proceeds = amount * price * 0.999
            
            # Update balances
            self.base_balance -= amount
            self.quote_balance += proceeds
            
        else:
            print_error(f"SIMULATION: Unknown action {action}")
            return False
        
        # Calculate value for transaction record
        value = amount * price
        
        # Record transaction
        transaction = {
            'timestamp': timestamp.isoformat(),
            'action': action.lower(),
            'amount': amount,
            'price': price,
            'value': value,
            'quote_balance_after': self.quote_balance,
            'base_balance_after': self.base_balance
        }
        
        # Add to transaction history cache
        self.transaction_history.append(transaction)
        
        # Store in database
        self.db.add_transaction(
            symbol=self.symbol,
            action=action.lower(),
            amount=amount,
            price=price,
            value=value,
            quote_balance_after=self.quote_balance,
            base_balance_after=self.base_balance
        )
        
        # Update balance history
        total_value = self.quote_balance + (self.base_balance * price)
        
        balance_entry = {
            'timestamp': timestamp.isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'price': price,
            'total_value_in_quote': total_value
        }
        
        # Add to balance history cache
        self.balance_history.append(balance_entry)
        
        # Store in database
        self.db.add_balance_entry(
            symbol=self.symbol,
            quote_balance=self.quote_balance,
            base_balance=self.base_balance,
            price=price,
            total_value_in_quote=total_value
        )
        
        # Export updated data
        self._save_data()
        
        return True
    
    def update_price(self, current_price):
        """
        Update current price without trading
        
        Parameters:
        current_price (float): Current price
        """
        timestamp = datetime.now()
        
        # Calculate total value
        total_value = self.quote_balance + (self.base_balance * current_price)
        
        # Create balance entry
        balance_entry = {
            'timestamp': timestamp.isoformat(),
            'quote_balance': self.quote_balance,
            'base_balance': self.base_balance,
            'price': current_price,
            'total_value_in_quote': total_value
        }
        
        # Add to cache
        self.balance_history.append(balance_entry)
        
        # Only save to database occasionally to reduce I/O
        if len(self.balance_history) % 10 == 0:
            self.db.add_balance_entry(
                symbol=self.symbol,
                quote_balance=self.quote_balance,
                base_balance=self.base_balance,
                price=current_price,
                total_value_in_quote=total_value
            )
            
            # Export updated data less frequently
            if len(self.balance_history) % 50 == 0:
                self._save_data()
    
    def get_current_balance(self, current_price):
        """
        Get current balance information
        
        Parameters:
        current_price (float): Current price
        
        Returns:
        dict: Balance information
        """
        total_value = self.quote_balance + (self.base_balance * current_price)
        
        # Calculate profit/loss
        if len(self.balance_history) > 0:
            initial_value = self.balance_history[0]['total_value_in_quote']
            profit_loss = total_value - initial_value
            profit_loss_pct = (profit_loss / initial_value * 100) if initial_value > 0 else 0
        else:
            initial_value = self.quote_balance
            profit_loss = 0
            profit_loss_pct = 0
        
        return {
            'quote_currency': self.quote_currency,
            'quote_balance': self.quote_balance,
            'base_currency': self.base_currency,
            'base_balance': self.base_balance,
            'current_price': current_price,
            'total_value_in_quote': total_value,
            'initial_value': initial_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        }
    
    def _save_data(self):
        """Export simulation data to JSON file (for backwards compatibility)"""
        try:
            # Create symbol directory
            symbol_dir = os.path.join(self.data_dir, self.symbol.replace('/', '_'))
            os.makedirs(symbol_dir, exist_ok=True)
            
            # Export from database to JSON
            self.db.export_to_json(
                symbol=self.symbol,
                target_file=os.path.join(symbol_dir, 'simulation_data.json')
            )
            
        except Exception as e:
            print_error(f"Error saving simulation data: {e}")
    
    def generate_performance_report(self, current_price):
        """
        Generate a performance report
        
        Parameters:
        current_price (float): Current price
        
        Returns:
        dict: Performance metrics
        """
        # Get performance from database
        performance = self.db.get_symbol_performance(self.symbol)
        
        if performance:
            # Add additional metrics
            performance['current_price'] = current_price
            
            # Get trade metrics
            if self.transaction_history:
                buy_count = sum(1 for t in self.transaction_history if t['action'] == 'buy')
                sell_count = sum(1 for t in self.transaction_history if t['action'] == 'sell')
                
                # Calculate avg prices
                if buy_count > 0:
                    avg_buy_price = sum(t['price'] for t in self.transaction_history if t['action'] == 'buy') / buy_count
                    performance['avg_buy_price'] = avg_buy_price
                
                if sell_count > 0:
                    avg_sell_price = sum(t['price'] for t in self.transaction_history if t['action'] == 'sell') / sell_count
                    performance['avg_sell_price'] = avg_sell_price
                
                performance['total_trades'] = buy_count + sell_count
                performance['buy_trades'] = buy_count
                performance['sell_trades'] = sell_count
            
            # Calculate position status
            if self.base_balance > 0:
                performance['current_position'] = 'In market'
            else:
                performance['current_position'] = 'In cash'
                
            performance['current_time'] = datetime.now().isoformat()
            
            return performance
        
        # Fallback to calculating from instance variables if database info not available
        if not self.balance_history:
            return {'error': 'No balance history available'}
        
        # Get first balance entry
        initial = self.balance_history[0]
        current = self.get_current_balance(current_price)
        
        # Calculate metrics
        initial_value = initial['total_value_in_quote']
        current_value = current['total_value_in_quote']
        
        absolute_return = current_value - initial_value
        percent_return = (absolute_return / initial_value) * 100 if initial_value > 0 else 0
        
        # Count trades
        buy_count = sum(1 for t in self.transaction_history if t['action'] == 'buy')
        sell_count = sum(1 for t in self.transaction_history if t['action'] == 'sell')
        
        # Calculate avg prices
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
            'current_position': 'In market' if self.base_balance > 0 else 'In cash',
            'start_time': initial['timestamp'],
            'current_time': datetime.now().isoformat(),
            'base_currency': self.base_currency,
            'quote_currency': self.quote_currency
        }
    
    def plot_performance(self, save_path=None):
        """
        Generate and save a performance chart
        
        Parameters:
        save_path (str): Path to save chart (default: performance_chart.png in symbol directory)
        
        Returns:
        str: Path to saved chart
        """
        # If no save path provided, use the symbol directory
        if save_path is None:
            symbol_dir = os.path.join(self.data_dir, self.symbol.replace('/', '_'))
            os.makedirs(symbol_dir, exist_ok=True)
            save_path = os.path.join(symbol_dir, 'performance_chart.png')
        
        try:
            # Use balance history from database for more accuracy
            balance_history = self.db.get_balance_history(self.symbol)
            
            if not balance_history:
                balance_history = self.balance_history
                
            if not balance_history:
                return "No data to plot"
            
            # Convert to DataFrame
            df = pd.DataFrame(balance_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create figure with subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
            
            # Plot total value
            ax1.plot(df['timestamp'], df['total_value_in_quote'], 'b-', label='Total Value')
            ax1.set_title(f'Simulation Performance: {self.symbol}')
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
            transactions = self.db.get_transactions(self.symbol)
            if not transactions and self.transaction_history:
                transactions = self.transaction_history
                
            if transactions:
                trans_df = pd.DataFrame(transactions)
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
        
        except Exception as e:
            print_error(f"Error generating performance chart: {e}")
            import traceback
            traceback.print_exc()
            return f"Error generating chart: {str(e)}"


def load_simulation_data(data_dir='simulation_data'):
    """
    Load existing simulation data
    
    Parameters:
    data_dir (str): Directory where simulation data is stored
    
    Returns:
    tuple: (SimulationTracker instance, success boolean)
    """
    # Check if we should use the database implementation
    db_path = os.path.join(data_dir, 'simulation_data.db')
    use_db = os.path.exists(db_path)
    
    try:
        if use_db:
            # Initialize database
            db = SimulationDatabase(data_dir)
            
            # Get all symbols
            symbols = db.get_all_symbols()
            
            if not symbols:
                print_warning("No symbols found in database")
                return None, False
            
            # Use first symbol for now (in future, could pass symbol parameter)
            symbol_entry = symbols[0]
            symbol = symbol_entry['symbol']
            
            # Create simulation tracker
            sim_tracker = SimulationTracker(
                initial_balance=symbol_entry['initial_balance'],
                base_currency=symbol_entry['base_currency'],
                quote_currency=symbol_entry['quote_currency'],
                data_dir=data_dir
            )
            
            # Set symbol
            sim_tracker.symbol = symbol
            
            # Get balance history and transactions from database
            balance_history = db.get_balance_history(symbol)
            transactions = db.get_transactions(symbol)
            
            # Set current balances
            if balance_history:
                latest = balance_history[-1]
                sim_tracker.quote_balance = latest['quote_balance']
                sim_tracker.base_balance = latest['base_balance']
            
            # Cache history in instance for compatibility
            sim_tracker.balance_history = balance_history
            sim_tracker.transaction_history = transactions
            
            print_success(f"Loaded existing simulation data from database for {symbol}")
            return sim_tracker, True
            
        else:
            # Check for JSON file
            data_file = os.path.join(data_dir, 'simulation_data.json')
            if not os.path.exists(data_file):
                # If no direct file in data_dir, look for symbol subdirectories
                subdirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
                for subdir in subdirs:
                    symbol_data_file = os.path.join(data_dir, subdir, 'simulation_data.json')
                    if os.path.exists(symbol_data_file):
                        data_file = symbol_data_file
                        break
                else:
                    print_warning(f"No simulation data files found in {data_dir}")
                    return None, False
            
            # Load from JSON
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            balance_history = data.get('balance_history', [])
            transactions = data.get('transactions', [])
            
            if not balance_history:
                print_warning("No balance history found in data file")
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
                
            # Try to extract from directory name if possible
            file_dir = os.path.basename(os.path.dirname(data_file))
            if '_' in file_dir:
                symbol_parts = file_dir.split('_')
                if len(symbol_parts) == 2:
                    base_currency = symbol_parts[0]
                    quote_currency = symbol_parts[1]
            
            # Create simulation tracker
            sim_tracker = SimulationTracker(
                initial_balance=quote_balance,
                base_currency=base_currency,
                quote_currency=quote_currency,
                data_dir=data_dir
            )
            
            # Set history
            sim_tracker.balance_history = balance_history
            sim_tracker.transaction_history = transactions
            
            # Set current balances from the most recent entry
            if balance_history:
                latest_entry = balance_history[-1]
                sim_tracker.quote_balance = latest_entry.get('quote_balance', quote_balance)
                sim_tracker.base_balance = latest_entry.get('base_balance', 0)
            
            print_success(f"Loaded existing simulation data from file for {base_currency}/{quote_currency}")
            return sim_tracker, True
        
    except Exception as e:
        print_error(f"Error loading simulation data: {e}")
        import traceback
        traceback.print_exc()
        return None, False