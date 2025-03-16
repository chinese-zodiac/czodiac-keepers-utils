"""
Configuration handling for the scheduler application.
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
from .models import Network, NetworkConfig, TransactionConfig

# Load environment variables
load_dotenv()


def get_network_config(network: Network) -> NetworkConfig:
    """
    Get the configuration for a specific network.
    
    Args:
        network: The network to get configuration for
        
    Returns:
        NetworkConfig for the specified network
        
    Raises:
        ValueError: If the network RPC URL is not configured
    """
    network_configs = {
        Network.ETHEREUM: NetworkConfig(
            rpc_url=os.getenv("ETH_RPC_URL", ""),
            chain_id=1,
            explorer_url="https://etherscan.io"
        ),
        Network.BSC: NetworkConfig(
            rpc_url=os.getenv("BSC_RPC_URL", ""),
            chain_id=56,
            explorer_url="https://bscscan.com"
        ),
        Network.POLYGON: NetworkConfig(
            rpc_url=os.getenv("POLYGON_RPC_URL", ""),
            chain_id=137,
            explorer_url="https://polygonscan.com"
        ),
        Network.ARBITRUM: NetworkConfig(
            rpc_url=os.getenv("ARBITRUM_RPC_URL", ""),
            chain_id=42161,
            explorer_url="https://arbiscan.io"
        ),
        Network.OPTIMISM: NetworkConfig(
            rpc_url=os.getenv("OPTIMISM_RPC_URL", ""),
            chain_id=10,
            explorer_url="https://optimistic.etherscan.io"
        ),
    }
    
    config = network_configs.get(network)
    if not config:
        raise ValueError(f"Unsupported network: {network}")
    
    if not config.rpc_url:
        raise ValueError(f"RPC URL for network {network} is not configured")
        
    return config


def get_transaction_config() -> TransactionConfig:
    """
    Get transaction configuration from environment variables.
    
    Returns:
        TransactionConfig with values from environment variables
    """
    return TransactionConfig(
        default_gas_limit=int(os.getenv("DEFAULT_GAS_LIMIT", "200000")),
        default_gas_price=int(os.getenv("DEFAULT_GAS_PRICE", "0")) or None,
        gas_price_multiplier=float(os.getenv("GAS_PRICE_MULTIPLIER", "1.0")),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        retry_delay=int(os.getenv("RETRY_DELAY", "30")),
    )


def get_private_key() -> str:
    """
    Get the private key from environment variables.
    
    Returns:
        Private key string
        
    Raises:
        ValueError: If the private key is not configured
    """
    private_key = os.getenv("PRIVATE_KEY", "")
    if not private_key:
        raise ValueError("Private key is not configured")
    
    # Ensure the private key has the 0x prefix
    if not private_key.startswith("0x"):
        private_key = f"0x{private_key}"
        
    return private_key


# Load all configuration on module import
TRANSACTION_CONFIG = get_transaction_config()
PRIVATE_KEY = get_private_key()


# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "simple") 