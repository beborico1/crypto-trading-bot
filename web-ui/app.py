
#!/usr/bin/env python3
"""
Web UI for High Frequency Crypto Trading Bot
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import os
import json
import time
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly
from trading.bot import CryptoTradingBot
import config
from trading.dashboard.dashboard_main import generate_dashboard, generate_combined_dashboard
from utils.terminal_colors import print_success, print_error, print_warning, print_info, print_header

# Initialize Flask app
app = Flask(__name__)

# Global variables to store active bots and their states
active_bots = {}
bot_threads = {}
bot_statuses = {}
simulation_data = {}

def load_simulation_data():
    """Load simulation data for all symbols in the data directory"""
    global simulation_data
    simulation_data = {}
    
    try:
        # Check if data directory exists
        if not os.path.exists(config.DATA_DIR):
            os.makedirs(config.DATA_DIR, exist_ok=True)
            return
        
        # Find all symbol directories
        symbol_dirs = [d for d in os.listdir(config.DATA_DIR) 
                     if os.path.isdir(os.path.join(config.DATA_DIR, d)) and d != 'dashboard' and d != 'combined_dashboard']
        
        print_info(f"Found {len(symbol_dirs)} symbol directories: {symbol_dirs}")
        
        for symbol_dir in symbol_dirs:
            symbol = symbol_dir.replace('_', '/')
            # Ensure the symbol is properly formatted (no leading/trailing spaces)
            symbol = symbol.strip()
            
            data_file = os.path.join(config.DATA_DIR, symbol_dir, 'simulation_data.json')
            
            if os.path.exists(data_file):
                print_info(f"Loading simulation data for {symbol} from {data_file}")
                
                with open(data_file, 'r') as f:
                    data = json.load(f)
                
                # Store the data
                simulation_data[symbol] = data
                
                # Calculate performance metrics
                if 'balance_history' in data and len(data['balance_history']) > 1:
                    initial_value = data['balance_history'][0]['total_value_in_quote']
                    current_value = data['balance_history'][-1]['total_value_in_quote']
                    performance = ((current_value / initial_value) - 1) * 100
                    
                    # Store performance metrics
                    simulation_data[symbol]['performance'] = {
                        'initial_value': initial_value,
                        'current_value': current_value,
                        'absolute_return': current_value - initial_value,
                        'percent_return': performance,
                        'trades': len(data.get('transactions', [])),
                        'buy_trades': sum(1 for t in data.get('transactions', []) if t.get('action') == 'buy'),
                        'sell_trades': sum(1 for t in data.get('transactions', []) if t.get('action') == 'sell')
                    }
                    
                    print_info(f"Performance metrics calculated for {symbol}: {performance:.2f}%")
            else:
                print_warning(f"No simulation data file found for {symbol} at path: {data_file}")
        
        print_info(f"Loaded simulation data for {len(simulation_data)} symbols: {list(simulation_data.keys())}")
    except Exception as e:
        print_error(f"Error loading simulation data: {e}")
        import traceback
        traceback.print_exc()
        
def bot_thread_function(bot, interval, symbol):
    """Function to run a bot in a separate thread"""
    global bot_statuses
    
    bot_statuses[symbol] = {
        'status': 'running',
        'last_update': datetime.now().isoformat(),
        'symbol': symbol,
        'price': 0.0,
        'position_size': 0.0,
        'error': None
    }
    
    try:
        while bot_statuses[symbol]['status'] == 'running':
            # Fetch the latest market data
            df = bot.analyze_market(limit=30)
            
            if df is not None and len(df) > 0:
                # Get the current price
                current_price = df.iloc[-1]['close']
                
                # Update bot status
                bot_statuses[symbol]['price'] = current_price
                bot_statuses[symbol]['position_size'] = bot.current_position_size
                bot_statuses[symbol]['last_update'] = datetime.now().isoformat()
                
                # Process trading signals
                from trading.execution.trade_execution import process_signals
                symbol_prefix = f"[{symbol}] "
                process_signals(bot, df, current_price, symbol_prefix)
                
                # Update simulation tracker with current price
                if bot.in_simulation_mode and bot.sim_tracker:
                    bot.sim_tracker.update_price(current_price)
            
            # Sleep until next check
            time.sleep(interval)
    
    except Exception as e:
        print_error(f"Error in bot thread for {symbol}: {e}")
        bot_statuses[symbol]['status'] = 'error'
        bot_statuses[symbol]['error'] = str(e)
        import traceback
        traceback.print_exc()

@app.route('/')
def index():
    """Main dashboard page"""
    global active_bots, bot_statuses, simulation_data
    
    # Reload simulation data
    load_simulation_data()
    
    return render_template('index.html', 
                          active_bots=active_bots,
                          bot_statuses=bot_statuses,
                          simulation_data=simulation_data,
                          config=config)

# UPDATED: Start bot route with improved symbol handling
@app.route('/start_bot', methods=['POST'])
def start_bot():
    """Start a new bot with improved symbol handling"""
    global active_bots, bot_threads, bot_statuses
    
    try:
        # Get bot configuration from form
        symbol = request.form.get('symbol', '').strip()
        
        # Handle custom symbol if provided
        if symbol == 'custom':
            symbol = request.form.get('custom_symbol', '').strip()
        
        print_info(f"Starting bot with symbol: '{symbol}'")
        
        if not symbol:
            return jsonify({'success': False, 'message': 'Symbol cannot be empty'})
        
        # Validate symbol format (should contain a forward slash)
        if '/' not in symbol:
            return jsonify({'success': False, 'message': 'Invalid symbol format. Use BASE/QUOTE format (e.g., BTC/USDT)'})
        
        timeframe = request.form.get('timeframe', config.DEFAULT_TIMEFRAME)
        
        # Map unsupported timeframes to supported ones
        api_timeframe = timeframe
        if timeframe in ['30s', '10s', '5s']:
            print_info(f"Note: Using 1m candles for API compatibility with check interval of {config.CHECK_INTERVAL}s")
            api_timeframe = '1m'
        
        # Check if bot already exists
        if symbol in active_bots:
            return jsonify({'success': False, 'message': f'Bot for {symbol} is already running'})
        
        # Create data directory for this symbol
        symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
        os.makedirs(symbol_dir, exist_ok=True)
        
        # Determine strategy flags
        strategy = request.form.get('strategy', 'high_frequency')
        use_enhanced_strategy = strategy == 'enhanced'
        use_scalping_strategy = strategy == 'scalping'
        use_standard_strategy = strategy == 'standard'
        use_high_frequency = strategy == 'high_frequency'
        
        # Initialize the bot
        bot = CryptoTradingBot(
            symbol=symbol,
            timeframe=timeframe,  # Pass original timeframe to bot
            api_key=config.API_KEY,
            base_url=config.BASE_URL,
            amount=float(request.form.get('amount', config.DEFAULT_TRADE_AMOUNT)),
            short_window=int(request.form.get('short_window', config.SHORT_WINDOW)),
            long_window=int(request.form.get('long_window', config.LONG_WINDOW)),
            simulation_mode=request.form.get('simulation_mode', 'true') == 'true',
            use_enhanced_strategy=use_enhanced_strategy,
            use_scalping_strategy=use_scalping_strategy,
            take_profit_percentage=float(request.form.get('take_profit', 0.5)),
            stop_loss_percentage=float(request.form.get('stop_loss', 0.3)),
            max_position_size=float(request.form.get('max_position_size', 15.0)),
            high_frequency_mode=use_high_frequency,
            data_dir=symbol_dir
        )
        
        # Set trade limit for high frequency mode
        if use_high_frequency:
            bot.minute_trade_limit = int(request.form.get('trade_limit', 20))
        
        # Store the bot
        active_bots[symbol] = bot
        
        # Initialize status entry
        bot_statuses[symbol] = {
            'status': 'initializing',
            'last_update': datetime.now().isoformat(),
            'symbol': symbol,
            'price': 0.0,
            'position_size': 0.0,
            'error': None
        }
        
        # Create a new thread for the bot
        interval = int(request.form.get('interval', config.CHECK_INTERVAL))
        thread = threading.Thread(
            target=bot_thread_function, 
            args=(bot, interval, symbol),
            daemon=True
        )
        thread.start()
        
        # Store the thread
        bot_threads[symbol] = thread
        
        return jsonify({'success': True, 'message': f'Bot for {symbol} started successfully'})
    
    except Exception as e:
        print_error(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error starting bot: {str(e)}'})
    
@app.route('/stop_bot/<symbol>', methods=['POST'])
def stop_bot(symbol):
    """Stop a running bot"""
    global active_bots, bot_threads, bot_statuses
    
    try:
        if symbol in active_bots:
            # Update bot status to 'stopping'
            bot_statuses[symbol]['status'] = 'stopping'
            
            # Generate final dashboard
            symbol_dir = os.path.join(config.DATA_DIR, symbol.replace('/', '_'))
            generate_dashboard(output_dir=symbol_dir)
            
            # Remove the bot from active bots
            del active_bots[symbol]
            
            # Update status to 'stopped'
            bot_statuses[symbol]['status'] = 'stopped'
            
            return jsonify({'success': True, 'message': f'Bot for {symbol} stopped successfully'})
        else:
            return jsonify({'success': False, 'message': f'No active bot found for {symbol}'})
    
    except Exception as e:
        print_error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'message': f'Error stopping bot: {str(e)}'})

@app.route('/bot_status/<symbol>')
def get_bot_status(symbol):
    """Get the status of a specific bot"""
    global bot_statuses
    
    if symbol in bot_statuses:
        return jsonify(bot_statuses[symbol])
    else:
        return jsonify({'status': 'not found', 'symbol': symbol})

@app.route('/all_bot_statuses')
def get_all_bot_statuses():
    """Get the status of all bots"""
    global bot_statuses
    
    return jsonify(bot_statuses)

@app.route('/generate_dashboards', methods=['POST'])
def generate_dashboards():
    """Generate dashboards for all bots"""
    try:
        # Generate individual dashboards
        symbol_dirs = [d for d in os.listdir(config.DATA_DIR) 
                     if os.path.isdir(os.path.join(config.DATA_DIR, d)) and d != 'dashboard' and d != 'combined_dashboard']
        
        for symbol_dir in symbol_dirs:
            full_dir = os.path.join(config.DATA_DIR, symbol_dir)
            symbol = symbol_dir.replace('_', '/')
            print_info(f"Generating dashboard for {symbol}...")
            generate_dashboard(output_dir=full_dir)
        
        # Generate combined dashboard
        generate_combined_dashboard(output_dir=config.DATA_DIR)
        
        # Reload simulation data
        load_simulation_data()
        
        return jsonify({'success': True, 'message': 'Dashboards generated successfully'})
    
    except Exception as e:
        print_error(f"Error generating dashboards: {e}")
        return jsonify({'success': False, 'message': f'Error generating dashboards: {str(e)}'})

@app.route('/performance_chart/<base>/<quote>')
def performance_chart(base, quote):
    """Generate a performance chart for a specific symbol with extensive debugging"""
    try:
        # Combine base and quote into a symbol
        symbol = f"{base}/{quote}"
        clean_symbol = symbol.strip()
        
        print_info(f"Generating performance chart for symbol: '{clean_symbol}'")
        
        if clean_symbol not in simulation_data:
            print_warning(f"No simulation data found for '{clean_symbol}'. Available symbols: {list(simulation_data.keys())}")
            return jsonify({'success': False, 'message': f'No data found for this symbol: {clean_symbol}'})
        
        # Create a performance chart using plotly
        balance_history = simulation_data[clean_symbol].get('balance_history', [])
        
        if not balance_history:
            print_warning(f"No balance history found for '{clean_symbol}'")
            return jsonify({'success': False, 'message': f'No balance history found for this symbol: {clean_symbol}'})
        
        print_info(f"Found {len(balance_history)} balance history entries for '{clean_symbol}'")
        
        # Detailed diagnostic logging
        print_info(f"First few balance entries:")
        for i, entry in enumerate(balance_history[:5]):
            print_info(f"Entry {i}: timestamp={entry.get('timestamp')}, value={entry.get('total_value_in_quote')}")
        
        # Make a copy of the data to avoid modifying the original
        data_for_chart = []
        
        # Ensure each entry has all required fields and proper format
        for entry in balance_history:
            if 'timestamp' not in entry or 'total_value_in_quote' not in entry:
                continue
                
            # Create a clean entry with just what we need for the chart
            clean_entry = {
                'timestamp': entry['timestamp'],
                'value': float(entry['total_value_in_quote']),
                'price': float(entry.get('price', 0))
            }
            data_for_chart.append(clean_entry)
            
        # Sort by timestamp to ensure proper chronological order
        data_for_chart.sort(key=lambda x: x['timestamp'])
        
        # Extract x and y values directly to ensure proper handling
        timestamps = [entry['timestamp'] for entry in data_for_chart]
        values = [entry['value'] for entry in data_for_chart]
        
        # Check if we have enough data points
        if len(timestamps) < 2:
            print_warning(f"Not enough data points for '{clean_symbol}' - need at least 2, got {len(timestamps)}")
            
            # If only one data point, duplicate it with a slightly different timestamp
            # This ensures at least a flat line will be displayed
            if len(timestamps) == 1:
                from datetime import datetime, timedelta
                # Parse the timestamp, add a minute, and convert back to ISO format
                try:
                    dt = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
                    new_dt = dt + timedelta(minutes=1)
                    timestamps.append(new_dt.isoformat())
                    values.append(values[0])
                    print_info(f"Added duplicate data point to enable chart rendering")
                except Exception as e:
                    print_error(f"Error adding duplicate point: {e}")
        
        # Create figure directly with the extracted data
        fig = go.Figure()
        
        # Add total value line trace
        fig.add_trace(go.Scatter(
            x=timestamps,  # Use timestamps directly
            y=values,      # Use values directly
            mode='lines',
            name='Total Value',
            line=dict(color='#6a3de8', width=2)
        ))
        
        # Add buy/sell markers from transactions if available
        transactions = simulation_data[clean_symbol].get('transactions', [])
        if transactions:
            print_info(f"Found {len(transactions)} transactions for '{clean_symbol}'")
            
            # Lists to hold buy and sell data points
            buy_x = []
            buy_y = []
            sell_x = []
            sell_y = []
            
            for tx in transactions:
                if 'timestamp' not in tx or 'action' not in tx:
                    continue
                    
                tx_time = tx['timestamp']
                
                # Find matching or subsequent balance entry for this transaction
                matched_value = None
                for entry in data_for_chart:
                    if entry['timestamp'] >= tx_time:
                        matched_value = entry['value']
                        break
                        
                if matched_value is None and data_for_chart:
                    # If no matching entry, use the last known value
                    matched_value = data_for_chart[-1]['value']
                
                if matched_value is not None:
                    if tx['action'] == 'buy':
                        buy_x.append(tx_time)
                        buy_y.append(matched_value)
                    elif tx['action'] == 'sell':
                        sell_x.append(tx_time)
                        sell_y.append(matched_value)
            
            # Add buy markers
            if buy_x:
                fig.add_trace(go.Scatter(
                    x=buy_x,
                    y=buy_y,
                    mode='markers',
                    name='Buy',
                    marker=dict(symbol='triangle-up', size=12, color='#38d39f')
                ))
            
            # Add sell markers
            if sell_x:
                fig.add_trace(go.Scatter(
                    x=sell_x,
                    y=sell_y,
                    mode='markers',
                    name='Sell',
                    marker=dict(symbol='triangle-down', size=12, color='#ff4b5b')
                ))
        
        # Update layout with improved styling
        fig.update_layout(
            title={
                'text': f'Performance Chart: {clean_symbol}',
                'font': {'color': '#000000'}
            },
            xaxis={
                'title': 'Time',
                'title_font': {'color': '#000000'},
                'tickfont': {'color': '#000000'},
                'gridcolor': '#f0f0f0',
                'linecolor': '#d0d0d0',
                'type': 'date',  # Explicitly set as date type
                'tickformat': '%H:%M:%S<br>%Y-%m-%d'  # Format date and time
            },
            yaxis={
                'title': 'Value (USDT)',
                'title_font': {'color': '#000000'},
                'tickfont': {'color': '#000000'},
                'gridcolor': '#f0f0f0',
                'linecolor': '#d0d0d0',
                'tickprefix': '$'
            },
            height=350,
            margin=dict(l=50, r=50, t=50, b=50),
            legend={
                'orientation': "h", 
                'yanchor': "bottom", 
                'y': 1.02, 
                'xanchor': "right", 
                'x': 1,
                'font': {'color': '#000000'}
            },
            hovermode='closest',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#000000'}
        )
        
        # Print diagnostic info about the chart being generated
        print_info(f"Chart data points: {len(timestamps)}")
        print_info(f"Value range: {min(values) if values else 'N/A'} to {max(values) if values else 'N/A'}")
        
        # Convert to JSON
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        print_info(f"Successfully generated chart for '{clean_symbol}'")
        return jsonify({'success': True, 'chart': chart_json})
    
    except Exception as e:
        print_error(f"Error generating performance chart for '{symbol}': {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error generating chart: {str(e)}'})
    
@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """Configuration page"""
    if request.method == 'POST':
        # Update configuration
        try:
            # Update settings in config module
            config.DEFAULT_SYMBOLS = request.form.get('symbols', 'BTC/USDT,ETH/USDT').split(',')
            config.DEFAULT_TIMEFRAME = request.form.get('timeframe', '30s')
            config.DEFAULT_TRADE_AMOUNT = float(request.form.get('trade_amount', 0.0001))
            config.SIMULATION_MODE = request.form.get('simulation_mode', 'true') == 'true'
            config.SHORT_WINDOW = int(request.form.get('short_window', 2))
            config.LONG_WINDOW = int(request.form.get('long_window', 5))
            config.CHECK_INTERVAL = int(request.form.get('check_interval', 2))
            
            # Save configuration to .env file
            with open('.env', 'w') as f:
                f.write(f"# API Configuration\n")
                f.write(f"API_KEY={config.API_KEY}\n\n")
                f.write(f"# Trading Configuration\n")
                f.write(f"SYMBOLS={','.join(config.DEFAULT_SYMBOLS)}\n")
                f.write(f"TIMEFRAME={config.DEFAULT_TIMEFRAME}\n")
                f.write(f"TRADE_AMOUNT={config.DEFAULT_TRADE_AMOUNT}\n\n")
                f.write(f"# Mode Configuration\n")
                f.write(f"SIMULATION_MODE={'true' if config.SIMULATION_MODE else 'false'}\n")
                f.write(f"SIMULATION_INITIAL_BALANCE={config.SIMULATION_INITIAL_BALANCE}\n\n")
                f.write(f"# Strategy Parameters\n")
                f.write(f"SHORT_WINDOW={config.SHORT_WINDOW}\n")
                f.write(f"LONG_WINDOW={config.LONG_WINDOW}\n\n")
                f.write(f"# Bot Settings\n")
                f.write(f"CHECK_INTERVAL={config.CHECK_INTERVAL}\n")
                f.write(f"GENERATE_DASHBOARD_INTERVAL=5\n\n")
                f.write(f"# Directory Settings\n")
                f.write(f"DATA_DIR={config.DATA_DIR}\n")
            
            return redirect(url_for('config_page'))
        
        except Exception as e:
            print_error(f"Error updating configuration: {e}")
            return render_template('config.html', config=config, error=str(e))
    
    return render_template('config.html', config=config)


@app.route('/debug/simulation/<base>/<quote>')
def debug_simulation_data(base, quote):
    """Debug endpoint to view raw simulation data"""
    symbol = f"{base}/{quote}".strip()
    
    if symbol not in simulation_data:
        return jsonify({
            'success': False,
            'message': f'No simulation data found for {symbol}',
            'available_symbols': list(simulation_data.keys())
        })
        
    # Get a summary of the data rather than the full dataset
    data = simulation_data[symbol]
    summary = {
        'balance_history_count': len(data.get('balance_history', [])),
        'transactions_count': len(data.get('transactions', [])),
        'balance_history_sample': data.get('balance_history', [])[:5],  # First 5 entries
        'performance': data.get('performance'),
        'timestamp_range': {
            'first': data['balance_history'][0]['timestamp'] if data.get('balance_history') else None,
            'last': data['balance_history'][-1]['timestamp'] if data.get('balance_history') else None
        }
    }
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'data_summary': summary
    })
    
@app.route('/test_connection')
def test_connection():
    """Test the connection to the exchange"""
    try:
        import ccxt
        
        exchange = ccxt.binance({
            'enableRateLimit': True
        })
        
        # Simple API call to test connection
        markets = exchange.load_markets()
        status = exchange.fetch_status()
        
        # List supported timeframes
        timeframes = list(exchange.timeframes.keys()) if hasattr(exchange, 'timeframes') else []
        
        return jsonify({
            'success': True,
            'status': status.get('status', 'unknown'),
            'markets_count': len(markets),
            'supported_timeframes': timeframes
        })
    except Exception as e:
        print_error(f"Error testing connection: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        })

# UPDATED: SimulationTracker.__init__ method (to be added to the SimulationTracker class)
def updated_simulation_tracker_init(self, initial_balance=100.0, base_currency='BTC', quote_currency='USDT', data_dir='simulation_data'):
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
    
    # Important: Set the initial timestamp to current time
    current_time = datetime.now()
    
    # Store the initial balance with current timestamp and a fixed value of 100 as baseline
    self.balance_history = [{
        'timestamp': current_time.isoformat(),
        'quote_balance': self.quote_balance,
        'base_balance': self.base_balance,
        'total_value_in_quote': self.quote_balance,
        'price': 0.0  # Initial price (will be updated)
    }]
    
    # Store the data directory
    self.data_dir = data_dir
    
    # Create simulation data directory if it doesn't exist
    os.makedirs(self.data_dir, exist_ok=True)
    
    print_simulation(f"Started with {initial_balance} {quote_currency}")

# UPDATED: SimulationTracker.update_price method (to be added to the SimulationTracker class)
def updated_update_price(self, current_price):
    """
    Update the current price and record balance without trading

    Parameters:
    current_price (float): Current price of base currency in quote currency
    """
    # Get the current timestamp
    timestamp = datetime.now()
    
    # Calculate total value in quote currency
    total_value = self.quote_balance + (self.base_balance * current_price)
    
    # Record the balance history with current timestamp and price
    self.balance_history.append({
        'timestamp': timestamp.isoformat(),
        'quote_balance': self.quote_balance,
        'base_balance': self.base_balance,
        'total_value_in_quote': total_value,
        'price': current_price
    })
    
    # Save the simulation data periodically (every 10 updates)
    if len(self.balance_history) % 10 == 0:
        self._save_data()
        
if __name__ == '__main__':
    # Load initial simulation data
    load_simulation_data()
    
    # Create a sample .env file if it doesn't exist
    if not os.path.exists('.env'):
        config.create_sample_env_file()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5222, debug=True)
