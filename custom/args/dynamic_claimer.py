"""
Dynamic claimer argument calculator.

This module calculates arguments for reward claiming based on current blockchain state.
It dynamically determines which address should receive rewards based on performance.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from web3 import Web3

from . import ArgumentCalculator


class DynamicClaimerCalculator(ArgumentCalculator):
    """
    Calculator for determining which address should receive rewards.
    
    This calculator selects the most appropriate address to receive rewards
    based on performance metrics or other criteria.
    """
    
    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Calculate arguments for claim rewards.
        
        Args:
            input_data: Optional configuration data with parameters:
                - candidate_addresses: List of candidate addresses
                - rpc_url: Optional RPC URL for blockchain queries
                - contract_address: Optional address of the rewards contract
                - selection_strategy: Strategy for selecting address ("round_robin", "random", "performance")
                
        Returns:
            List containing the selected recipient address
        """
        logger = logging.getLogger(__name__)
        
        # Default values
        candidate_addresses = [
            "0x9876543210987654321098765432109876543210"
        ]
        selection_strategy = "random"
        
        # Override with input data if provided
        if input_data:
            candidate_addresses = input_data.get("candidate_addresses", candidate_addresses)
            selection_strategy = input_data.get("selection_strategy", selection_strategy)
            
        # Ensure we have at least one address
        if not candidate_addresses:
            logger.warning("No candidate addresses provided, using default")
            candidate_addresses = ["0x9876543210987654321098765432109876543210"]
            
        # Select address based on strategy
        selected_address = None
        
        if selection_strategy == "random":
            # Randomly select an address
            selected_address = random.choice(candidate_addresses)
            logger.info(f"Randomly selected address: {selected_address}")
            
        elif selection_strategy == "round_robin":
            # For round-robin, we'd need to store state between runs
            # This is simplified for demo purposes
            selected_address = candidate_addresses[0]
            logger.info(f"Selected first address (round-robin): {selected_address}")
            
        elif selection_strategy == "performance":
            # In a real implementation, this would query on-chain performance metrics
            # For demo, we'll just choose the first address
            selected_address = candidate_addresses[0]
            logger.info(f"Selected first address (performance): {selected_address}")
            
        else:
            # Default to first address for unknown strategies
            selected_address = candidate_addresses[0]
            logger.warning(f"Unknown selection strategy: {selection_strategy}, using first address")
            
        # Return as list of arguments
        return [selected_address]


# Create instance of the calculator for direct import
calculator = DynamicClaimerCalculator()


# Function to match the expected interface in ContractJobCustomArgs
def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    """
    Calculate arguments using the DynamicClaimerCalculator.
    
    Args:
        input_data: Optional configuration data
        
    Returns:
        List of calculated arguments
    """
    return calculator.calculate_args(input_data) 