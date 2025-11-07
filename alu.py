from types import SimpleNamespace
from typing import Callable, Dict

# Modernized collection of primitive ALU operations
AluOps = SimpleNamespace(
    add=lambda a, b: a + b,
    sub=lambda a, b: a - b,
    xor=lambda a, b: a ^ b,
    bor=lambda a, b: a | b,
    band=lambda a, b: a & b,
)

# Decoder mapping from funct3 to operation implementation
FUNCT3_TO_ALU_MAP: Dict[str, Callable[[int, int], int]] = {
    "000": AluOps.add,
    "010": AluOps.add,
    "001": AluOps.add,
    "100": AluOps.xor,
    "110": AluOps.bor,
    "111": AluOps.band,
}

# Backwards-compatible exports expected by other modules
ALU_OPs = SimpleNamespace(ADD=AluOps.add, SUB=AluOps.sub, XOR=AluOps.xor, OR=AluOps.bor, AND=AluOps.band)
FUNCT3_TO_ALU: Dict[str, Callable[[int, int], int]] = FUNCT3_TO_ALU_MAP