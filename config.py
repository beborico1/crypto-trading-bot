import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Exchange configuration
API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.binance.com'

# Trading parameters - Now using a list of symbols
DEFAULT_SYMBOLS = os.getenv('SYMBOLS', 'BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,BNB/USDT').split(',')
DEFAULT_TIMEFRAME = os.getenv('TIMEFRAME', '30s')  # Changed from 1m to 30s for higher frequency
DEFAULT_TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', 0.0001))

# Mode configuration
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'

# Simulation parameters
SIMULATION_INITIAL_BALANCE = float(os.getenv('SIMULATION_INITIAL_BALANCE', 100.0))

# Strategy parameters - Ultra short windows for high frequency trading
SHORT_WINDOW = int(os.getenv('SHORT_WINDOW', 2))  # Changed from 3 to 2
LONG_WINDOW = int(os.getenv('LONG_WINDOW', 5))   # Changed from 10 to 5

# Bot settings
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 2))  # Changed from 5 to 2 seconds for more frequent checks
UPDATE_DISPLAY_INTERVAL = 1  # Display update every 1 check

# Dashboard settings
GENERATE_DASHBOARD_INTERVAL = int(os.getenv('GENERATE_DASHBOARD_INTERVAL', 5))  # Generate dashboard every 5 checks

# Directory settings
DATA_DIR = os.getenv('DATA_DIR', 'simulation_data')
os.makedirs(DATA_DIR, exist_ok=True)

# Create a sample .env file if it doesn't exist
def create_sample_env_file():
    """Create a sample .env file if one doesn't exist"""
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# API Configuration
API_KEY=your_api_key_here

# Trading Configuration
SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT,BNB/USDT
TIMEFRAME=30s
TRADE_AMOUNT=0.0001

# Mode Configuration
SIMULATION_MODE=true
SIMULATION_INITIAL_BALANCE=100.0

# Strategy Parameters
SHORT_WINDOW=2
LONG_WINDOW=5

# Bot Settings
CHECK_INTERVAL=2
GENERATE_DASHBOARD_INTERVAL=5

# Directory Settings
DATA_DIR=simulation_data
""")
        print("Created sample .env file. Please edit it with your configuration.")

# Create sample .env file if it doesn't exist
if not os.path.exists('.env'):
    create_sample_env_file()