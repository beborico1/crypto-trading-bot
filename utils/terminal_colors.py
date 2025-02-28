# utils/terminal_colors.py
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# Color definitions
class Colors:
    # Text colors
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    BLACK = Fore.BLACK
    
    # Background colors
    BG_GREEN = Back.GREEN
    BG_RED = Back.RED
    BG_YELLOW = Back.YELLOW
    BG_BLUE = Back.BLUE
    
    # Text styles
    BOLD = Style.BRIGHT
    NORMAL = Style.NORMAL
    RESET = Style.RESET_ALL

# Helper functions for formatted output
def print_success(message):
    """Print a success message in green"""
    print(f"{Colors.GREEN}{Colors.BOLD}{message}{Colors.RESET}")

def print_error(message):
    """Print an error message in red"""
    print(f"{Colors.RED}{Colors.BOLD}{message}{Colors.RESET}")

def print_warning(message):
    """Print a warning message in yellow"""
    print(f"{Colors.YELLOW}{Colors.BOLD}{message}{Colors.RESET}")

def print_info(message):
    """Print an info message in blue"""
    print(f"{Colors.BLUE}{message}{Colors.RESET}")

def print_buy(message):
    """Print a buy signal message"""
    print(f"{Colors.BG_GREEN}{Colors.BLACK} BUY {Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}")

def print_sell(message):
    """Print a sell signal message"""
    print(f"{Colors.BG_RED}{Colors.BLACK} SELL {Colors.RESET} {Colors.RED}{message}{Colors.RESET}")

def print_price(message):
    """Print price information in cyan"""
    print(f"{Colors.CYAN}{message}{Colors.RESET}")

def print_header(message):
    """Print a header in magenta"""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}{message}{Colors.RESET}")

def print_simulation(message):
    """Print simulation information"""
    print(f"{Colors.YELLOW}SIMULATION: {message}{Colors.RESET}")

def format_profit(value, include_sign=True):
    """Format profit value with color (green for positive, red for negative)"""
    if value > 0:
        sign = "+" if include_sign else ""
        return f"{Colors.GREEN}{sign}{value:.2f}{Colors.RESET}"
    elif value < 0:
        return f"{Colors.RED}{value:.2f}{Colors.RESET}"
    else:
        return f"{value:.2f}"

def format_percentage(percentage, include_sign=True):
    """Format percentage with color (green for positive, red for negative)"""
    if percentage > 0:
        sign = "+" if include_sign else ""
        return f"{Colors.GREEN}{sign}{percentage:.2f}%{Colors.RESET}"
    elif percentage < 0:
        return f"{Colors.RED}{percentage:.2f}%{Colors.RESET}"
    else:
        return f"{percentage:.2f}%"