import time
import os
import ccxt
from datetime import datetime

from utils.data_utils import prepare_ohlcv_dataframe, calculate_moving_averages
from utils.api_utils import make_api_request
from trading.strategies import calculate_ma_crossover_signals, calculate_enhanced_signals, get_latest_signal
from trading.order import check_balance, execute_trade
from trading.simulation import SimulationTracker, load_simulation_data
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_header, 
    print_simulation, format_profit, format_percentage, Colors
)

class CryptoTradingBot:
    def __init__(self, symbol, timeframe, api_key, base_url, amount, short_window, long_window, simulation_mode=False, use_enhanced_strategy=True):
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
        self.use_enhanced_strategy = use_enhanced_strategy
        
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
    
    def fetch_ohlcv_data(self, limit=100):
        """
        Fetch candlestick data from the exchange
        
        Parameters:
        limit (int): Number of candles to fetch
        
        Returns:
        pandas.DataFrame: OHLCV data
        """
        try:
            # Fetch OHLCV data using CCXT (no authentication needed)
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
            
            # Convert to DataFrame
            df = prepare_ohlcv_dataframe(ohlcv)
            
            return df
        except Exception as e:
            print_error(f"Error fetching data: {e}")
            return None
    
    def analyze_market(self, limit=100):
        """
        Analyze market data and calculate signals
        
        Parameters:
        limit (int): Number of candles to fetch
        
        Returns:
        pandas.DataFrame: OHLCV data with signals
        """
        # Fetch latest data
        df = self.fetch_ohlcv_data(limit=limit)
        
        # Calculate moving averages and other indicators
        df = calculate_moving_averages(df, self.short_window, self.long_window)
        
        # Calculate signals based on strategy
        if self.use_enhanced_strategy:
            df = calculate_enhanced_signals(df, self.short_window, self.long_window)
        else:
            df = calculate_ma_crossover_signals(df, self.short_window, self.long_window)
        
        return df
    
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
        
        print_info(f"Bot started. Checking for signals every {interval} seconds.")
        print_info(f"Using {self.timeframe} candles with MA windows of {self.short_window}/{self.long_window}")
        
        # For simulation, determine if we're currently holding a position
        if self.in_simulation_mode and self.sim_tracker:
            current_balance = self.sim_tracker.get_current_balance(0)  # Price doesn't matter for the check
            self.in_position = current_balance['base_balance'] > 0
            
        # Track execution time for performance monitoring
        last_iteration_time = 0
        
        try:
            while True:
                start_time = time.time()
                
                # Analyze market data
                df = self.analyze_market(limit=self.long_window + 10)
                
                if df is not None and len(df) > 0:
                    # Get the latest signal
                    position_change, current_price, short_ma, long_ma = get_latest_signal(df, use_enhanced=self.use_enhanced_strategy)
                    
                    # Update simulation tracker with latest price
                    if self.in_simulation_mode and self.sim_tracker and current_price is not None:
                        self.sim_tracker.update_price(current_price)
                    
                    # Check for buy signal
                    if position_change == 1:
                        print_buy(f"BUY SIGNAL at {datetime.now()}")
                        
                        if not self.in_position:
                            if self.in_simulation_mode and self.sim_tracker:
                                # Execute simulated trade
                                if self.sim_tracker.execute_trade('buy', self.amount, current_price):
                                    self.in_position = True
                                    # Generate and save performance chart
                                    self.sim_tracker.plot_performance()
                            elif not self.in_simulation_mode:
                                # Execute real trade
                                if execute_trade('buy', self.base_url, self.api_key, self.symbol, self.amount):
                                    self.in_position = True
                        else:
                            print_warning("Already in position - skipping buy")
                    
                    # Check for sell signal
                    elif position_change == -1:
                        print_sell(f"SELL SIGNAL at {datetime.now()}")
                        
                        if self.in_position:
                            if self.in_simulation_mode and self.sim_tracker:
                                # Execute simulated trade
                                if self.sim_tracker.execute_trade('sell', self.amount, current_price):
                                    self.in_position = False
                                    # Generate and save performance chart
                                    self.sim_tracker.plot_performance()
                            elif not self.in_simulation_mode:
                                # Execute real trade
                                if execute_trade('sell', self.base_url, self.api_key, self.symbol, self.amount):
                                    self.in_position = False
                        else:
                            print_warning("Not in position - skipping sell")
                    
                    # No signal
                    else:
                        print_info(f"No trading signal at {datetime.now()}")
                    
                    # Print latest prices
                    if current_price is not None:
                        print_price(f"Current price: ${current_price:,.2f}")
                    if short_ma is not None and long_ma is not None:
                        print_price(f"Short MA: ${short_ma:.2f}, Long MA: ${long_ma:.2f}")
                    
                    # Print additional indicators if using enhanced strategy
                    if self.use_enhanced_strategy and 'rsi' in df.columns and 'macd' in df.columns:
                        latest = df.iloc[-1]
                        
                        # Color RSI based on overbought/oversold conditions
                        rsi_value = latest['rsi']
                        if rsi_value > 70:
                            rsi_formatted = f"{Colors.RED}{rsi_value:.2f}{Colors.RESET}"
                        elif rsi_value < 30:
                            rsi_formatted = f"{Colors.GREEN}{rsi_value:.2f}{Colors.RESET}"
                        else:
                            rsi_formatted = f"{rsi_value:.2f}"
                            
                        # Color MACD based on signal line crossover
                        macd_value = latest['macd']
                        macd_signal_value = latest['macd_signal']
                        
                        if macd_value > macd_signal_value:
                            macd_formatted = f"{Colors.GREEN}{macd_value:.2f}{Colors.RESET}"
                            macd_signal_formatted = f"{macd_signal_value:.2f}"
                        elif macd_value < macd_signal_value:
                            macd_formatted = f"{Colors.RED}{macd_value:.2f}{Colors.RESET}"
                            macd_signal_formatted = f"{macd_signal_value:.2f}"
                        else:
                            macd_formatted = f"{macd_value:.2f}"
                            macd_signal_formatted = f"{macd_signal_value:.2f}"
                            
                        print_info(f"RSI: {rsi_formatted}, MACD: {macd_formatted}, MACD Signal: {macd_signal_formatted}")
                        
                        if 'bb_lower' in df.columns and 'bb_upper' in df.columns:
                            distance_to_lower = ((current_price - latest['bb_lower']) / current_price) * 100
                            distance_to_upper = ((latest['bb_upper'] - current_price) / current_price) * 100
                            
                            # Color BB distances
                            if distance_to_lower < 2:  # Very close to lower band
                                lower_formatted = f"{Colors.GREEN}{distance_to_lower:.2f}%{Colors.RESET}"
                            else:
                                lower_formatted = f"{distance_to_lower:.2f}%"
                                
                            if distance_to_upper < 2:  # Very close to upper band
                                upper_formatted = f"{Colors.RED}{distance_to_upper:.2f}%{Colors.RESET}"
                            else:
                                upper_formatted = f"{distance_to_upper:.2f}%"
                                
                            print_info(f"BB Distance - Lower: {lower_formatted}, Upper: {upper_formatted}")
                    
                    # Print simulation balance if in simulation mode
                    if self.in_simulation_mode and self.sim_tracker and current_price is not None:
                        balance = self.sim_tracker.get_current_balance(current_price)
                        
                        profit_loss_formatted = format_percentage(balance['profit_loss_pct'])
                        
                        print_simulation(
                            f"Balance: {balance['quote_balance']:.2f} {balance['quote_currency']}, "
                            f"{balance['base_balance']:.8f} {balance['base_currency']}, "
                            f"Total value: ${balance['total_value_in_quote']:.2f} "
                            f"({profit_loss_formatted})"
                        )
                        
                        # Generate a performance report every 10 iterations
                        if int(time.time()) % (interval * 10) < interval:
                            report = self.sim_tracker.generate_performance_report(current_price)
                            
                            print_header("----- SIMULATION PERFORMANCE REPORT -----")
                            print_info(f"Initial balance: ${report['initial_balance']:.2f} {balance['quote_currency']}")
                            print_info(f"Current balance: ${report['current_balance']:.2f} {balance['quote_currency']}")
                            
                            return_formatted = format_profit(report['absolute_return'])
                            percent_return_formatted = format_percentage(report['percent_return'])
                            
                            print_info(f"Return: {return_formatted} {balance['quote_currency']} ({percent_return_formatted})")
                            print_info(f"Total trades: {report['total_trades']} (Buy: {report['buy_trades']}, Sell: {report['sell_trades']})")
                            
                            # Format current position with color
                            if report['current_position'] == 'In market':
                                position_formatted = f"{Colors.GREEN}{report['current_position']}{Colors.RESET}"
                            else:
                                position_formatted = f"{Colors.YELLOW}{report['current_position']}{Colors.RESET}"
                                
                            print_info(f"Current position: {position_formatted}")
                            print_header("-------------------------------------------")
                
                # Calculate execution time
                execution_time = time.time() - start_time
                last_iteration_time = execution_time
                
                # Wait for the next check (adjusting for execution time)
                sleep_time = max(0.1, interval - execution_time)
                time.sleep(sleep_time)
                
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