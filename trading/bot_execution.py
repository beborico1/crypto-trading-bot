"""
Bot execution module for the trading bot.
Handles signal processing, trade execution, and market updates.
"""

import time
from datetime import datetime
from trading.order import execute_trade
from trading.market_analysis import get_signal_info, extract_technical_indicators
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, print_price, print_simulation, 
    format_profit, format_percentage, Colors
)

def process_signals(bot, df, current_price):
    """
    Process trading signals and execute trades accordingly
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    df (pandas.DataFrame): DataFrame with signals
    current_price (float): Current market price
    
    Returns:
    bool: True if signals were processed, False otherwise
    """
    if df is None or len(df) == 0 or current_price is None:
        return False
    
    # Get the latest signal
    position_change, price, short_ma, long_ma = get_signal_info(
        df, 
        use_enhanced_strategy=bot.use_enhanced_strategy, 
        use_scalping_strategy=bot.use_scalping_strategy
    )
    
    # Handle profit taking and stop loss if in position
    if bot.in_position and bot.entry_price is not None:
        price_change_pct = ((current_price - bot.entry_price) / bot.entry_price) * 100
        
        # Take profit
        if price_change_pct >= bot.take_profit_percentage:
            print_sell(f"TAKE PROFIT triggered at ${current_price:.2f} ({price_change_pct:.2f}%)")
            
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated sell for take profit
                if bot.sim_tracker.execute_trade('sell', bot.amount, current_price):
                    bot.in_position = False
                    bot.entry_price = None
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real sell for take profit
                if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, bot.amount):
                    bot.in_position = False
                    bot.entry_price = None
            return True
        
        # Stop loss
        elif price_change_pct <= -bot.stop_loss_percentage:
            print_sell(f"STOP LOSS triggered at ${current_price:.2f} ({price_change_pct:.2f}%)")
            
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated sell for stop loss
                if bot.sim_tracker.execute_trade('sell', bot.amount, current_price):
                    bot.in_position = False
                    bot.entry_price = None
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real sell for stop loss
                if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, bot.amount):
                    bot.in_position = False
                    bot.entry_price = None
            return True
    
    # Check for buy signal
    if position_change == 1:
        print_buy(f"BUY SIGNAL at {datetime.now()}")
        
        if not bot.in_position:
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated trade
                if bot.sim_tracker.execute_trade('buy', bot.amount, current_price):
                    bot.in_position = True
                    bot.entry_price = current_price  # Store entry price
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real trade
                if execute_trade('buy', bot.base_url, bot.api_key, bot.symbol, bot.amount):
                    bot.in_position = True
                    bot.entry_price = current_price  # Store entry price
        else:
            print_warning("Already in position - skipping buy")
        return True
    
    # Check for sell signal
    elif position_change == -1:
        print_sell(f"SELL SIGNAL at {datetime.now()}")
        
        if bot.in_position:
            if bot.in_simulation_mode and bot.sim_tracker:
                # Execute simulated trade
                if bot.sim_tracker.execute_trade('sell', bot.amount, current_price):
                    bot.in_position = False
                    bot.entry_price = None  # Clear entry price
                    # Generate and save performance chart
                    bot.sim_tracker.plot_performance()
            elif not bot.in_simulation_mode:
                # Execute real trade
                if execute_trade('sell', bot.base_url, bot.api_key, bot.symbol, bot.amount):
                    bot.in_position = False
                    bot.entry_price = None  # Clear entry price
        else:
            print_warning("Not in position - skipping sell")
        return True
    
    # No signal
    else:
        print_info(f"No trading signal at {datetime.now()}")
        return False

