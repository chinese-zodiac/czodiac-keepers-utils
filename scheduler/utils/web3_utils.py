"""
Utility functions for Web3 interactions.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from retry import retry

from web3 import Web3
from web3.contract import Contract
from web3.types import TxParams, Wei
from web3.exceptions import ContractLogicError, TransactionNotFound

from ..models import Network, ContractJob, ContractJobCustomArgs, ContractJobMulti, AnyJob
from ..config import get_network_config, get_private_key, TRANSACTION_CONFIG

logger = logging.getLogger(__name__)


def get_web3_provider(network: Network) -> Web3:
    """
    Get a Web3 provider for the specified network.
    
    Args:
        network: The blockchain network to connect to
        
    Returns:
        Web3 provider instance
    """
    network_config = get_network_config(network)
    web3 = Web3(Web3.HTTPProvider(network_config.rpc_url))
    
    if not web3.is_connected():
        raise ConnectionError(f"Failed to connect to {network.value} network")
        
    logger.debug(f"Connected to {network.value} network: {network_config.rpc_url}")
    return web3


def load_contract_abi(abi_path: str) -> List[Dict[str, Any]]:
    """
    Load a contract ABI from a JSON file.
    
    Args:
        abi_path: Path to the ABI JSON file
        
    Returns:
        List containing the contract ABI
        
    Raises:
        FileNotFoundError: If the ABI file doesn't exist
    """
    path = Path(abi_path)
    if not path.exists():
        raise FileNotFoundError(f"Contract ABI file not found: {abi_path}")
        
    with open(path, 'r') as f:
        return json.load(f)


def get_contract_instance(
    web3: Web3,
    contract_address: str,
    contract_abi_path: str
) -> Contract:
    """
    Get a contract instance for the specified address and ABI.
    
    Args:
        web3: Web3 provider
        contract_address: Address of the contract
        contract_abi_path: Path to the contract ABI JSON file
        
    Returns:
        Contract instance
    """
    abi = load_contract_abi(contract_abi_path)
    contract = web3.eth.contract(address=contract_address, abi=abi)
    return contract


def calculate_custom_args(job: ContractJobCustomArgs) -> List[Any]:
    """
    Calculate custom arguments for a contract method call.
    
    Args:
        job: Contract job with custom argument configuration
        
    Returns:
        List of calculated arguments
        
    Raises:
        ImportError: If the calculator module cannot be imported
        AttributeError: If the calculator function is not found
    """
    try:
        # Import the calculator module
        from custom.args import import_calculator
        
        # Import the calculator module
        calculator = import_calculator(job.args_module_path)
        
        # Get the calculator function
        if not hasattr(calculator, job.args_function_name):
            raise AttributeError(
                f"Calculator function '{job.args_function_name}' not found in module '{job.args_module_path}'"
            )
            
        calculator_func = getattr(calculator, job.args_function_name)
        
        # Calculate the arguments
        args = calculator_func(job.args_input)
        
        logger.info(f"Calculated custom arguments for job '{job.name}': {args}")
        
        return args
        
    except Exception as e:
        logger.exception(f"Error calculating custom arguments: {str(e)}")
        raise


def estimate_gas(
    contract: Contract,
    method_name: str,
    args: List[Any],
    from_address: str,
    value: int = 0
) -> int:
    """
    Estimate gas for a contract method call.
    
    Args:
        contract: Contract instance
        method_name: Name of the method to call
        args: Arguments for the method
        from_address: Address sending the transaction
        value: Amount of native currency to send with the transaction
        
    Returns:
        Estimated gas amount
        
    Raises:
        ContractLogicError: If the gas estimation fails due to contract logic
    """
    method = getattr(contract.functions, method_name)
    try:
        gas_estimate = method(*args).estimate_gas({
            'from': from_address,
            'value': value
        })
        # Add a buffer for safety
        return int(gas_estimate * 1.2)
    except ContractLogicError as e:
        logger.error(f"Gas estimation failed: {e}")
        raise


def get_transaction_params(
    web3: Web3,
    from_address: str,
    to_address: str,
    gas_limit: Optional[int] = None,
    gas_price: Optional[int] = None,
    value: int = 0,
    data: str = "0x"
) -> TxParams:
    """
    Build transaction parameters.
    
    Args:
        web3: Web3 provider
        from_address: Sender address
        to_address: Recipient address
        gas_limit: Gas limit for the transaction
        gas_price: Gas price for the transaction
        value: Amount of native currency to send
        data: Transaction data
        
    Returns:
        Transaction parameters
    """
    tx_params: TxParams = {
        'from': from_address,
        'to': to_address,
        'data': data,
        'value': value,
        'nonce': web3.eth.get_transaction_count(from_address),
    }
    
    # Set gas limit
    if gas_limit:
        tx_params['gas'] = gas_limit
    else:
        tx_params['gas'] = TRANSACTION_CONFIG.default_gas_limit
    
    # Set gas price
    if gas_price:
        tx_params['gasPrice'] = gas_price
    elif TRANSACTION_CONFIG.default_gas_price:
        tx_params['gasPrice'] = TRANSACTION_CONFIG.default_gas_price
    else:
        # Use network's gas price with multiplier
        network_gas_price = web3.eth.gas_price
        adjusted_gas_price = int(network_gas_price * TRANSACTION_CONFIG.gas_price_multiplier)
        tx_params['gasPrice'] = adjusted_gas_price
    
    return tx_params


@retry(
    (TransactionNotFound, ConnectionError),
    tries=3,
    delay=5,
    backoff=2,
    logger=logger
)
def wait_for_transaction_receipt(web3: Web3, tx_hash: str, timeout: int = 180) -> Dict[str, Any]:
    """
    Wait for a transaction receipt with retry logic.
    
    Args:
        web3: Web3 provider
        tx_hash: Transaction hash
        timeout: Maximum time to wait for receipt
        
    Returns:
        Transaction receipt
    """
    return web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)


def execute_contract_method(job: ContractJob) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Execute a contract method according to the job config.
    
    Args:
        job: Contract job configuration
        
    Returns:
        Tuple of (success, transaction hash, error message)
    """
    logger.info(f"Executing contract method '{job.method_name}' on {job.network.name}")
    
    try:
        web3 = get_web3_provider(job.network)
        account = web3.eth.account.from_key(get_private_key())
        from_address = account.address
        
        # Get contract instance
        contract = get_contract_instance(
            web3,
            job.contract_address,
            job.contract_abi_path
        )
        
        # Calculate dynamic arguments if this is a custom args job
        method_args = job.method_args
        if isinstance(job, ContractJobCustomArgs):
            try:
                method_args = calculate_custom_args(job)
            except Exception as e:
                logger.error(f"Failed to calculate custom arguments: {str(e)}")
                return False, None, f"Failed to calculate custom arguments: {str(e)}"
        
        # Build contract method
        method = getattr(contract.functions, job.method_name)
        contract_method = method(*method_args)
        
        # If validation is enabled, try to estimate gas first
        if job.validate_before_send:
            try:
                gas_estimate = contract_method.estimate_gas({
                    'from': from_address,
                    'value': job.value
                })
                logger.debug(f"Gas estimate for {job.name}: {gas_estimate}")
                # Use the estimated gas if no specific limit is provided
                gas_limit = job.gas_limit or int(gas_estimate * 1.2)
            except ContractLogicError as e:
                logger.error(f"Transaction would fail: {str(e)}")
                return False, None, f"Transaction would fail: {str(e)}"
        else:
            gas_limit = job.gas_limit or TRANSACTION_CONFIG.default_gas_limit
        
        # Build transaction params without including 'data' field
        # Use a simplified version of get_transaction_params that doesn't include data
        tx_params = {
            'from': from_address,
            'value': job.value,
            'nonce': web3.eth.get_transaction_count(from_address),
        }
        
        # Set gas limit
        if gas_limit:
            tx_params['gas'] = gas_limit
        else:
            tx_params['gas'] = TRANSACTION_CONFIG.default_gas_limit
        
        # Set gas price
        if job.gas_price:
            tx_params['gasPrice'] = job.gas_price
        elif TRANSACTION_CONFIG.default_gas_price:
            tx_params['gasPrice'] = TRANSACTION_CONFIG.default_gas_price
        else:
            # Use network's gas price with multiplier
            network_gas_price = web3.eth.gas_price
            adjusted_gas_price = int(network_gas_price * TRANSACTION_CONFIG.gas_price_multiplier)
            tx_params['gasPrice'] = adjusted_gas_price
        
        # Build the transaction
        tx = contract_method.build_transaction(tx_params)
        
        # Sign transaction
        signed_tx = account.sign_transaction(tx)
        
        # Debug logging to see the structure of the signed transaction
        logger.debug(f"Signed transaction structure: {dir(signed_tx)}")
        
        # Try different ways to access the raw transaction data
        # Different versions of Web3.py have different attribute names
        if hasattr(signed_tx, 'rawTransaction'):
            raw_tx = signed_tx.rawTransaction
        elif hasattr(signed_tx, 'raw_transaction'):
            raw_tx = signed_tx.raw_transaction
        else:
            # If we can't find the raw transaction, try converting the signed_tx to dictionary
            try:
                tx_dict = dict(signed_tx)
                if 'rawTransaction' in tx_dict:
                    raw_tx = tx_dict['rawTransaction']
                elif 'raw_transaction' in tx_dict:
                    raw_tx = tx_dict['raw_transaction']
                else:
                    raise AttributeError("Could not find raw transaction data in signed transaction")
            except:
                # Last resort: if it has a __getitem__ method, try that
                try:
                    raw_tx = signed_tx['rawTransaction']
                except:
                    try:
                        raw_tx = signed_tx['raw_transaction']
                    except:
                        raise AttributeError("Could not extract raw transaction data")
                    
        # Send transaction with the extracted raw transaction data
        tx_hash = web3.eth.send_raw_transaction(raw_tx)
        tx_hash_hex = web3.to_hex(tx_hash)
        logger.info(f"Transaction sent: {tx_hash_hex}")
        
        # Wait for receipt
        receipt = wait_for_transaction_receipt(web3, tx_hash_hex)
        
        # Check if the transaction was successful
        if receipt['status'] == 1:
            logger.info(f"Transaction successful: {tx_hash_hex}")
            return True, tx_hash_hex, None
        else:
            logger.error(f"Transaction failed: {tx_hash_hex}")
            return False, tx_hash_hex, "Transaction failed"
            
    except Exception as e:
        logger.exception(f"Error executing contract method: {str(e)}")
        return False, None, str(e)


