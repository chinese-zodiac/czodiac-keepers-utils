"""
Token burning swap argument calculator.

This module calculates arguments for the TokenBurningAndLP.swapBaseTokenForSubjectToken
method based on random amounts and balance checks.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.exceptions import ContractLogicError

from . import ArgumentCalculator


class TokenBurningSwapCalculator(ArgumentCalculator):
    """
    Calculator for TokenBurningAndLP.swapBaseTokenForSubjectToken arguments.
    
    This calculator generates a random amount for swapping base tokens,
    checks if the amount is less than the available balance, and returns
    appropriate swap parameters.
    """
    
    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Calculate arguments for swapBaseTokenForSubjectToken.
        
        Args:
            input_data: Configuration data with required parameters:
                - token_burning_address: Address of the TokenBurning contract
                - base_token_address: Address of the base token contract
                - rand_min: Minimum amount to swap (before decimals adjustment)
                - rand_max: Maximum amount to swap (before decimals adjustment)
                - decimals: Number of decimals for the token (default: 18)
                - rpc_url: Optional RPC URL for blockchain queries (uses config value if not provided)
                
        Returns:
            List containing [_amount, _minAmountOut] parameters for the swap method
            
        Raises:
            ValueError: If the balance is too low or required parameters are missing
        """
        logger = logging.getLogger(__name__)
        
        # Validate input data
        if not input_data:
            raise ValueError("Input data is required for token burning swap calculator")
        
        # Extract required parameters
        token_burning_address = input_data.get("token_burning_address")
        base_token_address = input_data.get("base_token_address")
        rand_min = input_data.get("rand_min", 1)
        rand_max = input_data.get("rand_max", 100)
        decimals = input_data.get("decimals", 18)
        rpc_url = input_data.get("rpc_url")
        
        # Validate required parameters
        if not token_burning_address or not base_token_address:
            raise ValueError("token_burning_address and base_token_address are required")
        
        try:
            # Get Web3 provider - Use the network from the job input data if rpc_url is not provided
            web3 = None
            if rpc_url:
                web3 = Web3(Web3.HTTPProvider(rpc_url))
                if not web3.is_connected():
                    logger.warning(f"Could not connect to provided RPC URL: {rpc_url}")
                    web3 = None
            
            # If we don't have a connected web3 instance, try to use the network from the job
            if web3 is None:
                from scheduler.utils.web3_utils import get_web3_provider
                from scheduler.models import Network
                
                # Default to BSC network if not specified
                network = input_data.get("network", Network.BSC)
                logger.info(f"Using default network provider for: {network}")
                web3 = get_web3_provider(network)
            
            # Load ERC20 ABI (minimal for balance checking)
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            # Create contract instances
            base_token = web3.eth.contract(address=base_token_address, abi=erc20_abi)
            
            # Check base token balance of TokenBurning contract
            balance = base_token.functions.balanceOf(token_burning_address).call()
            logger.info(f"Base token balance of TokenBurning contract: {balance / (10**decimals)}")
            
            # Generate random amount (not adjusted for decimals yet)
            raw_amount = random.randint(rand_min, rand_max)
            logger.info(f"Generated random raw amount: {raw_amount}")
            
            # Convert to token amount with decimals
            amount = raw_amount * (10**decimals)
            
            # Check if amount is less than balance
            if amount > balance:
                logger.warning(
                    f"Random amount {raw_amount} exceeds balance "
                    f"{balance / (10**decimals)} - canceling job"
                )
                raise ValueError(
                    f"Random amount {raw_amount} exceeds available balance "
                    f"{balance / (10**decimals)}"
                )
            
            # Set parameters for the swap method
            swap_amount = amount
            min_amount_out = 0  # As per requirement
            
            logger.info(f"Swap parameters: amount={swap_amount}, minAmountOut={min_amount_out}")
            
            # Return parameters for swapBaseTokenForSubjectToken method
            return [swap_amount, min_amount_out]
            
        except (ContractLogicError, ConnectionError) as e:
            logger.error(f"Error querying blockchain: {str(e)}")
            raise ValueError(f"Failed to check token balance: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in token burning swap calculator: {str(e)}")
            raise


# Create instance of the calculator for direct import
calculator = TokenBurningSwapCalculator()


# Function to match the expected interface in ContractJobCustomArgs
def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    """
    Calculate arguments using the TokenBurningSwapCalculator.
    
    Args:
        input_data: Configuration data
        
    Returns:
        List of calculated arguments
        
    Raises:
        ValueError: If the balance is too low or required parameters are missing
    """
    return calculator.calculate_args(input_data) 