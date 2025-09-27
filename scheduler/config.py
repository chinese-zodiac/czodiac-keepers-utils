"""
Configuration handling for the scheduler application.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from .models import Network, NetworkConfig, TransactionConfig

# Load environment variables
load_dotenv()


def _parse_rpc_urls(raw_value: str) -> List[str]:
    """Parse a comma-separated list of RPC URLs into a cleaned list."""
    if not raw_value:
        return []

    return [url.strip() for url in raw_value.split(",") if url.strip()]


def _build_network_kwargs(raw_value: str) -> Dict[str, Any]:
    """Build keyword arguments for NetworkConfig from environment input."""
    urls = _parse_rpc_urls(raw_value)

    if not urls:
        return {"rpc_url": "", "rpc_urls": []}

    return {"rpc_url": urls[0], "rpc_urls": urls}


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
            **_build_network_kwargs(os.getenv("ETH_RPC_URL", "")),
            chain_id=1,
            explorer_url="https://etherscan.io"
        ),
        Network.BSC: NetworkConfig(
            **_build_network_kwargs(os.getenv("BSC_RPC_URL", "")),
            chain_id=56,
            explorer_url="https://bscscan.com"
        ),
        Network.POLYGON: NetworkConfig(
            **_build_network_kwargs(os.getenv("POLYGON_RPC_URL", "")),
            chain_id=137,
            explorer_url="https://polygonscan.com"
        ),
        Network.ARBITRUM: NetworkConfig(
            **_build_network_kwargs(os.getenv("ARBITRUM_RPC_URL", "")),
            chain_id=42161,
            explorer_url="https://arbiscan.io"
        ),
        Network.OPTIMISM: NetworkConfig(
            **_build_network_kwargs(os.getenv("OPTIMISM_RPC_URL", "")),
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
        default_gas_price=int(os.getenv("DEFAULT_GAS_PRICE", "100000000")) or None,
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