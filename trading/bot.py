import time
import os
import ccxt
from datetime import datetime

from utils.data_utils import prepare_ohlcv_dataframe, calculate_moving_averages
from utils.api_utils import make_api_request
from trading.strategies import calculate_ma_crossover_signals, calculate_enhanced_signals, calculate_scalping_signals
from trading.order import check_balance, execute_trade
from trading.simulation import SimulationTracker, load_simulation_data
from trading.market_analysis import fetch_ohlcv_data, analyze_market
from trading.bot_execution import process_signals, handle_market_update
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_header, 
    print_simulation, format_profit, format_percentage, Colors
)

class CryptoTradingBot:
    def __init__(self, symbol, timeframe, api_key, base_url, amount, short_window, long_window, 
                 simulation_mode=False, use_enhanced_strategy=True, use_scalping_strategy=False,
                 take_profit_percentage=1.5, stop_loss_percentage=1.0):
        """
        Initialize the trading bot with exchange details and trading parameters
        
        Parameters:
        symbol (str): The trading pair (e.g., 'BTC/USDT')
        timeframe (str): The candle timeframe (e.g., '1h')
        api_key (str): API key for authentication
        base_url (str): Base URL for the API
        amount (float): Amount to trade
        short_window (int): Short moving average window
        long_window (int): Long moving average window
        simulation_mode (bool): Force simulation mode even if credentials exist
        use_enhanced_strategy (bool): Whether to use the enhanced strategy for more frequent trading
        use_scalping_strategy (bool): Whether to use the scalping strategy for very frequent trading
        take_profit_percentage (float): Percentage gain to trigger take profit
        stop_loss_percentage (float): Percentage loss to trigger stop loss
        """
        # Exchange configuration
        self.symbol = symbol
        self.timeframe = timeframe
        self.api_key = api_key
        self.base_url = base_url
        
        # Connect to exchange (for market data only)
        self.exchange = ccxt.binance({
            'enableRateLimit': True
        })
        
        # Trading parameters
        self.amount = amount
        self.in_position = False
        
        # Moving average parameters
        self.short_window = short_window
        self.long_window = long_window
        
        # Strategy configuration
        self.use_enhanced_strategy = use_enhanced_strategy and not use_scalping_strategy
        self.use_scalping_strategy = use_scalping_strategy
        
        # Risk management parameters
        self.take_profit_percentage = take_profit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.entry_price = None
        
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
            loaded_tracker, success = load_simulation_data()
            if success:
                self.sim_tracker = loaded_tracker
                print_success("Loaded existing simulation data")
            else:
                # Start a new simulation with default values
                base_currency = self.symbol.split('/')[0]
                quote_currency = self.symbol.split('/')[1]
                self.sim_tracker = SimulationTracker(
                    initial_balance=100.0,  # Start with 100 USDT
                    base_currency=base_currency,
                    quote_currency=quote_currency
                )
                print_info(f"Started new simulation with 100 {quote_currency}")
        
        print_header(f"Bot initialized for {self.symbol} on Binance using {timeframe} timeframe")
        if self.use_enhanced_strategy:
            print_info("Using enhanced trading strategy for more frequent trades")
        elif self.use_scalping_strategy:
            print_info("Using scalping strategy for very frequent trades!")
    
    def fetch_ohlcv_data(self, limit=100):
        """
        Fetch candlestick data from the exchange
        
        Parameters:
        limit (int): Number of candles to fetch
        
        Returns:
        pandas.DataFrame: OHLCV data
        """
        return fetch_ohlcv_data(self.exchange, self.symbol, self.timeframe, limit)
    
    def analyze_market(self, limit=100):
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
    
    def run_bot(self, interval=60):
        """
        Run the trading bot in a loop
        
        Parameters:
        interval (int): Seconds between each check
        """
        # Print the operating mode at startup
        if self.in_simulation_mode:
            if self.simulation_mode:
                print_warning("SIMULATION MODE: Enabled by configuration. No real trades will be executed.")
            else:
                missing = []
                if not self.api_key:
                    missing.append("API key")
                if not os.path.isfile('binance_private_key.pem'):
                    missing.append("RSA private key")
                print_warning(f"SIMULATION MODE: {', '.join(missing)} not found. No real trades will be executed.")
        else:
            print(f"{Colors.BG_BLUE}{Colors.WHITE} LIVE TRADING MODE {Colors.RESET} Bot will execute real trades on Binance!")
        
        # Print strategy information
        if self.use_scalping_strategy:
            print_info(f"Using SCALPING strategy with {self.timeframe} candles")
        elif self.use_enhanced_strategy:
            print_info(f"Using ENHANCED strategy with {self.timeframe} candles")
        else:
            print_info(f"Using STANDARD MA CROSSOVER strategy with {self.timeframe} candles")
        
        print_info(f"Moving average windows: {self.short_window}/{self.long_window}")
        print_info(f"Take profit: {self.take_profit_percentage}%, Stop loss: {self.stop_loss_percentage}%")
        print_info(f"Bot started. Checking for signals every {interval} seconds.")
        
        # For simulation, determine if we're currently holding a position
        if self.in_simulation_mode and self.sim_tracker:
            current_balance = self.sim_tracker.get_current_balance(0)  # Price doesn't matter for the check
            self.in_position = current_balance['base_balance'] > 0
        
        try:
            # Delegate bot execution to the bot_execution module
            handle_market_update(
                self, 
                interval=interval
            )
            
        except KeyboardInterrupt:
            print_warning("Bot stopped by user.")
            
            # Generate final report and plot in simulation mode
            if self.in_simulation_mode and self.sim_tracker:
                df = self.fetch_ohlcv_data(limit=1)
                if df is not None and len(df) > 0:
                    current_price = df.iloc[-1]['close']
                    report = self.sim_tracker.generate_performance_report(current_price)
                    chart_path = self.sim_tracker.plot_performance()
                    
                    print_header("===== FINAL SIMULATION REPORT =====")
                    print_info(f"Initial balance: ${report['initial_balance']:.2f} USDT")
                    print_info(f"Final balance: ${report['current_balance']:.2f} USDT")
                    
                    return_formatted = format_profit(report['absolute_return'])
                    percent_return_formatted = format_percentage(report['percent_return'])
                    
                    print_info(f"Return: {return_formatted} USDT ({percent_return_formatted})")
                    print_info(f"Total trades: {report['total_trades']} (Buy: {report['buy_trades']}, Sell: {report['sell_trades']})")
                    print_info(f"Performance chart saved to: {chart_path}")
                    print_header("=====================================")
                    
        except Exception as e:
            print_error(f"Error running bot: {e}")
            raise