"""
Sample job configuration for the Web3 Contract Scheduler.
"""

from scheduler.models import ContractJob, ContractJobCustomArgs, ContractJobMulti, Network

# List of jobs to register with the scheduler
JOBS = [
    ContractJob(
        name="Daily Token Distribution",
        network=Network.ETHEREUM,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_abi_path="abis/token_abi.json",
        method_name="distribute",
        method_args=[100],
        schedule="every day at 12:00",
        gas_limit=200000,
    ),
    ContractJob(
        name="Hourly Update",
        network=Network.POLYGON,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_abi_path="abis/update_abi.json",
        method_name="update",
        method_args=[],
        schedule="every 1 hour",
        gas_limit=150000,
        enabled=True,
    ),
    ContractJob(
        name="Weekly Claim",
        network=Network.BSC,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_abi_path="abis/claim_abi.json",
        method_name="claimRewards",
        method_args=["0x9876543210987654321098765432109876543210"],
        schedule="every monday at 09:00",
        gas_limit=300000,
        enabled=True,
    ),
    
    # Custom argument jobs
    ContractJobCustomArgs(
        name="Dynamic Token Distribution",
        network=Network.ETHEREUM,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_abi_path="abis/token_abi.json",
        method_name="distribute",
        schedule="every day at 15:00",
        args_module_path="token_distributor",
        args_input={
            "base_amount": 200,
            "multiplier": 1.2,
            "max_amount": 500,
            "min_amount": 50
        },
        gas_limit=200000,
        enabled=True,
    ),
    ContractJobCustomArgs(
        name="Dynamic Rewards Claim",
        network=Network.BSC,
        contract_address="0x1234567890123456789012345678901234567890",
        contract_abi_path="abis/claim_abi.json",
        method_name="claimRewards",
        schedule="every tuesday at 10:00",
        args_module_path="dynamic_claimer",
        args_input={
            "candidate_addresses": [
                "0x1111111111111111111111111111111111111111",
                "0x2222222222222222222222222222222222222222",
                "0x3333333333333333333333333333333333333333"
            ],
            "selection_strategy": "random"
        },
        gas_limit=300000,
        enabled=True,
    ),
    
    # Multi-job sequence example
    ContractJobMulti(
        name="daily_token_operations",
        jobs=[
            # Job 1: Burn tokens with custom argument calculation
            ContractJobCustomArgs(
                name="burn_tokens",
                network=Network.BSC,
                contract_address="0x1234567890123456789012345678901234567890",
                contract_abi_path="abis/GemBurnerV3.json",
                method_name="burnTokens",
                schedule="",  # Not used for individual jobs in multi-job
                args_module_path="token_burning_swap",
                args_function_name="calculate_burn_args",
                gas_limit=300000,
                enabled=True
            ),
            # Job 2: Claim rewards
            ContractJob(
                name="claim_rewards",
                network=Network.BSC,
                contract_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                contract_abi_path="abis/claim_abi.json",
                method_name="claimRewards",
                method_args=[],  # No arguments needed
                schedule="",  # Not used for individual jobs in multi-job
                gas_limit=200000,
                enabled=True
            ),
            # Job 3: Swap tokens
            ContractJob(
                name="swap_tokens",
                network=Network.BSC,
                contract_address="0xfedcbafedcbafedcbafedcbafedcbafedcbafed",
                contract_abi_path="abis/TidalDexRouter.json",
                method_name="swapExactTokensForTokens",
                method_args=[
                    1000000000000000000,  # amount_in (1 token with 18 decimals)
                    0,  # amount_out_min
                    ["0x1111111111111111111111111111111111111111", "0x2222222222222222222222222222222222222222"],  # path
                    "0x9876543210987654321098765432109876543210",  # to address
                    1700000000  # deadline
                ],
                schedule="",  # Not used for individual jobs in multi-job
                gas_limit=250000,
                enabled=True
            )
        ],
        schedule="every day at 12:00",  # Schedule applies to the entire sequence
        enabled=True,
        stop_on_failure=True,  # Stop if any job fails
        delay_between_jobs=10.0,  # Wait 10 seconds between each job
        retry_config={
            "max_retries": 3,
            "retry_delay": 60
        }
    ),
] 