def display_market_info(bot, df, current_price):
    """
    Display market information and technical indicators
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    df (pandas.DataFrame): DataFrame with technical indicators
    current_price (float): Current market price
    """
    if df is None or len(df) == 0 or current_price is None:
        return
    
    # Extract indicators based on strategy
    indicators = extract_technical_indicators(
        df, 
        use_enhanced_strategy=bot.use_enhanced_strategy, 
        use_scalping_strategy=bot.use_scalping_strategy
    )
    
    # Print price information
    print_price(f"Current price: ${current_price:,.2f}")
    
    # Print MA or EMA values based on strategy
    if bot.use_scalping_strategy:
        if 'ema3' in indicators and 'ema8' in indicators:
            print_price(f"EMA3: ${indicators['ema3']:.2f}, EMA8: ${indicators['ema8']:.2f}")
    else:
        if 'short_ma' in indicators and 'long_ma' in indicators:
            print_price(f"Short MA: ${indicators['short_ma']:.2f}, Long MA: ${indicators['long_ma']:.2f}")
    
    # Print additional indicators based on strategy
    if bot.use_scalping_strategy:
        # Print fast RSI
        if 'fast_rsi' in indicators and 'stoch_k' in indicators and 'stoch_d' in indicators:
            rsi_value = indicators['fast_rsi']
            if rsi_value > 70:
                rsi_formatted = f"{Colors.RED}{rsi_value:.2f}{Colors.RESET}"
            elif rsi_value < 30:
                rsi_formatted = f"{Colors.GREEN}{rsi_value:.2f}{Colors.RESET}"
            else:
                rsi_formatted = f"{rsi_value:.2f}"
            
            # Print Stochastic
            stoch_k = indicators['stoch_k']
            stoch_d = indicators['stoch_d']
            if stoch_k > stoch_d:
                stoch_formatted = f"{Colors.GREEN}K:{stoch_k:.2f} D:{stoch_d:.2f}{Colors.RESET}"
            else:
                stoch_formatted = f"{Colors.RED}K:{stoch_k:.2f} D:{stoch_d:.2f}{Colors.RESET}"
            
            print_info(f"Fast RSI: {rsi_formatted}, Stochastic: {stoch_formatted}")
    
    elif bot.use_enhanced_strategy:
        # Print RSI and MACD
        if 'rsi' in indicators and 'macd' in indicators and 'macd_signal' in indicators:
            # Color RSI based on overbought/oversold conditions
            rsi_value = indicators['rsi']
            if rsi_value > 70:
                rsi_formatted = f"{Colors.RED}{rsi_value:.2f}{Colors.RESET}"
            elif rsi_value < 30:
                rsi_formatted = f"{Colors.GREEN}{rsi_value:.2f}{Colors.RESET}"
            else:
                rsi_formatted = f"{rsi_value:.2f}"
                
            # Color MACD based on signal line crossover
            macd_value = indicators['macd']
            macd_signal_value = indicators['macd_signal']
            
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
    
    # Print Bollinger Band information for any strategy
    if 'bb_lower' in indicators and 'bb_upper' in indicators and current_price is not None:
        distance_to_lower = ((current_price - indicators['bb_lower']) / current_price) * 100
        distance_to_upper = ((indicators['bb_upper'] - current_price) / current_price) * 100
        
        # Determine threshold based on strategy
        threshold = 1 if bot.use_scalping_strategy else 2
        
        # Color BB distances
        if distance_to_lower < threshold:  # Close to lower band
            lower_formatted = f"{Colors.GREEN}{distance_to_lower:.2f}%{Colors.RESET}"
        else:
            lower_formatted = f"{distance_to_lower:.2f}%"
            
        if distance_to_upper < threshold:  # Close to upper band
            upper_formatted = f"{Colors.RED}{distance_to_upper:.2f}%{Colors.RESET}"
        else:
            upper_formatted = f"{distance_to_upper:.2f}%"
            
        print_info(f"BB Distance - Lower: {lower_formatted}, Upper: {upper_formatted}")

def display_simulation_info(bot, current_price):
    """
    Display simulation information
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    """
    if not bot.in_simulation_mode or bot.sim_tracker is None or current_price is None:
        return
    
    balance = bot.sim_tracker.get_current_balance(current_price)
    
    profit_loss_formatted = format_percentage(balance['profit_loss_pct'])
    
    print_simulation(
        f"Balance: {balance['quote_balance']:.2f} {balance['quote_currency']}, "
        f"{balance['base_balance']:.8f} {balance['base_currency']}, "
        f"Total value: ${balance['total_value_in_quote']:.2f} "
        f"({profit_loss_formatted})"
    )
    
    # If in position, show current trade P/L
    if bot.in_position and bot.entry_price is not None:
        trade_pnl_pct = ((current_price - bot.entry_price) / bot.entry_price) * 100
        trade_pnl_formatted = format_percentage(trade_pnl_pct)
        
        print_simulation(
            f"Current trade: Entry @ ${bot.entry_price:.2f}, Current P/L: {trade_pnl_formatted}"
        )

def display_performance_report(bot, current_price, interval, current_time):
    """
    Display performance report periodically
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    current_price (float): Current market price
    interval (int): Check interval in seconds
    current_time (float): Current timestamp
    """
    if not bot.in_simulation_mode or bot.sim_tracker is None or current_price is None:
        return
    
    # Generate a performance report periodically (every 10 intervals)
    if int(current_time) % (interval * 10) < interval:
        report = bot.sim_tracker.generate_performance_report(current_price)
        balance = bot.sim_tracker.get_current_balance(current_price)
        
        print_info("----- SIMULATION PERFORMANCE REPORT -----")
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
        print_info("-------------------------------------------")

def handle_market_update(bot, interval=60):
    """
    Handle market updates in a loop
    
    Parameters:
    bot (CryptoTradingBot): Bot instance
    interval (int): Seconds between each check
    """
    # Track execution time
    last_iteration_time = 0
    
    while True:
        start_time = time.time()
        
        # Analyze market data
        df = bot.analyze_market(limit=bot.long_window + 10)
        
        if df is not None and len(df) > 0:
            # Get current price
            current_price = df.iloc[-1]['close']
            
            # Update simulation tracker with latest price
            if bot.in_simulation_mode and bot.sim_tracker and current_price is not None:
                bot.sim_tracker.update_price(current_price)
            
            # Process signals and execute trades
            process_signals(bot, df, current_price)
            
            # Display market information
            display_market_info(bot, df, current_price)
            
            # Display simulation information
            display_simulation_info(bot, current_price)
            
            # Display performance report
            display_performance_report(bot, current_price, interval, start_time)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        last_iteration_time = execution_time
        
        # Wait for the next check (adjusting for execution time)
        sleep_time = max(0.1, interval - execution_time)
        time.sleep(sleep_time)