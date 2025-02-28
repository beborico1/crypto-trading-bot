import time
import hmac
import hashlib
import base64
from urllib.parse import urlencode
import os
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def get_headers(api_key):
    """
    Generate headers for API requests
    
    Parameters:
    api_key (str): API key for authentication
    
    Returns:
    dict: Headers for API requests
    """
    return {
        'X-MBX-APIKEY': api_key
    }

def generate_signature(params):
    """
    Generate RSA signature for API requests
    
    Parameters:
    params (dict): Query parameters
    
    Returns:
    str: RSA signature
    """
    # Add timestamp if not present
    if 'timestamp' not in params:
        params['timestamp'] = int(time.time() * 1000)
        
    # Convert params to query string
    query_string = urlencode(params)
    
    try:
        # Read the private key file
        with open('binance_private_key.pem', 'rb') as f:
            private_key_data = f.read()
        
        # Create RSA signature
        private_key = load_pem_private_key(
            private_key_data,
            password=None,  # Add password if your key is password-protected
        )
        
        signature = private_key.sign(
            query_string.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Return base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')
    except Exception as e:
        print(f"Error generating RSA signature: {e}")
        raise

def make_api_request(method, endpoint, base_url, api_key, params=None, authenticate=True):
    """
    Make an API request to the exchange
    
    Parameters:
    method (str): HTTP method ('GET', 'POST', etc)
    endpoint (str): API endpoint
    base_url (str): Base URL for the API
    api_key (str): API key for authentication
    params (dict): Query parameters
    authenticate (bool): Whether to authenticate the request
    
    Returns:
    dict: Response from the API
    """
    if params is None:
        params = {}
    
    # Add timestamp for authenticated requests
    if authenticate:
        params['timestamp'] = int(time.time() * 1000)
        signature = generate_signature(params)
        params['signature'] = signature
    
    # Create full URL
    url = f"{base_url}{endpoint}"
    
    # Make the request
    headers = get_headers(api_key) if authenticate else {}
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Check for successful response
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error making API request: {e}")
        return Noned