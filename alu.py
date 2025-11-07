from types import SimpleNamespace
from typing import Callable, Dict

# Collection of primitive ALU operations used by the decoder
ALU_OPs = SimpleNamespace(
    ADD=lambda a, b: a + b,
    SUB=lambda a, b: a - b,
    XOR=lambda a, b: a ^ b,
    OR=lambda a, b: a | b,
    AND=lambda a, b: a & b,
)

# Map funct3 fields to the corresponding ALU function
FUNCT3_TO_ALU: Dict[str, Callable[[int, int], int]] = {
    "000": ALU_OPs.ADD,
    "010": ALU_OPs.ADD,
    "001": ALU_OPs.ADD,
    "100": ALU_OPs.XOR,
    "110": ALU_OPs.OR,
    "111": ALU_OPs.AND,
}