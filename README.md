# Crypto Trading Bot

A cryptocurrency trading bot with moving average crossover strategy and enhanced technical indicators.

## Features

- **Real-time market data** via Binance API
- **Moving Average Crossover** strategy with enhanced indicators (RSI, MACD, Bollinger Bands)
- **Simulation mode** for testing strategies without real trading
- **Colorized terminal output** for better readability
- **Performance tracking and visualization**
- **Dashboard generation** with trading metrics and charts

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install TA-Lib (Technical Analysis Library):
   - **Windows**: Download and install from [TA-Lib Windows Binary](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
   - **macOS**: `brew install ta-lib`
   - **Linux**: `sudo apt install ta-lib`

4. Create a `.env` file with your configuration (or run the bot once to generate a sample):
   ```
   # API Configuration
   API_KEY=your_api_key_here

   # Trading Configuration
   SYMBOL=BTC/USDT
   TIMEFRAME=5m
   TRADE_AMOUNT=0.001

   # Mode Configuration
   SIMULATION_MODE=true
   SIMULATION_INITIAL_BALANCE=100.0

   # Strategy Parameters
   SHORT_WINDOW=5
   LONG_WINDOW=20

   # Bot Settings
   CHECK_INTERVAL=30
   GENERATE_DASHBOARD_INTERVAL=10

   # Directory Settings
   DATA_DIR=simulation_data
   ```

## Usage

### Run in Simulation Mode (default)

```bash
python main.py
```

### Run with Custom Parameters

```bash
python main.py --symbol ETH/USDT --timeframe 15m --amount 0.01 --interval 60 --short-window 7 --long-window 25
```

### Available Command-line Options

- `--symbol`: Trading pair symbol (default: BTC/USDT)
- `--timeframe`: Candle timeframe (default: 5m)
- `--amount`: Amount to trade (default: 0.001)
- `--interval`: Check interval in seconds (default: 30)
- `--short-window`: Short moving average window (default: 5)
- `--long-window`: Long moving average window (default: 20)
- `--simulation`: Force simulation mode even if credentials exist
- `--dashboard-only`: Generate dashboard from existing simulation data and exit
- `--standard-strategy`: Use standard MA crossover strategy instead of enhanced strategy

### Generate Dashboard Only

```bash
python main.py --dashboard-only
```

## Trading Strategies

### Standard Moving Average Crossover

The bot uses a simple Moving Average Crossover strategy:
- **BUY** when the short MA crosses above the long MA
- **SELL** when the short MA crosses below the long MA

### Enhanced Strategy (Default)

The enhanced strategy includes additional technical indicators:
- **RSI** (Relative Strength Index) for overbought/oversold conditions
- **MACD** (Moving Average Convergence/Divergence) for trend strength
- **Bollinger Bands** for volatility and price extremes

## Terminal Color Scheme

The bot uses colorized terminal output for better readability:
- 🟢 **Green**: Buy signals, positive returns, success messages
- 🔴 **Red**: Sell signals, negative returns, error messages
- 🟡 **Yellow**: Warnings, simulation mode info
- 🔵 **Blue**: Informational messages, price data
- 🟣 **Magenta**: Headers and important section dividers

## Dashboard

The dashboard provides a comprehensive view of your trading performance:
- Total portfolio value over time
- Price history
- Performance percentage
- Trade distribution
- Key performance metrics (returns, drawdown, win rate)
- Daily performance chart

Generate a dashboard any time with:
```bash
python main.py --dashboard-only
```

## Safety Considerations

- Always start in simulation mode to test your strategy
- Use small trade amounts when starting with real trading
- Set up proper API key permissions (read-only for testing)
- Never share your API keys or private keys

## License

MIT License