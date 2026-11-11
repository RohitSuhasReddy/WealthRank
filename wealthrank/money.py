"""Indian-style money fields with visible commas and lossless parsing."""
import re
from decimal import Decimal, InvalidOperation


_INDIA = re.compile(r"^\d{1,3}(?:,\d{2})*,\d{3}(?:\.\d{1,4})?$")
_WEST = re.compile(r"^\d{1,3}(?:,\d{3})+(?:\.\d{1,4})?$")
_PLAIN = re.compile(r"^\d+(?:\.\d{1,4})?$")


def parse_inr(value: str) -> float:
    """Accept INR 25,00,000, 2,500,000 or 2500000; reject malformed groupings."""
    clean = str(value).strip().replace("₹", "").strip()
    if not clean or not any(regex.fullmatch(clean) for regex in (_INDIA, _WEST, _PLAIN)):
        raise ValueError("Enter an amount like 25,00,000, 2,500,000 or 2500000.")
    try:
        number = Decimal(clean.replace(",", ""))
    except InvalidOperation as exc:
        raise ValueError("Enter a valid rupee amount.") from exc
    if not number.is_finite() or number < 0 or number > Decimal("5000000000"):
        raise ValueError("Amount must be between ₹0 and ₹5,00,00,00,000.")
    return float(number)


def format_inr(amount: float, decimals: bool = False) -> str:
    """Display values as 25,00,000 (or 25,00,000.50)."""
    number = Decimal(str(amount))
    if not number.is_finite():
        raise ValueError("Cannot format a non-finite money amount.")
    sign = "-" if number < 0 else ""
    precision = 4 if decimals and number != number.quantize(Decimal("0.01")) else 2
    text = f"{abs(number):.{precision}f}" if decimals else f"{abs(number):.0f}"
    integer, _, fraction = text.partition(".")
    if len(integer) > 3:
        tail, head = integer[-3:], integer[:-3]
        pairs = []
        while len(head) > 2:
            pairs.append(head[-2:])
            head = head[:-2]
        if head:
            pairs.append(head)
        integer = ",".join(reversed(pairs)) + "," + tail
    return sign + integer + ("." + fraction if decimals else "")


def parse_signed_inr(value: str) -> float:
    """Signed net worth is allowed; positive asset/debt entry uses parse_inr."""
    cleaned = str(value).strip()
    if cleaned.startswith("-"):
        return -parse_inr(cleaned[1:].strip())
    return parse_inr(cleaned)
