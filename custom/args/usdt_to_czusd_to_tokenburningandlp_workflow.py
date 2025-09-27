"""USDT to CZUSD workflow argument calculator."""

import logging
import random
import time
from decimal import Decimal, ROUND_DOWN, getcontext
from typing import Any, Dict, List, Optional, Union

from web3 import Web3
from web3.exceptions import ContractLogicError

from scheduler.config import TRANSACTION_CONFIG, get_private_key
from scheduler.models import Network
from scheduler.utils.web3_utils import (
    get_web3_provider,
    load_contract_abi,
    wait_for_transaction_receipt,
)

from . import ArgumentCalculator


getcontext().prec = 78


class UsdtToCzusdWorkflowCalculator(ArgumentCalculator):
    """Calculate router arguments for the USDT→CZUSD→TokenBurningAndLP workflow."""

    ERC20_ABI_PATH: str = "abis/ERC20.json"

    def calculate_args(self, input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Prepare `swapExactTokensForTokens` parameters for TidalDex router.

        The calculator inspects the relayer's USDT balance, selects a batch size
        within configured bounds, applies a max slippage constraint, and directs
        the output to the TokenBurningAndLP contract.

        Args:
            input_data: Workflow configuration parameters.

        Returns:
            Arguments for `swapExactTokensForTokens`.

        Raises:
            ValueError: If required configuration is missing or execution preconditions fail.
        """

        logger = logging.getLogger(__name__)

        if not input_data:
            raise ValueError("Workflow configuration is required")

        network = _parse_network(input_data.get("network"))
        web3 = get_web3_provider(network)

        usdt_token_address = _to_checksum(web3, input_data.get("usdt_token_address"))
        czusd_token_address = _to_checksum(web3, input_data.get("czusd_token_address"))
        router_address = _to_checksum(web3, input_data.get("router_address"))
        target_address = _to_checksum(web3, input_data.get("target_address"))

        if not all([usdt_token_address, czusd_token_address, router_address, target_address]):
            raise ValueError("Token and router addresses must be provided")

        decimals = int(input_data.get("decimals", 18))
        min_swap_amount = _to_decimal(input_data.get("min_swap_amount", "50"))
        max_swap_amount = _to_decimal(input_data.get("max_swap_amount", "150"))
        slippage_percent = _to_decimal(input_data.get("max_slippage_percent", "2"))
        precision = int(input_data.get("random_precision", 2))
        deadline_seconds = int(input_data.get("deadline_seconds", 600))
        approval_amount_override = input_data.get("approval_amount")
        approval_multiplier = _to_decimal(input_data.get("approval_multiplier", "5"))

        relayer_address = _resolve_relayer_address(web3, input_data.get("relayer_address"))

        if max_swap_amount < min_swap_amount:
            raise ValueError("max_swap_amount cannot be less than min_swap_amount")

        erc20_abi = load_contract_abi(self.ERC20_ABI_PATH)
        usdt_contract = web3.eth.contract(address=usdt_token_address, abi=erc20_abi)

        balance_raw = usdt_contract.functions.balanceOf(relayer_address).call()
        balance_decimal = _wei_to_decimal(balance_raw, decimals)
        logger.info(
            "Relayer USDT balance detected: %s (decimals=%s)",
            balance_decimal,
            decimals,
        )

        if balance_decimal < min_swap_amount:
            raise ValueError(
                f"USDT balance {balance_decimal:.4f} below minimum batch size {min_swap_amount:.4f}"
            )

        max_available_decimal = min(balance_decimal, max_swap_amount)

        swap_amount_decimal = _select_swap_amount(
            minimum=min_swap_amount,
            maximum=max_available_decimal,
            precision=precision,
        )
        swap_amount_wei = _decimal_to_wei(swap_amount_decimal, decimals)

        _ensure_router_allowance(
            web3=web3,
            token_contract=usdt_contract,
            owner=relayer_address,
            spender=router_address,
            required_amount=swap_amount_wei,
            decimals=decimals,
            approval_amount_override=approval_amount_override,
            approval_multiplier=approval_multiplier,
        )

        path = [usdt_token_address, czusd_token_address]

        min_amount_out = _apply_slippage(Decimal(swap_amount_wei), slippage_percent)

        deadline = int(time.time()) + deadline_seconds

        logger.info(
            "Prepared swap arguments: amount_in=%s, min_out=%s, path=%s, deadline=%s",
            swap_amount_wei,
            min_amount_out,
            path,
            deadline,
        )

        return [swap_amount_wei, min_amount_out, path, target_address, deadline]


def calculate_args(input_data: Optional[Dict[str, Any]] = None) -> List[Any]:
    """Proxy function exposing calculator for `ContractJobCustomArgs`."""

    calculator = UsdtToCzusdWorkflowCalculator()
    return calculator.calculate_args(input_data)


def _parse_network(value: Optional[Union[str, Network]]) -> Network:
    if isinstance(value, Network):
        return value
    if isinstance(value, str):
        return Network(value)
    return Network.BSC


def _resolve_relayer_address(web3: Web3, relayer_address: Optional[str]) -> str:
    if relayer_address:
        return _to_checksum(web3, relayer_address)

    account = web3.eth.account.from_key(get_private_key())
    return account.address


def _to_decimal(value: Union[str, int, float, Decimal]) -> Decimal:
    return Decimal(str(value))


def _wei_to_decimal(amount: int, decimals: int) -> Decimal:
    scale = Decimal(10) ** decimals
    return (Decimal(amount) / scale).quantize(Decimal("1e-18"))


def _decimal_to_wei(amount: Decimal, decimals: int) -> int:
    scale = Decimal(10) ** decimals
    quantized = amount.quantize(Decimal("1e-18"), rounding=ROUND_DOWN)
    return int((quantized * scale).to_integral_value(rounding=ROUND_DOWN))


def _select_swap_amount(minimum: Decimal, maximum: Decimal, precision: int) -> Decimal:
    if maximum < minimum:
        return minimum

    scale = 10 ** precision
    min_scaled = int((minimum * scale).to_integral_value(rounding=ROUND_DOWN))
    max_scaled = int((maximum * scale).to_integral_value(rounding=ROUND_DOWN))

    if max_scaled < min_scaled:
        return minimum

    selected_scaled = random.randint(min_scaled, max_scaled)
    return Decimal(selected_scaled) / Decimal(scale)


def _apply_slippage(amount: Decimal, slippage_percent: Decimal) -> int:
    slippage_fraction = slippage_percent / Decimal(100)
    min_amount = amount * (Decimal(1) - slippage_fraction)
    if min_amount <= 0:
        raise ValueError("Slippage calculation resulted in non-positive minimum amount")
    return int(min_amount.to_integral_value(rounding=ROUND_DOWN))


def _to_checksum(web3: Web3, address: Optional[str]) -> str:
    if not address:
        return ""
    return web3.to_checksum_address(address)


def _extract_raw_transaction(signed_tx: Any) -> bytes:
    if hasattr(signed_tx, "rawTransaction"):
        return signed_tx.rawTransaction  # type: ignore[return-value]
    if hasattr(signed_tx, "raw_transaction"):
        return signed_tx.raw_transaction  # type: ignore[return-value]

    try:
        return signed_tx["rawTransaction"]  # type: ignore[index,return-value]
    except (TypeError, KeyError):
        pass

    try:
        return signed_tx["raw_transaction"]  # type: ignore[index,return-value]
    except (TypeError, KeyError):
        pass

    raise AttributeError("Could not extract raw transaction from signed transaction")


def _ensure_router_allowance(
    *,
    web3: Web3,
    token_contract,
    owner: str,
    spender: str,
    required_amount: int,
    decimals: int,
    approval_amount_override: Optional[Union[str, int, float, Decimal]],
    approval_multiplier: Decimal,
) -> int:
    logger = logging.getLogger(__name__)

    allowance = token_contract.functions.allowance(owner, spender).call()
    if allowance >= required_amount:
        logger.debug(
            "Existing allowance %s sufficient for required amount %s",
            allowance,
            required_amount,
        )
        return allowance

    logger.info(
        "Allowance %s below required amount %s; submitting approval",
        allowance,
        required_amount,
    )

    if approval_amount_override is not None:
        approval_amount_decimal = _to_decimal(approval_amount_override)
    else:
        required_decimal = _wei_to_decimal(required_amount, decimals)
        approval_amount_decimal = required_decimal * approval_multiplier
        if approval_amount_decimal < required_decimal:
            approval_amount_decimal = required_decimal

    approval_amount_wei = _decimal_to_wei(approval_amount_decimal, decimals)
    if approval_amount_wei < required_amount:
        approval_amount_wei = required_amount

    _send_approval_transaction(
        web3=web3,
        token_contract=token_contract,
        owner=owner,
        spender=spender,
        approval_amount=approval_amount_wei,
    )

    updated_allowance = token_contract.functions.allowance(owner, spender).call()
    if updated_allowance < required_amount:
        raise ValueError(
            "Allowance remains insufficient after approval; "
            f"current allowance {updated_allowance}, required {required_amount}"
        )

    logger.info(
        "Updated allowance %s for spender %s on token %s",
        updated_allowance,
        spender,
        token_contract.address,
    )
    return updated_allowance


def _send_approval_transaction(
    *,
    web3: Web3,
    token_contract,
    owner: str,
    spender: str,
    approval_amount: int,
) -> None:
    logger = logging.getLogger(__name__)

    account = web3.eth.account.from_key(get_private_key())
    if account.address.lower() != owner.lower():
        raise ValueError(
            "Relayer address does not match automation signer address; "
            "cannot submit approval transaction."
        )

    approval_func = token_contract.functions.approve(spender, approval_amount)

    try:
        gas_estimate = approval_func.estimate_gas({"from": owner})
        gas_limit = int(gas_estimate * 1.2)
    except ContractLogicError as exc:
        logger.warning("Gas estimation failed for approval: %s", exc)
        gas_limit = TRANSACTION_CONFIG.default_gas_limit

    gas_price = TRANSACTION_CONFIG.default_gas_price
    if not gas_price:
        network_gas_price = web3.eth.gas_price
        gas_price = int(network_gas_price * TRANSACTION_CONFIG.gas_price_multiplier)

    tx_params: Dict[str, Any] = {
        "from": owner,
        "nonce": web3.eth.get_transaction_count(owner),
        "gas": gas_limit,
        "gasPrice": gas_price,
        "chainId": web3.eth.chain_id,
    }

    tx = approval_func.build_transaction(tx_params)
    signed_tx = account.sign_transaction(tx)

    raw_tx = _extract_raw_transaction(signed_tx)

    tx_hash = web3.eth.send_raw_transaction(raw_tx)
    tx_hash_hex = web3.to_hex(tx_hash)
    logger.info(
        "Submitted approval transaction %s for spender %s amount %s",
        tx_hash_hex,
        spender,
        approval_amount,
    )

    receipt = wait_for_transaction_receipt(web3, tx_hash_hex)
    if receipt.get("status") != 1:
        raise ValueError(
            f"Approval transaction {tx_hash_hex} failed with status {receipt.get('status')}"
        )

    logger.info("Approval transaction %s confirmed", tx_hash_hex)

