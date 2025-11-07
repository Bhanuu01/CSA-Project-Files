from functools import partial
from typing import Optional

from constants import SYS_BIT, BIAS, UPPER_BOUND

# curry int conversion for binary strings
binary_str_to_int = partial(int, base=2)


def sign_ext(x: str, prefix: Optional[str] = None, length: int = SYS_BIT) -> str:
    """Extend x to a fixed bit width using the sign bit (or provided prefix).

    Behavior matches the original; raises if the input exceeds the target width.
    """
    if len(x) > length:
        raise ValueError("x is longer than length")
    pad = prefix or x[0]
    return pad * (length - len(x)) + x


def signed_binary_str_to_int(x: str) -> int:
    """Interpret a 32-bit two's complement string as a Python int."""
    val = binary_str_to_int(x)
    return (val - BIAS) if (val > UPPER_BOUND) else val


def signed_int_to_binary_str(x: int) -> str:
    """Encode a Python int as a 32-bit two's complement binary string.

    The truncation behavior is retained to preserve output compatibility.
    """
    if x < 0:
        x += BIAS
        return format(x, "b")[:32]
    return sign_ext(format(x, "b")[:32], prefix="0")
