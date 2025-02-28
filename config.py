import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Exchange configuration
API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.binance.com'

# Trading parameters
DEFAULT_SYMBOL = os.getenv('SYMBOL', 'BTC/USDT')
DEFAULT_TIMEFRAME = os.getenv('TIMEFRAME', '5m')  # Changed from 1h to 5m
DEFAULT_TRADE_AMOUNT = float(os.getenv('TRADE_AMOUNT', 0.001))

# Mode configuration
SIMULATION_MODE = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'

# Simulation parameters
SIMULATION_INITIAL_BALANCE = float(os.getenv('SIMULATION_INITIAL_BALANCE', 100.0))

# Strategy parameters
SHORT_WINDOW = int(os.getenv('SHORT_WINDOW', 5))  # Changed from 10 to 5
LONG_WINDOW = int(os.getenv('LONG_WINDOW', 20))   # Changed from 50 to 20

# Bot settings
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 30))  # Changed from 60 to 30 seconds

# Dashboard settings
GENERATE_DASHBOARD_INTERVAL = int(os.getenv('GENERATE_DASHBOARD_INTERVAL', 10))  # Generate dashboard every N checks

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
""")
        print("Created sample .env file. Please edit it with your configuration.")

# Create sample .env file if it doesn't exist
if not os.path.exists('.env'):
    create_sample_env_file()