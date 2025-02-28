import time
from datetime import datetime
from utils.api_utils import make_api_request
from utils.terminal_colors import (
    print_success, print_error, print_warning, print_info, 
    print_buy, print_sell, Colors
)

def check_balance(base_url, api_key, symbol):
    """
    Check account balance
    
    Parameters:
    base_url (str): Base URL for the API
    api_key (str): API key for authentication
    symbol (str): Trading pair (e.g., 'BTC/USDT')
    
    Returns:
    dict: Account balance
    """
    endpoint = '/api/v3/account'
    
    print_info(f"Checking account balance for {symbol}...")
    
    response = make_api_request('GET', endpoint, base_url, api_key)
    
    if response:
        balances = {asset['asset']: {
            'free': float(asset['free']),
            'locked': float(asset['locked'])
        } for asset in response['balances']}
        
        base_currency = symbol.split('/')[0]
        quote_currency = symbol.split('/')[1]
        
        base_balance = balances.get(base_currency, {'free': 0})['free']
        quote_balance = balances.get(quote_currency, {'free': 0})['free']
        
        print_success(
            f"Balance - {base_currency}: {Colors.BLUE}{base_balance}{Colors.RESET}, "
            f"{quote_currency}: {Colors.BLUE}${quote_balance:,.2f}{Colors.RESET}"
        )
        
        return balances
    
    print_error("Failed to retrieve account balance")
    return None

def execute_trade(action, base_url, api_key, symbol, amount):
    """
    Execute a buy or sell trade
    
    Parameters:
    action (str): 'buy' or 'sell'
    base_url (str): Base URL for the API
    api_key (str): API key for authentication
    symbol (str): Trading pair (e.g., 'BTC/USDT')
    amount (float): Amount to trade
    
    Returns:
    dict: Order details
    """
    endpoint = '/api/v3/order'
    
    # Convert symbol format from BTC/USDT to BTCUSDT
    formatted_symbol = symbol.replace('/', '')
    
    params = {
        'symbol': formatted_symbol,
        'side': action.upper(),
        'type': 'MARKET',
        'quantity': amount
    }
    
    # Print message based on action
    if action.upper() == 'BUY':
        print_buy(f"Executing BUY order: {amount} {symbol} at market price...")
    else:
        print_sell(f"Executing SELL order: {amount} {symbol} at market price...")
    
    response = make_api_request('POST', endpoint, base_url, api_key, params)
    
    if response:
        if action.upper() == 'BUY':
            print_success(f"BUY order executed: {amount} {symbol} at market price")
        else:
            print_success(f"SELL order executed: {amount} {symbol} at market price")
        return response
    
    print_error(f"Failed to execute {action.upper()} order")
    return None