"""Input validation for trading bot CLI arguments."""

from decimal import Decimal, InvalidOperation
from typing import Literal, TypedDict, cast

OrderSide = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT"]

VALID_SIDES: frozenset[str] = frozenset({"BUY", "SELL"})
VALID_ORDER_TYPES: frozenset[str] = frozenset({"MARKET", "LIMIT"})


class ValidationError(Exception):
    """Raised when CLI arguments fail validation."""


class OrderArgs(TypedDict):
    """Normalized and validated order arguments."""

    symbol: str
    side: OrderSide
    type: OrderType
    quantity: str
    price: str | None


def _parse_positive_decimal(value: str | None, field_name: str) -> Decimal:
    """Parse a string into a positive Decimal or raise ValidationError."""
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_name} is required and must be greater than 0.")

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(
            f"Invalid {field_name.lower()} '{value}'. Must be a positive number."
        ) from exc

    if parsed <= 0:
        raise ValidationError(f"{field_name} must be greater than 0.")

    return parsed


def _format_decimal(value: Decimal) -> str:
    """Format a Decimal for the Binance API."""
    return format(value.normalize(), "f")


def validate_symbol(symbol: str | None) -> str:
    """Validate and normalize the trading symbol."""
    if symbol is None or not symbol.strip():
        raise ValidationError("Symbol must not be empty.")

    return symbol.strip().upper()


def validate_side(side: str | None) -> OrderSide:
    """Validate order side is BUY or SELL."""
    if side is None or not side.strip():
        raise ValidationError("Side is required. Allowed values: BUY, SELL.")

    normalized = side.strip().upper()
    if normalized not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Allowed values: {', '.join(sorted(VALID_SIDES))}."
        )

    return cast(OrderSide, normalized)


def validate_order_type(order_type: str | None) -> OrderType:
    """Validate order type is MARKET or LIMIT."""
    if order_type is None or not order_type.strip():
        raise ValidationError("Order type is required. Allowed values: MARKET, LIMIT.")

    normalized = order_type.strip().upper()
    if normalized not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. "
            f"Allowed values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )

    return cast(OrderType, normalized)
    """Validate quantity is a positive number."""
def validate_quantity(quantity: str | None) -> str:
    return _format_decimal(_parse_positive_decimal(quantity, "Quantity"))


def validate_price(price: str | None, order_type: OrderType) -> str | None:
    """Validate price; required and positive for LIMIT orders."""
    if order_type != "LIMIT":
        return None

    if price is None or not str(price).strip():
        raise ValidationError("Price is required for LIMIT orders.")

    return _format_decimal(_parse_positive_decimal(price, "Price"))


def validate_order_args(
    symbol: str | None,
    side: str | None,
    order_type: str | None,
    quantity: str | None,
    price: str | None,
) -> OrderArgs:
    """Validate all order arguments and return normalized values."""
    normalized_type = validate_order_type(order_type)
    normalized_price = validate_price(price, normalized_type)

    return OrderArgs(
        symbol=validate_symbol(symbol),
        side=validate_side(side),
        type=normalized_type,
        quantity=validate_quantity(quantity),
        price=normalized_price,
    )
