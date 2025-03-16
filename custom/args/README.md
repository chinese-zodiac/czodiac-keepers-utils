# Custom Argument Calculators

This directory contains custom argument calculators for contract method calls. These calculators dynamically determine the arguments for contract methods at runtime, allowing for more complex logic than what can be expressed in a static job configuration.

## Available Calculators

### TokenBurningSwap Calculator

The `token_burning_swap.py` calculator is designed to handle arguments for the TokenBurningAndLP contract's `swapBaseTokenForSubjectToken` method. It:

1. Generates a random amount within a specified range
2. Checks the actual balance of base tokens in the TokenBurning contract
3. Ensures the random amount doesn't exceed the available balance
4. Returns appropriate parameters for the swap method

#### Usage Example

```python
from scheduler.models import ContractJobCustomArgs, Network

job = ContractJobCustomArgs(
    name="Random Token Swap for Burning",
    network=Network.BSC,
    contract_address="0x1234567890123456789012345678901234567890",  # TokenBurningAndLP contract
    contract_abi_path="abis/TokenBurningAndLP.json",
    method_name="swapBaseTokenForSubjectToken",
    schedule="every 6 hours",
    args_module_path="token_burning_swap",
    args_input={
        # Address of the token burning contract which holds the base tokens
        "token_burning_address": "0x1234567890123456789012345678901234567890",
        # Address of the base token contract
        "base_token_address": "0x5555555555555555555555555555555555555555",
        # Random range for swap amount (before applying decimals)
        "rand_min": 10,
        "rand_max": 100,
        # Token decimals (default is 18 if not specified)
        "decimals": 18,
        # Network for web3 provider (defaults to BSC if not specified)
        "network": Network.BSC
    },
    gas_limit=500000,
    enabled=True,
)
```

#### Input Parameters

| Parameter               | Type    | Description                                                     | Default  |
| ----------------------- | ------- | --------------------------------------------------------------- | -------- |
| `token_burning_address` | string  | Address of the TokenBurning contract that holds the base tokens | Required |
| `base_token_address`    | string  | Address of the base token contract                              | Required |
| `rand_min`              | integer | Minimum amount to swap (before decimals adjustment)             | 1        |
| `rand_max`              | integer | Maximum amount to swap (before decimals adjustment)             | 100      |
| `decimals`              | integer | Number of decimals for the token                                | 18       |
| `network`               | Network | Blockchain network for Web3 provider                            | BSC      |
| `rpc_url`               | string  | Custom RPC URL (optional, uses config if not provided)          | None     |

#### Return Values

The calculator returns a list with two values:

1. `_amount`: The randomly generated amount with decimals applied
2. `_minAmountOut`: Always set to 0 as per requirements

## Creating New Calculators

To create a new custom argument calculator:

1. Create a new Python file in this directory (e.g., `my_calculator.py`)
2. Implement the `ArgumentCalculator` abstract base class or provide a `calculate_args` function
3. Return a list of arguments that matches the contract method's expected parameters

### Calculator Template

```python
from typing import Any, Dict, List, Optional
from . import ArgumentCalculator

class MyCalculator(ArgumentCalculator):
    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        # Your logic here
        return [arg1, arg2, ...]

# Create an instance
calculator = MyCalculator()

# Standalone function that meets the expected interface
def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    return calculator.calculate_args(input_data)
```
