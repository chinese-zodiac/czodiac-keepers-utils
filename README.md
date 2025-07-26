# Web3 Contract Scheduler

A Python-based application for scheduling calls to smart contract methods using the Schedule library.

## Features

- Declarative configuration of scheduled contract method calls
- Secure handling of private keys and configuration
- Supports multiple blockchain networks
- Detailed logging
- Retry mechanisms for failed transactions
- Dynamic argument calculation using custom Python modules

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your configuration (see `.env.example`)

## Usage

Configure your jobs in the `config.py` file and run:

```bash
python main.py
```

### Command-line Options

- `--run-once`: Run pending jobs once and exit
- `--interval SECONDS`: Set interval between scheduler runs (default: 1 second)
- `--job JOB_NAME`: Specify a specific job to run (can be used multiple times)
- `--dry-run`: Validate jobs without executing transactions

## Configuration Examples

### Standard Job

```python
# config.py
from scheduler.models import ContractJob, Network

# Regular contract jobs with fixed arguments
job = ContractJob(
    name="Daily Token Distribution",
    network=Network.ETHEREUM,
    contract_address="0x123...",
    contract_abi_path="abis/token_abi.json",
    method_name="distribute",
    method_args=[100],
    schedule="every day at 12:00",
    gas_limit=200000,
)
```

### Dynamic Arguments Job

```python
# Custom argument jobs with dynamic calculation
from scheduler.models import ContractJobCustomArgs

job = ContractJobCustomArgs(
    name="Dynamic Token Distribution",
    network=Network.ETHEREUM,
    contract_address="0x123...",
    contract_abi_path="abis/token_abi.json",
    method_name="distribute",
    schedule="every day at 15:00",
    args_module_path="token_distributor",  # Path to custom module in custom/args/
    args_input={
        "base_amount": 200,
        "multiplier": 1.2,
        "max_amount": 500,
        "min_amount": 50
    },
    gas_limit=200000,
)
```

### Multi-Job Sequences

Execute multiple contract jobs in sequence with `ContractJobMulti`. See `config.example.py` for a complete example.

```python
from scheduler.models import ContractJobMulti

multi_job = ContractJobMulti(
    name="daily_token_operations",
    jobs=[burn_job, claim_job, swap_job],  # List of ContractJob/ContractJobCustomArgs
    schedule="every day at 12:00",  # Schedule applies to the entire sequence
    enabled=True,
    stop_on_failure=True,  # Stop if any job fails
    delay_between_jobs=10.0,  # Wait 10 seconds between each job
    retry_config={"max_retries": 3, "retry_delay": 60}
)
```

#### Multi-Job Configuration Options

- `jobs`: List of `ContractJob` or `ContractJobCustomArgs` to execute in sequence
- `stop_on_failure`: If `True`, stops execution when any job fails; if `False`, continues with remaining jobs
- `delay_between_jobs`: Optional delay in seconds between job executions
- `retry_config`: Retry configuration applies to the entire multi-job sequence

#### Use Cases for Multi-Jobs

1. **Sequential Operations**: Execute related contract calls that must happen in order (e.g., approve → transfer → claim)
2. **Multi-Network Operations**: Perform the same operation across different blockchain networks
3. **Complex Workflows**: Chain together multiple smart contract interactions with error handling

## Creating Custom Argument Calculators

Place your custom argument calculator modules in the `custom/args/` directory. Each module should provide a `calculate_args` function:

```python
# custom/args/my_calculator.py
from typing import Any, Dict, List, Optional

def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    """
    Calculate arguments for a contract method call.

    Args:
        input_data: Optional input data provided by the job configuration

    Returns:
        List of arguments to pass to the contract method
    """
    # Your logic here
    return [arg1, arg2, ...]
```

## Schedule Formats

The scheduler supports several schedule formats:

- `every day at HH:MM` - Run daily at the specified time
- `every monday at HH:MM` - Run weekly on the specified day
- `every N minutes` - Run every N minutes
- `every N hours` - Run every N hours

## Environment Variables

Create a `.env` file with the following variables:

```
# Network RPC URLs
ETH_RPC_URL=https://ethereum.rpc.provider
BSC_RPC_URL=https://bsc.rpc.provider

# Private Keys (prefixed with 0x)
PRIVATE_KEY=0xYourPrivateKeyHere

# Gas settings (optional)
DEFAULT_GAS_PRICE=5000000000  # 5 gwei
GAS_PRICE_MULTIPLIER=1.1

# Other settings
LOG_LEVEL=INFO
```

## License

MIT
