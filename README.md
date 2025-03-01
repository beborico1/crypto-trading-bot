# Cryptocurrency Trading Bot

A versatile automated trading bot for cryptocurrency markets featuring multiple strategies, simulation mode, and performance analytics.

![Trading Dashboard](simulation_data/dashboard/trading_dashboard.png)

## Features

- **Multiple Trading Strategies**:
  - Standard MA Crossover Strategy
  - Enhanced Strategy with RSI, MACD, and Bollinger Bands
  - Scalping Strategy for high-frequency trading
  
- **Risk Management**:
  - Automated take profit and stop loss mechanisms
  - Customizable risk parameters
  
- **Simulation Mode**:
  - Test strategies without risking real funds
  - Historical performance tracking
  
- **Comprehensive Dashboard**:
  - Portfolio value visualization
  - Trade history analysis
  - Performance metrics
  
- **Real-time Analysis**:
  - Technical indicators (RSI, MACD, Stochastic, Bollinger Bands)
  - Moving average calculations
  - Signal generation

## Requirements

- Python 3.7+
- TA-Lib
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install TA-Lib (Technical Analysis Library):
   - Windows: `pip install TA-Lib`
   - macOS: `brew install ta-lib && pip install TA-Lib`
   - Linux: `apt-get install ta-lib && pip install TA-Lib`

4. Create a `.env` file with your configuration (a sample will be generated on first run)

## Configuration

The bot is configured through environment variables in a `.env` file:

```
# API Configuration
API_KEY=your_api_key_here

# Trading Configuration
SYMBOL=BTC/USDT
TIMEFRAME=1m
TRADE_AMOUNT=0.001

# Mode Configuration
SIMULATION_MODE=true
SIMULATION_INITIAL_BALANCE=100.0

# Strategy Parameters
SHORT_WINDOW=3
LONG_WINDOW=10

# Bot Settings
CHECK_INTERVAL=15
GENERATE_DASHBOARD_INTERVAL=10

# Directory Settings
DATA_DIR=simulation_data
```

## Usage

### Basic Usage

Run the bot with default settings:

```bash
python main.py
```

### Advanced Usage

Customize bot behavior with command line arguments:

```bash
python main.py --symbol ETH/USDT --timeframe 5m --amount 0.01 --short-window 5 --long-window 15 --interval 5 --simulation
```

### Available Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--symbol` | Trading pair | BTC/USDT |
| `--timeframe` | Candle timeframe | 1m |
| `--amount` | Amount to trade | 0.001 |
| `--interval` | Check interval (seconds) | 15 |
| `--short-window` | Short MA window | 3 |
| `--long-window` | Long MA window | 10 |
| `--simulation` | Force simulation mode | false |
| `--dashboard-only` | Generate dashboard and exit | false |
| `--standard-strategy` | Use standard MA crossover | false |
| `--scalping-mode` | Use scalping strategy | false |
| `--take-profit` | Take profit percentage | 1.5 |
| `--stop-loss` | Stop loss percentage | 1.0 |

## Trading Strategies

### Standard MA Crossover
Classical moving average crossover strategy that generates signals when the short MA crosses above (buy) or below (sell) the long MA.

```bash
python main.py --standard-strategy
```

### Enhanced Strategy
Combines multiple indicators (MA crossover, RSI, MACD, Bollinger Bands) for more frequent and potentially more accurate trading signals.

```bash
python main.py
```

### Scalping Strategy
High-frequency trading strategy designed for very short-term trades with frequent entries and exits.

```bash
python main.py --scalping-mode
```

## Simulation Mode

Test strategies without risking real funds:

```bash
python main.py --simulation
```

The bot will simulate trades with an initial balance defined in your `.env` file or provided via command line arguments.

## Dashboard Generation

Generate performance dashboard from simulation data:

```bash
python main.py --dashboard-only
```

This will create visualization charts in the `simulation_data/dashboard` directory.

## Live Trading

**⚠️ Warning:** Live trading involves financial risk. Use at your own risk.

To enable live trading:
1. Set `SIMULATION_MODE=false` in your `.env` file
2. Provide a valid API key
3. Place your RSA private key in the project root as `binance_private_key.pem`

```bash
python main.py
```

## Project Structure

- `main.py`: Entry point for the application
- `config.py`: Configuration management
- `trading/`: Core trading functionality
  - `bot.py`: Main bot implementation
  - `strategies.py`: Trading strategy implementations
  - `order.py`: Order execution
  - `simulation.py`: Simulation logic
  - `dashboard.py`: Performance visualization
- `utils/`: Utility functions
  - `api_utils.py`: API interaction
  - `data_utils.py`: Data manipulation
  - `terminal_colors.py`: Terminal output formatting

## Performance Tracking

The bot tracks performance metrics including:
- Total portfolio value
- Profit/loss percentage
- Number of trades
- Win rate
- Average profit per trade
- Maximum drawdown

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Do not risk money that you are not willing to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.