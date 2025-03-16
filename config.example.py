"""
Sample job configuration for the Web3 Contract Scheduler.
"""

from scheduler.models import ContractJob, ContractJobCustomArgs, Network

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
] 