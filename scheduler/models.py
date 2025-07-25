"""
Data models for contract job scheduling.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class Network(str, Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"


class ContractJob(BaseModel):
    """
    Model representing a scheduled contract method call.
    
    Attributes:
        name: Human-readable name for the job
        network: Blockchain network to use
        contract_address: Address of the contract to interact with
        contract_abi_path: Path to the contract ABI JSON file
        method_name: Name of the contract method to call
        method_args: Arguments to pass to the contract method
        schedule: Schedule expression (e.g., "daily at 12:00")
        gas_limit: Maximum gas to use for the transaction
        gas_price: Optional gas price (in wei) to use, overrides default
        value: Optional amount of native currency to send with the transaction
        enabled: Whether this job is enabled
        validate_before_send: Whether to validate the transaction before sending
        retry_config: Configuration for retry attempts
    """
    name: str
    network: Network
    contract_address: str
    contract_abi_path: str
    method_name: str
    method_args: List[Any] = Field(default_factory=list)
    schedule: Optional[str] = None
    gas_limit: Optional[int] = None
    gas_price: Optional[int] = None
    value: int = 0
    enabled: bool = True
    validate_before_send: bool = True
    retry_config: Optional[Dict[str, Any]] = None
    
    @validator("contract_address")
    def validate_address(cls, v: str) -> str:
        """Validate that the contract address is properly formatted."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Contract address must be a valid Ethereum address")
        return v


class ContractJobCustomArgs(ContractJob):
    """
    Model representing a scheduled contract method call with custom argument calculation.
    
    This job type dynamically calculates method arguments by running a Python module
    from the custom/args directory before executing the contract call.
    
    Attributes:
        args_module_path: Path to the Python module that calculates arguments, relative to custom/args directory
        args_function_name: Name of the function in the module to call for argument calculation
        args_input: Optional input data to pass to the argument calculator function
    """
    args_module_path: str
    args_function_name: str = "calculate_args"
    args_input: Optional[Dict[str, Any]] = None
    
    # Override method_args to make it optional since we'll calculate them dynamically
    method_args: Optional[List[Any]] = None


class ContractJobMulti(BaseModel):
    """
    Model representing a scheduled execution of multiple contract method calls in sequence.
    
    This job type executes a list of ContractJob or ContractJobCustomArgs instances
    in the specified order. Each job can have different networks, contracts, and parameters.
    
    Attributes:
        name: Human-readable name for the multi-job
        jobs: List of contract jobs to execute in sequence
        schedule: Schedule expression (e.g., "daily at 12:00")
        enabled: Whether this multi-job is enabled
        stop_on_failure: If True, stops execution when any job fails; if False, continues with remaining jobs
        delay_between_jobs: Optional delay in seconds between job executions
        retry_config: Configuration for retry attempts (applies to the entire multi-job)
    """
    name: str
    jobs: List[Union[ContractJob, ContractJobCustomArgs]]
    schedule: str
    enabled: bool = True
    stop_on_failure: bool = True
    delay_between_jobs: Optional[float] = None
    retry_config: Optional[Dict[str, Any]] = None
    
    @validator("jobs")
    def validate_jobs_not_empty(cls, v: List[Union[ContractJob, ContractJobCustomArgs]]) -> List[Union[ContractJob, ContractJobCustomArgs]]:
        """Validate that at least one job is provided."""
        if not v:
            raise ValueError("At least one job must be provided in jobs list")
        return v


class NetworkConfig(BaseModel):
    """Configuration for a blockchain network."""
    rpc_url: str
    chain_id: Optional[int] = None
    explorer_url: Optional[str] = None


class TransactionConfig(BaseModel):
    """Configuration for transaction parameters."""
    default_gas_limit: int = 200000
    default_gas_price: Optional[int] = None
    gas_price_multiplier: float = 1.0
    max_retries: int = 3
    retry_delay: int = 30  # seconds


# Type alias for any job type
AnyJob = Union[ContractJob, ContractJobCustomArgs, ContractJobMulti] 