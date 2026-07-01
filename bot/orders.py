"""Order placement functions for Binance Futures Testnet."""

import logging
from typing import Any

from binance.client import Client

from bot.logging_config import log_request, log_response
from bot.validators import OrderSide, OrderType

logger = logging.getLogger("trading_bot")


def _build_order_params(
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    quantity: str,
    price: str | None = None,
) -> dict[str, Any]:
    """Build the parameter dict sent to Binance."""
    params: dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"

    return params


def _place_order(client: Client, params: dict[str, Any]) -> dict[str, Any]:
    """Submit an order to Binance Futures Testnet and log the exchange."""
    log_request(logger, params)
    response = client.futures_create_order(**params)
    log_response(logger, response)
    return response


def place_market_order(
    client: Client,
    symbol: str,
    side: OrderSide,
    quantity: str,
) -> dict[str, Any]:
    """Place a MARKET order on Binance Futures Testnet."""
    params = _build_order_params(
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=quantity,
    )
    return _place_order(client, params)


def place_limit_order(
    client: Client,
    symbol: str,
    side: OrderSide,
    quantity: str,
    price: str,
) -> dict[str, Any]:
    """Place a LIMIT order on Binance Futures Testnet."""
    params = _build_order_params(
        symbol=symbol,
        side=side,
        order_type="LIMIT",
        quantity=quantity,
        price=price,
    )
    return _place_order(client, params)
