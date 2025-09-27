"""Shared Web3 provider service with connection reuse and failover."""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from web3 import Web3

from ..config import get_network_config
from ..models import Network


logger = logging.getLogger(__name__)


class Web3ProviderService:
    """Manage shared Web3 providers per network with fallback handling."""

    def __init__(self) -> None:
        self._providers: Dict[Network, Web3] = {}
        self._locks: Dict[Network, threading.Lock] = {}
        self._active_indices: Dict[Network, int] = {}

    def get_provider(self, network: Network) -> Web3:
        """
        Retrieve a connected Web3 provider for the given network.

        If a cached provider exists and remains connected it is reused, otherwise the
        service attempts to reconnect using the configured RPC endpoints with
        automatic failover.
        """

        lock = self._locks.setdefault(network, threading.Lock())

        with lock:
            provider = self._providers.get(network)
            if provider and provider.is_connected():
                logger.debug("Reusing existing Web3 provider for %s network", network.value)
                return provider

            connected_provider = self._connect_with_failover(network)
            self._providers[network] = connected_provider
            return connected_provider

    def _connect_with_failover(self, network: Network) -> Web3:
        """Attempt to connect to the network using each configured RPC endpoint."""

        network_config = get_network_config(network)
        rpc_urls: List[str] = network_config.rpc_urls or [network_config.rpc_url]

        start_index = self._active_indices.get(network, 0) % len(rpc_urls)
        last_error: Optional[Exception] = None

        for attempt in range(len(rpc_urls)):
            index = (start_index + attempt) % len(rpc_urls)
            rpc_url = rpc_urls[index]

            provider = Web3(Web3.HTTPProvider(rpc_url))

            try:
                if provider.is_connected():
                    if attempt > 0:
                        logger.warning(
                            "Connected to fallback RPC for %s network on attempt %d/%d: %s",
                            network.value,
                            attempt + 1,
                            len(rpc_urls),
                            rpc_url,
                        )
                    else:
                        logger.debug("Connected to %s network: %s", network.value, rpc_url)

                    self._active_indices[network] = index
                    return provider

                logger.warning(
                    "RPC URL unreachable for %s network (attempt %d/%d): %s",
                    network.value,
                    attempt + 1,
                    len(rpc_urls),
                    rpc_url,
                )
            except Exception as exc:  # pragma: no cover - defensive logging
                last_error = exc
                logger.warning(
                    "Error connecting to RPC for %s network (attempt %d/%d): %s - %s",
                    network.value,
                    attempt + 1,
                    len(rpc_urls),
                    rpc_url,
                    exc,
                )

        error_message = (
            f"Failed to connect to {network.value} network after trying {len(rpc_urls)} RPC endpoint(s)"
        )
        if last_error:
            raise ConnectionError(error_message) from last_error

        raise ConnectionError(error_message)


web3_provider_service = Web3ProviderService()


