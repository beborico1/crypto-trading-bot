"""
Terminal color utilities for console output formatting
"""

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'  # Added YELLOW (same as WARNING)
    WARNING = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'  # Alias for ENDC for compatibility

def print_header(text):
    """Print bold header text"""
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")

def print_success(text):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message in yellow"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def print_buy(text):
    """Print buy operation in green"""
    print(f"{Colors.GREEN}BUY → {text}{Colors.ENDC}")

def print_sell(text):
    """Print sell operation in red"""
    print(f"{Colors.RED}SELL ← {text}{Colors.ENDC}")

def print_signal(text, signal_type):
    """Print signal with appropriate color"""
    if signal_type.lower() == 'buy':
        print(f"{Colors.GREEN}SIGNAL ↑ {text}{Colors.ENDC}")
    elif signal_type.lower() == 'sell':
        print(f"{Colors.RED}SIGNAL ↓ {text}{Colors.ENDC}")
    else:
        print(f"{Colors.BLUE}SIGNAL - {text}{Colors.ENDC}")

def print_simulation(text):
    """Print simulation message in cyan"""
    print(f"{Colors.CYAN}SIM » {text}{Colors.ENDC}")

def print_price(price, prev_price=None):
    """Print price with color based on change"""
    # Ensure price is a float
    try:
        price = float(price)
        if prev_price is not None:
            prev_price = float(prev_price)
    except (ValueError, TypeError):
        print(f"PRICE = ${price}")
        return
        
    # Rest of the function remains the same
    if prev_price is None:
        print(f"PRICE = ${price:.2f}")
    else:
        if price > prev_price:
            print(f"{Colors.GREEN}PRICE ↑ ${price:.2f} (+{(price-prev_price):.2f}){Colors.ENDC}")
        elif price < prev_price:
            print(f"{Colors.RED}PRICE ↓ ${price:.2f} (-{(prev_price-price):.2f}){Colors.ENDC}")
        else:
            print(f"{Colors.BLUE}PRICE = ${price:.2f} (0.00){Colors.ENDC}")
            
def format_profit(value, include_sign=True):
    """Format profit value with color and sign"""
    if value > 0:
        sign = "+" if include_sign else ""
        return f"{Colors.GREEN}{sign}${value:.2f}{Colors.ENDC}"
    elif value < 0:
        return f"{Colors.RED}-${abs(value):.2f}{Colors.ENDC}"
    else:
        # Zero values - use neutral color (blue)
        sign = "+" if include_sign else ""
        return f"{Colors.BLUE}{sign}${value:.2f}{Colors.ENDC}"

def format_percentage(value, include_sign=True):
    """Format percentage value with color and sign"""
    if value > 0:
        sign = "+" if include_sign else ""
        return f"{Colors.GREEN}{sign}{value:.2f}%{Colors.ENDC}"
    elif value < 0:
        return f"{Colors.RED}{value:.2f}%{Colors.ENDC}"
    else:
        # Zero values - use neutral color (blue)
        sign = "+" if include_sign else ""
        return f"{Colors.BLUE}{sign}{value:.2f}%{Colors.ENDC}"