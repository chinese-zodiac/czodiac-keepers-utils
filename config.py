"""
Sample job configuration for the Web3 Contract Scheduler.
"""

from datetime import time

from scheduler.models import ContractJob, ContractJobCustomArgs, Network, ContractJobMulti, TimeWindow

Cl8yChartBoostV2 = ContractJob(
    name="Cl8yChartBoostV2",
    network=Network.BSC,
    contract_address="0xD7f213cf9D017FF2D130a4B34630Dcb5b8D66d85",
    contract_abi_path="abis/ChartBoostV2.json",
    method_name="run",
    method_args=[
        "0x8F452a1fdd388A45e1080992eFF051b4dd9048d2"
    ],
    schedule="every 3 to 5 hours",
    gas_limit=550000,
    enabled=True,
    validate_before_send=True,
    retry_config={
        "max_retries": 3,
        "retry_delay": 60  # seconds
    }
)


# List of jobs to register with the scheduler
JOBS = [
    Cl8yChartBoostV2,
    # Mint CZUSD for CL8Y Token Burning and LP every 12 hours
    ContractJob(
        name="Mint CZUSD for CL8Y Token Burning and LP",
        network=Network.BSC,
        contract_address="0x587bb405E571755d32AFC9396918FC4F49489482",
        contract_abi_path="abis/MintCZUSDToAddress.json",
        method_name="mint",
        method_args=[
            # recipient address
            "0x4a395302C16a13baC55f739ee95647887e48d655"
        ],
        schedule="every 5 to 7 hours",
        gas_limit=120000,
        enabled=True,
        validate_before_send=True,
        retry_config={
            "max_retries": 3,
            "retry_delay": 60  # seconds
        }
    ),

    ContractJobCustomArgs(
        name="usdt_to_czusd_to_tokenburningandlp_workflow",
        network=Network.BSC,
        contract_address="0x71aB950a0C349103967e711b931c460E9580c631",
        contract_abi_path="abis/TidalDexRouter.json",
        method_name="swapExactTokensForTokens",
        schedule="every 1 to 2 hours",
        args_module_path="usdt_to_czusd_to_tokenburningandlp_workflow",
        args_input={
            "network": Network.BSC,
            "usdt_token_address": "0x55d398326f99059fF775485246999027B3197955",
            "czusd_token_address": "0xE68b79e51bf826534Ff37AA9CeE71a3842ee9c70",
            "router_address": "0x71aB950a0C349103967e711b931c460E9580c631",
            "target_address": "0x4a395302C16a13baC55f739ee95647887e48d655",
            "min_swap_amount": "50",
            "max_swap_amount": "150",
            "max_slippage_percent": "2",
            "deadline_seconds": 600,
            "random_precision": 2,
            "decimals": 18,
        },
        gas_limit=450000,
        enabled=True,
        validate_before_send=True,
        retry_config={
            "max_retries": 3,
            "retry_delay": 60,
        },
    ),

    # Random swap job using custom argument calculator
    ContractJobMulti(
        name="BBLP_CL8Y",
        jobs=[
            Cl8yChartBoostV2,
            ContractJobCustomArgs(
                name="Conduct buy, burn, and LP",
                    network=Network.BSC,
                    contract_address="0x4a395302C16a13baC55f739ee95647887e48d655",  # TokenBurningAndLP contract
                    contract_abi_path="abis/TokenBurningAndLP.json",
                    method_name="swapBaseTokenForSubjectToken",
                args_module_path="token_burning_swap",
                args_input={
                    # Address of the token burning contract which holds the base tokens
                    "token_burning_address": "0x4a395302C16a13baC55f739ee95647887e48d655",
                    # Address of the base token contract
                    "base_token_address": "0xE68b79e51bf826534Ff37AA9CeE71a3842ee9c70",
                    # Random range for swap amount (before applying decimals)
                    "rand_min": 68,
                    "rand_max": 232,
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
            Cl8yChartBoostV2,
        ],
        schedule="every 2 to 4 hours",
        enabled=True,
        stop_on_failure=True,  # Stop if any job fails
        delay_between_jobs=5.0,  # Wait 5 seconds between each job
        retry_config={
            "max_retries": 3,
            "retry_delay": 60
        },
        allowed_time_windows=[
            TimeWindow(start=time(hour=1, minute=0), end=time(hour=12, minute=0)),
        ],
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
        gas_limit=1200000,
        enabled=True,
        validate_before_send=True,
        retry_config={
            "max_retries": 3,
            "retry_delay": 60  # seconds
        }
    ),
    
    # GemBurnPay weekly performUpkeep job
    ContractJob(
        name="GemBurnPay Weekly Upkeep",
        network=Network.BSC,
        contract_address="0x6B9b66A7E8340C4357bF68a0E2451d851e27a47F",
        contract_abi_path="abis/GemBurnPay.json",
        method_name="performUpkeep",
        method_args=["0x"],  # Empty bytes parameter
        schedule="every saturday at 01:00",
        gas_limit=500000,
        enabled=True,
        validate_before_send=True,
        retry_config={
            "max_retries": 3,
            "retry_delay": 60  # seconds
        }
    ),
] 
