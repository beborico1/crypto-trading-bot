"""
Dashboard module for high frequency trading visualization
"""

from trading.dashboard.dashboard_main import dashboard_command
from trading.dashboard.dashboard_single import generate_dashboard
from trading.dashboard.dashboard_combined import generate_combined_dashboard

__all__ = [
    'dashboard_command',
    'generate_dashboard',
    'generate_combined_dashboard'
]