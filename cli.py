"""CLI entrypoint for the Binance Futures Testnet trading bot."""

import argparse
import sys
from typing import Any

from binance.exceptions import BinanceAPIException, BinanceRequestException
from colorama import Fore, Style, init
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from bot.client import CredentialError, create_futures_client
from bot.logging_config import log_error, setup_logging
from bot.orders import place_limit_order, place_market_order
from bot.validators import OrderArgs, ValidationError, validate_order_args

logger = setup_logging()
init(autoreset=True)

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet.",
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair, e.g. BTCUSDT",
    )

    parser.add_argument(
        "--side",
        required=True,
        help="Order side: BUY or SELL",
    )

    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        help="Order type: MARKET or LIMIT",
    )

    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (must be > 0)",
    )

    parser.add_argument(
        "--price",
        help="Limit price (required for LIMIT orders, must be > 0)",
    )

    return parser


def print_request_summary(order_args: OrderArgs) -> None:
    """Print a professional request summary."""

    print("\n" + "=" * 60)
    print(
        Fore.CYAN
        + Style.BRIGHT
        + "      BINANCE FUTURES TESTNET TRADING BOT"
    )
    print("=" * 60)

    print(Fore.YELLOW + Style.BRIGHT + "\nOrder Summary")
    print("-" * 60)

    print(f"Symbol      : {order_args['symbol']}")
    print(f"Side        : {order_args['side']}")
    print(f"Order Type  : {order_args['type']}")
    print(f"Quantity    : {order_args['quantity']}")

    if order_args["type"] == "LIMIT":
        print(f"Price       : {order_args['price']}")

    print("-" * 60)
    print(Fore.BLUE + "Connecting to Binance Futures Testnet...\n")


def _has_avg_price(avg_price: Any) -> bool:
    """Return True when avgPrice exists."""
    return avg_price is not None and str(avg_price) not in (
        "",
        "0",
        "0.0",
        "0.00",
    )


def print_order_response(response: dict[str, Any]) -> None:
    """Print formatted order response."""

    print(Fore.GREEN + Style.BRIGHT + "✓ Order Submitted Successfully")

    print("-" * 60)

    print(f"Order ID       : {response.get('orderId', 'N/A')}")
    print(f"Status         : {response.get('status', 'N/A')}")
    print(f"Executed Qty   : {response.get('executedQty', 'N/A')}")

    avg_price = response.get("avgPrice")

    if _has_avg_price(avg_price):
        print(f"Average Price  : {avg_price}")
    else:
        print("Average Price  : N/A")

    print("-" * 60)


def place_order(order_args: OrderArgs) -> dict[str, Any]:
    """Create client and place order."""

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
        price=order_args["price"],
    )


def _exit_code_from_system_exit(exc: SystemExit) -> int:
    """Convert argparse exit into integer."""
    if isinstance(exc.code, int):
        return exc.code
    return EXIT_FAILURE


def run(argv: list[str] | None = None) -> int:
    """Run the CLI."""

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
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Validation Error: {exc}"
        )
        return EXIT_FAILURE

    print_request_summary(order_args)

    try:
        response = place_order(order_args)

    except CredentialError as exc:
        log_error(logger, "Credential error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Credential Error: {exc}"
        )
        return EXIT_FAILURE

    except BinanceAPIException as exc:
        log_error(logger, "Binance API error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Binance API Error ({exc.code}): {exc.message}"
        )
        return EXIT_FAILURE

    except BinanceRequestException as exc:
        log_error(logger, "Binance request error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Binance Request Error: {exc}"
        )
        return EXIT_FAILURE

    except Timeout as exc:
        log_error(logger, "Timeout", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + "\n✗ Request timed out. Please try again."
        )
        return EXIT_FAILURE

    except RequestsConnectionError as exc:
        log_error(logger, "Connection error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + "\n✗ Network connection error."
        )
        return EXIT_FAILURE

    except RequestException as exc:
        log_error(logger, "Request error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Network Error: {exc}"
        )
        return EXIT_FAILURE

    except Exception as exc:
        log_error(logger, "Unexpected error", exc)
        print(
            Fore.RED
            + Style.BRIGHT
            + f"\n✗ Unexpected Error: {exc}"
        )
        return EXIT_FAILURE

    print_order_response(response)

    print(
        Fore.GREEN
        + Style.BRIGHT
        + "\n✓ SUCCESS: Order placed successfully on Binance Futures Testnet."
    )

    return EXIT_SUCCESS


def main() -> None:
    """Application entry point."""
    sys.exit(run())


if __name__ == "__main__":
    main()