"""
Sample job configuration for the Web3 Contract Scheduler.
"""

from scheduler.models import ContractJob, ContractJobCustomArgs, Network

# List of jobs to register with the scheduler
JOBS = [
    # Mint CZUSD for CL8Y Token Burning and LP every 12 hours
    ContractJob(
        name="Mint CZUSD for CL8Y Token Burning and LP",
        network=Network.BSC,
        contract_address="0x587bb405E571755d32AFC9396918FC4F49489482",
        contract_abi_path="abis/MintCZUSDToAddress.json",
        method_name="mint",
        method_args=[
            # recipient address
            "0x7DB1c089074CCe43fAE87Fa28D1Fef79558918d2"
        ],
        schedule="every 10 to 14 hours",
        gas_limit=120000,
        enabled=True,
    ),
    
    # Random swap job using custom argument calculator
    ContractJobCustomArgs(
        name="Random CL8Y Swap to Burn And LP",
        network=Network.BSC,
        contract_address="0x7DB1c089074CCe43fAE87Fa28D1Fef79558918d2",  # TokenBurningAndLP contract
        contract_abi_path="abis/TokenBurningAndLP.json",
        method_name="swapBaseTokenForSubjectToken",
        # Updated to use random interval scheduling
        schedule="every 4 to 8 hours",
        args_module_path="token_burning_swap",
        args_input={
            # Address of the token burning contract which holds the base tokens
            "token_burning_address": "0x7DB1c089074CCe43fAE87Fa28D1Fef79558918d2",
            # Address of the base token contract
            "base_token_address": "0xE68b79e51bf826534Ff37AA9CeE71a3842ee9c70",
            # Random range for swap amount (before applying decimals)
            "rand_min": 58,
            "rand_max": 212,
            # Token decimals (default is 18 if not specified)
            "decimals": 18,
            # Network for web3 provider (defaults to BSC if not specified)
            "network": Network.BSC
        },
        gas_limit=350000,
        enabled=True,
        # Validate transaction would succeed before sending
        validate_before_send=True,
        # Retry configuration
        retry_config={
            "max_retries": 3,
            "retry_delay": 60  # seconds
        }
    ),
    
    # GemBurnerV3 weekly performUpkeep job
    ContractJob(
        name="GemBurnerV3 Weekly Upkeep",
        network=Network.BSC,
        contract_address="0xe7aB4C46491D2ecc5a7c5D9d341342B8FAc6e81F",
        contract_abi_path="abis/GemBurnerV3.json",
        method_name="performUpkeep",
        method_args=["0x"],  # Empty bytes parameter
        schedule="every saturday at 00:00",
        gas_limit=250000,
        enabled=True,
        validate_before_send=True,
        retry_config={
            "max_retries": 3,
            "retry_delay": 60  # seconds
        }
    ),
] 
