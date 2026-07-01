"""CLI entrypoint for the Binance Futures Testnet trading bot."""

import argparse
import sys
from typing import Any

from binance.exceptions import BinanceAPIException, BinanceRequestException
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from bot.client import CredentialError, create_futures_client
from bot.logging_config import log_error, setup_logging
from bot.orders import place_limit_order, place_market_order
from bot.validators import OrderArgs, ValidationError, validate_order_args

logger = setup_logging()

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet.",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="Order side: BUY or SELL")
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity (must be > 0)")
    parser.add_argument(
        "--price",
        help="Limit price (required for LIMIT orders, must be > 0)",
    )
    return parser


def print_request_summary(order_args: OrderArgs) -> None:
    """Print a summary of the order request."""
    print("\n--- Request Summary ---")
    print(f"Symbol   : {order_args['symbol']}")
    print(f"Side     : {order_args['side']}")
    print(f"Type     : {order_args['type']}")
    print(f"Quantity : {order_args['quantity']}")
    if order_args["type"] == "LIMIT":
        print(f"Price    : {order_args['price']}")


def _has_avg_price(avg_price: Any) -> bool:
    """Return True when the response includes a meaningful average price."""
    return avg_price is not None and str(avg_price) not in ("0", "0.0", "0.00", "")


def print_order_response(response: dict[str, Any]) -> None:
    """Print key fields from the Binance order response."""
    print("\n--- Order Response ---")
    print(f"orderId     : {response.get('orderId', 'N/A')}")
    print(f"status      : {response.get('status', 'N/A')}")
    print(f"executedQty : {response.get('executedQty', 'N/A')}")

    avg_price = response.get("avgPrice")
    if _has_avg_price(avg_price):
        print(f"avgPrice    : {avg_price}")


def place_order(order_args: OrderArgs) -> dict[str, Any]:
    """Create client and place the requested order."""
    client = create_futures_client()

    if order_args["type"] == "MARKET":
        return place_market_order(
            client=client,
            symbol=order_args["symbol"],
            side=order_args["side"],
            quantity=order_args["quantity"],
        )

    return place_limit_order(
        client=client,
        symbol=order_args["symbol"],
        side=order_args["side"],
        quantity=order_args["quantity"],
        price=order_args["price"],  # validated as required for LIMIT orders
    )


def _exit_code_from_system_exit(exc: SystemExit) -> int:
    """Convert argparse SystemExit into a process exit code."""
    if isinstance(exc.code, int):
        return exc.code
    return EXIT_FAILURE


def run(argv: list[str] | None = None) -> int:
    """Parse arguments, validate, place order, and return exit code."""
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return _exit_code_from_system_exit(exc)

    try:
        order_args = validate_order_args(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        log_error(logger, "Validation failed", exc)
        print(f"\nFailure: {exc}")
        return EXIT_FAILURE

    print_request_summary(order_args)

    try:
        response = place_order(order_args)
    except CredentialError as exc:
        log_error(logger, "Credential error", exc)
        print(f"\nFailure: {exc}")
        return EXIT_FAILURE
    except BinanceAPIException as exc:
        log_error(logger, "Binance API error", exc)
        print(f"\nFailure: Binance API error (code {exc.code}): {exc.message}")
        return EXIT_FAILURE
    except BinanceRequestException as exc:
        log_error(logger, "Binance request error", exc)
        print(f"\nFailure: Binance request error: {exc}")
        return EXIT_FAILURE
    except Timeout as exc:
        log_error(logger, "Request timed out", exc)
        print("\nFailure: Request timed out. Please try again.")
        return EXIT_FAILURE
    except RequestsConnectionError as exc:
        log_error(logger, "Network connection error", exc)
        print("\nFailure: Network connection error. Check your internet connection.")
        return EXIT_FAILURE
    except RequestException as exc:
        log_error(logger, "Network error", exc)
        print(f"\nFailure: Network error: {exc}")
        return EXIT_FAILURE
    except Exception as exc:
        log_error(logger, "Unexpected error", exc)
        print(f"\nFailure: Unexpected error: {exc}")
        return EXIT_FAILURE

    print_order_response(response)
    print("\nSuccess: Order placed successfully.")
    return EXIT_SUCCESS


def main() -> None:
    """Entry point for console scripts."""
    sys.exit(run())


if __name__ == "__main__":
    main()