def execute_multi_job(multi_job: ContractJobMulti) -> Tuple[bool, List[Tuple[str, bool, Optional[str], Optional[str]]], Optional[str]]:
    """
    Execute multiple contract jobs in sequence.
    
    Args:
        multi_job: Multi-job configuration containing list of jobs to execute
        
    Returns:
        Tuple of (overall_success, job_results, error_message)
        where job_results is a list of (job_name, success, tx_hash, error) for each job
    """
    logger.info(f"Executing multi-job '{multi_job.name}' with {len(multi_job.jobs)} jobs")
    
    job_results: List[Tuple[str, bool, Optional[str], Optional[str]]] = []
    overall_success = True
    
    try:
        for i, job in enumerate(multi_job.jobs):
            if not job.enabled:
                logger.info(f"Skipping disabled job: {job.name}")
                job_results.append((job.name, True, None, "Skipped - disabled"))
                continue
            
            logger.info(f"Executing job {i+1}/{len(multi_job.jobs)}: {job.name}")
            
            # Execute the individual job
            success, tx_hash, error = execute_contract_method(job)
            job_results.append((job.name, success, tx_hash, error))
            
            if not success:
                overall_success = False
                logger.error(f"Job '{job.name}' failed: {error}")
                
                if multi_job.stop_on_failure:
                    logger.warning(f"Stopping multi-job '{multi_job.name}' due to failure")
                    break
            else:
                logger.info(f"Job '{job.name}' completed successfully")
            
            # Add delay between jobs if specified
            if multi_job.delay_between_jobs and i < len(multi_job.jobs) - 1:
                logger.info(f"Waiting {multi_job.delay_between_jobs} seconds before next job...")
                time.sleep(multi_job.delay_between_jobs)
        
        if overall_success:
            logger.info(f"Multi-job '{multi_job.name}' completed successfully")
        else:
            logger.warning(f"Multi-job '{multi_job.name}' completed with some failures")
        
        return overall_success, job_results, None
        
    except Exception as e:
        logger.exception(f"Error executing multi-job '{multi_job.name}': {str(e)}")
        return False, job_results, str(e)


def execute_any_job(job: AnyJob) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Execute any type of job (single contract job or multi-job).
    
    Args:
        job: Job configuration (ContractJob, ContractJobCustomArgs, or ContractJobMulti)
        
    Returns:
        Tuple of (success, transaction hash or summary, error message)
    """
    if isinstance(job, ContractJobMulti):
        overall_success, job_results, error = execute_multi_job(job)
        
        # Create summary of results for multi-job
        if overall_success:
            successful_jobs = [result[0] for result in job_results if result[1]]
            summary = f"Multi-job completed: {len(successful_jobs)}/{len(job_results)} jobs successful"
            return True, summary, None
        else:
            failed_jobs = [result[0] for result in job_results if not result[1]]
            summary = f"Multi-job failed: {len(failed_jobs)} job(s) failed"
            return False, summary, error
    else:
        # Single contract job
        return execute_contract_method(job) 