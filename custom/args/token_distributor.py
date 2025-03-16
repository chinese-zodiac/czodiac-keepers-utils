"""
Token distributor argument calculator.

This module calculates arguments for token distribution based on current blockchain state.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from web3 import Web3

from . import ArgumentCalculator


class TokenDistributorCalculator(ArgumentCalculator):
    """
    Calculator for token distribution arguments.
    
    This calculator determines the optimal amount of tokens to distribute
    based on current time, user counts, and other parameters.
    """
    
    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Calculate arguments for token distribution.
        
        Args:
            input_data: Optional configuration data with parameters:
                - base_amount: Base amount to distribute
                - multiplier: Multiplier for distribution (e.g., for weekends)
                - max_amount: Maximum amount to distribute
                - min_amount: Minimum amount to distribute
                - rpc_url: Optional RPC URL for blockchain queries
                
        Returns:
            List containing the calculated distribution amount
        """
        logger = logging.getLogger(__name__)
        
        # Default values
        base_amount = 100
        multiplier = 1.0
        max_amount = 1000
        min_amount = 10
        
        # Override with input data if provided
        if input_data:
            base_amount = input_data.get("base_amount", base_amount)
            multiplier = input_data.get("multiplier", multiplier)
            max_amount = input_data.get("max_amount", max_amount)
            min_amount = input_data.get("min_amount", min_amount)
        
        # Calculate distribution amount based on day of week
        now = datetime.now()
        
        # Apply weekend multiplier (Saturday and Sunday)
        if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            logger.info("Applying weekend multiplier")
            multiplier *= 1.5
            
        # Check if it's month end (last 3 days of month)
        if now.day >= 28 and now.day >= (now.replace(day=28) + timedelta(days=4)).day - 3:
            logger.info("Applying month-end multiplier")
            multiplier *= 1.2
            
        # Calculate final amount
        amount = int(base_amount * multiplier)
        
        # Apply min/max bounds
        amount = max(min_amount, min(amount, max_amount))
        
        logger.info(f"Calculated distribution amount: {amount}")
        
        # Return as list of arguments
        return [amount]


# Create instance of the calculator for direct import
calculator = TokenDistributorCalculator()


# Function to match the expected interface in ContractJobCustomArgs
def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    """
    Calculate arguments using the TokenDistributorCalculator.
    
    Args:
        input_data: Optional configuration data
        
    Returns:
        List of calculated arguments
    """
    return calculator.calculate_args(input_data) 