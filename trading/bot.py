"""
Updates to the CryptoTradingBot class to support high frequency trading
"""

import time
import os
import ccxt
import config
from datetime import datetime

from utils.data_utils import prepare_ohlcv_dataframe, calculate_moving_averages
from utils.api_utils import make_api_request
from trading.strategies import calculate_ma_crossover_signals, calculate_enhanced_signals, calculate_scalping_signals, calculate_high_frequency_signals
from trading.order import check_balance, execute_trade
from trading.simulation import SimulationTracker, load_simulation_data
from trading.market_analysis import fetch_ohlcv_data, analyze_market
from trading.execution.bot_execution import process_signals, handle_market_update
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_header, 
    print_simulation, format_profit, format_percentage, Colors
)

class CryptoTradingBot:
    def __init__(self, symbol, timeframe, api_key, base_url, amount, short_window, long_window, 
                simulation_mode=False, use_enhanced_strategy=True, use_scalping_strategy=False,
                take_profit_percentage=1.5, stop_loss_percentage=1.0, max_position_size=5,
                high_frequency_mode=True, data_dir=None):
        """
        Initialize the trading bot with exchange details and trading parameters
        
        Parameters:
        symbol (str): The trading pair (e.g., 'BTC/USDT')
        timeframe (str): The candle timeframe (e.g., '1h')
        api_key (str): API key for authentication
        base_url (str): Base URL for the API
        amount (float): Base amount to trade for each position
        short_window (int): Short moving average window
        long_window (int): Long moving average window
        simulation_mode (bool): Force simulation mode even if credentials exist
        use_enhanced_strategy (bool): Whether to use the enhanced strategy for more frequent trading
        use_scalping_strategy (bool): Whether to use the scalping strategy for frequent trading
        take_profit_percentage (float): Percentage gain to trigger take profit
        stop_loss_percentage (float): Percentage loss to trigger stop loss
        max_position_size (float): Maximum position size as a multiple of the base amount
        high_frequency_mode (bool): Whether to use high frequency trading mode
        data_dir (str): Directory to store data for this symbol
        """
        # Exchange configuration
        self.symbol = symbol.strip()  # Ensure no whitespace
        self.timeframe = timeframe
        self.api_key = api_key
        self.base_url = base_url
        
        # Connect to exchange (for market data only)
        self.exchange = ccxt.binance({
            'enableRateLimit': True
        })
        
        # Set the data directory for this symbol
        self.data_dir = data_dir if data_dir else os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Trading parameters
        self.base_position_size = amount
        self.current_position_size = 0.0  # Track current position size instead of binary in_position flag
        self.max_position_size = max_position_size  # Maximum position as multiple of base amount
        self.position_entry_prices = []  # Track entry prices for each position increment
        
        # Position sizing parameters
        self.position_increment = 1.0  # Default scaling factor for position increments
        self.max_position_increments = max_position_size  # Maximum number of increments
        self.min_signal_strength_for_increment = 0.5  # Minimum signal strength to add to position
        
        # Moving average parameters
        self.short_window = short_window
        self.long_window = long_window
        
        # Strategy configuration
        self.use_enhanced_strategy = use_enhanced_strategy and not use_scalping_strategy and not high_frequency_mode
        self.use_scalping_strategy = use_scalping_strategy and not high_frequency_mode
        self.high_frequency_mode = high_frequency_mode
        
        # If high frequency mode is enabled, it takes precedence over other strategies
        if self.high_frequency_mode:
            self.use_enhanced_strategy = False
            self.use_scalping_strategy = False
        
        # Risk management parameters
        self.take_profit_percentage = take_profit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        
        # High frequency specific parameters
        if high_frequency_mode:
            # Use tighter risk parameters for high frequency trading
            self.hf_take_profit_percentage = 0.5  # Lower take profit for faster trades
            self.hf_stop_loss_percentage = 0.3    # Tighter stop loss for better protection
            self.trade_counter = 0                # Counter for high frequency trade tracking
            self.last_minute_trades = 0           # Tracks trades in the last minute
            self.minute_trade_limit = 20          # Maximum trades per minute
            self.last_trade_time = None           # Time of last trade
        
        # Simulation mode flag
        self.simulation_mode = simulation_mode
        
        # Determine if we're in simulation mode
        has_credentials = self.api_key is not None
        has_rsa_key = os.path.isfile('binance_private_key.pem')
        self.in_simulation_mode = self.simulation_mode or not has_credentials or not has_rsa_key
        
        # Initialize simulation tracker if in simulation mode
        self.sim_tracker = None
        if self.in_simulation_mode:
            # Try to load existing simulation data
            loaded_tracker, success = load_simulation_data(self.data_dir)
            if success:
                self.sim_tracker = loaded_tracker
                print_success(f"Loaded existing simulation data for {self.symbol}")
                
                # Check if we have any existing position
                current_balance = self.sim_tracker.get_current_balance(0)  # Price doesn't matter for the check
                self.current_position_size = current_balance['base_balance']
                
                # Reconstruct position entry prices if possible
                # For simplicity, treat all existing balance as a single position with a zero entry price
                if self.current_position_size > 0:
                    self.position_entry_prices = [(self.current_position_size, 0)]
                    print_info(f"Recovered existing position of {self.current_position_size} {self.symbol.split('/')[0]}")
            else:
                # Start a new simulation with default values
                base_currency = self.symbol.split('/')[0]
                quote_currency = self.symbol.split('/')[1]
                self.sim_tracker = SimulationTracker(
                    initial_balance=100.0,  # Start with 100 USDT
                    base_currency=base_currency,
                    quote_currency=quote_currency,
                    data_dir=self.data_dir
                )
                print_info(f"Started new simulation with 100 {quote_currency} for {self.symbol}")
        
        print_header(f"Bot initialized for {self.symbol} on Binance using {timeframe} timeframe")
        
        if self.high_frequency_mode:
            print_header(f"{self.symbol}: HIGH FREQUENCY TRADING MODE ENABLED")
            print_info(f"Using ultra-short EMA combinations with fast RSI and Stochastics")
            print_info(f"Take Profit: {self.hf_take_profit_percentage}%, Stop Loss: {self.hf_stop_loss_percentage}%")
        elif self.use_enhanced_strategy:
            print_info(f"{self.symbol}: Using enhanced trading strategy for more frequent trades")
        elif self.use_scalping_strategy:
            print_info(f"{self.symbol}: Using scalping strategy for very frequent trades!")
        
    @staticmethod
    def fetch_ohlcv_data(exchange, symbol, timeframe, limit=30):
        """
        Fetch candlestick data from the exchange with optimization for high frequency
        
        Parameters:
        exchange (ccxt.Exchange): Exchange instance
        symbol (str): The trading pair (e.g., 'BTC/USDT')
        timeframe (str): The candle timeframe (e.g., '30s', '1m')
        limit (int): Number of candles to fetch (reduced for faster processing)
        
        Returns:
        pandas.DataFrame: OHLCV data
        """
        try:
            # Ensure symbol is properly formatted (trim whitespace)
            clean_symbol = symbol.strip()
            
            # Convert timeframes not supported by Binance to supported ones
            binance_timeframe = timeframe
            if timeframe in ['30s', '10s', '5s']:
                print_info(f"Converting {timeframe} to '1m' for Binance API compatibility")
                binance_timeframe = '1m'
            
            # Fetch OHLCV data using CCXT (no authentication needed)
            ohlcv = exchange.fetch_ohlcv(clean_symbol, binance_timeframe, limit=limit)
            
            # Convert to DataFrame
            df = prepare_ohlcv_dataframe(ohlcv)
            
            return df
        except Exception as e:
            print_error(f"Error fetching data: {e}")
            return None
        
    def analyze_market(self, limit=30):
        """
        Analyze market data and calculate signals
        
        Parameters:
        limit (int): Number of candles to fetch
        
        Returns:
        pandas.DataFrame: OHLCV data with signals
        """
        return analyze_market(
            self.exchange, 
            self.symbol, 
            self.timeframe, 
            self.short_window, 
            self.long_window, 
            self.use_enhanced_strategy, 
            self.use_scalping_strategy, 
            limit
        )
    
    def can_make_trade(self):
        """
        Check if we can make a trade based on frequency limits
        
        Returns:
        bool: Whether we can make a trade
        """
        if not self.high_frequency_mode:
            return True
            
        # Check if this is our first trade
        if self.last_trade_time is None:
            self.last_minute_trades = 1
            self.last_trade_time = datetime.now()
            return True
            
        # Check how much time has passed since last trade
        now = datetime.now()
        seconds_since_last_trade = (now - self.last_trade_time).total_seconds()
        
        # Reset counter if a minute has passed
        if seconds_since_last_trade > 60:
            self.last_minute_trades = 0
            
        # Check if we're within trade frequency limits
        if self.last_minute_trades < self.minute_trade_limit:
            self.last_minute_trades += 1
            self.last_trade_time = now
            return True
            
        return False
    
    def run_bot(self, interval=2):
        """
        Run the trading bot in a loop, optimized for high frequency
        
        Parameters:
        interval (int): Seconds between each check
        """
        # Print the operating mode at startup
        symbol_prefix = f"[{self.symbol}] "
        
        if self.in_simulation_mode:
            if self.simulation_mode:
                print_warning(f"{symbol_prefix}SIMULATION MODE: Enabled by configuration. No real trades will be executed.")
            else:
                missing = []
                if not self.api_key:
                    missing.append("API key")
                if not os.path.isfile('binance_private_key.pem'):
                    missing.append("RSA private key")
                print_warning(f"{symbol_prefix}SIMULATION MODE: {', '.join(missing)} not found. No real trades will be executed.")
        else:
            print(f"{Colors.BG_BLUE}{Colors.WHITE} LIVE TRADING MODE {Colors.RESET} {symbol_prefix}Bot will execute real trades on Binance!")
        
        # Print strategy information
        if self.high_frequency_mode:
            print_info(f"{symbol_prefix}Using HIGH FREQUENCY strategy with {self.timeframe} candles")
            print_info(f"{symbol_prefix}EMA windows: 1/3/5, Fast RSI period: 5, Ultra-fast position management")
        elif self.use_scalping_strategy:
            print_info(f"{symbol_prefix}Using SCALPING strategy with {self.timeframe} candles")
        elif self.use_enhanced_strategy:
            print_info(f"{symbol_prefix}Using ENHANCED strategy with {self.timeframe} candles")
        else:
            print_info(f"{symbol_prefix}Using STANDARD MA CROSSOVER strategy with {self.timeframe} candles")
        
        # Print position sizing information
        print_info(f"{symbol_prefix}Base position size: {self.base_position_size} {self.symbol.split('/')[0]}")
        print_info(f"{symbol_prefix}Maximum position size: {self.base_position_size * self.max_position_size} {self.symbol.split('/')[0]} "
                  f"({self.max_position_size}x base size)")
        
        print_info(f"{symbol_prefix}Moving average windows: {self.short_window}/{self.long_window}")
        
        if self.high_frequency_mode:
            print_info(f"{symbol_prefix}High Frequency Take Profit: {self.hf_take_profit_percentage}%, Stop Loss: {self.hf_stop_loss_percentage}%")
            print_info(f"{symbol_prefix}Maximum trade frequency: {self.minute_trade_limit} trades per minute")
        else:
            print_info(f"{symbol_prefix}Take profit: {self.take_profit_percentage}%, Stop loss: {self.stop_loss_percentage}%")
            
        print_info(f"{symbol_prefix}Bot started. Checking for signals every {interval} seconds.")
        
        try:
            # Delegate bot execution to the bot_execution module
            handle_market_update(
                self, 
                interval=interval,
                symbol_prefix=symbol_prefix
            )
            
        except KeyboardInterrupt:
            print_warning(f"{symbol_prefix}Bot stopped by user.")
            
            # Generate final report and plot in simulation mode
            if self.in_simulation_mode and self.sim_tracker:
                df = self.fetch_ohlcv_data(limit=1)
                if df is not None and len(df) > 0:
                    current_price = df.iloc[-1]['close']
                    report = self.sim_tracker.generate_performance_report(current_price)
                    chart_path = self.sim_tracker.plot_performance()
                    
                    print_header(f"{symbol_prefix}===== FINAL SIMULATION REPORT =====")
                    print_info(f"{symbol_prefix}Initial balance: ${report['initial_balance']:.2f} USDT")
                    print_info(f"{symbol_prefix}Final balance: ${report['current_balance']:.2f} USDT")
                    
                    return_formatted = format_profit(report['absolute_return'])
                    percent_return_formatted = format_percentage(report['percent_return'])
                    
                    print_info(f"{symbol_prefix}Return: {return_formatted} USDT ({percent_return_formatted})")
                    print_info(f"{symbol_prefix}Total trades: {report['total_trades']} (Buy: {report['buy_trades']}, Sell: {report['sell_trades']})")
                    
                    # Calculate trade frequency
                    if 'start_time' in report and 'current_time' in report:
                        start_time = datetime.fromisoformat(report['start_time'])
                        end_time = datetime.fromisoformat(report['current_time'])
                        duration_seconds = (end_time - start_time).total_seconds()
                        duration_minutes = duration_seconds / 60
                        
                        if duration_minutes > 0 and report['total_trades'] > 0:
                            trades_per_minute = report['total_trades'] / duration_minutes
                            print_info(f"{symbol_prefix}Trading frequency: {trades_per_minute:.2f} trades per minute")
                            print_info(f"{symbol_prefix}Trading duration: {duration_minutes:.2f} minutes")
                    
                    print_info(f"{symbol_prefix}Performance chart saved to: {chart_path}")
                    print_header(f"{symbol_prefix}=====================================")
                    
        except Exception as e:
            print_error(f"{symbol_prefix}Error running bot: {e}")
            raise