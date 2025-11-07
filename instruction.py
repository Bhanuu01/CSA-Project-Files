from alu import FUNCT3_TO_ALU, ALU_OPs
from constants import ENDIAN_TYPES, INSTR_TYPES
from control import INSTR_TYPE_TO_CONTROL, INSTR_CONTROL_MAP
from misc import sign_ext, signed_binary_str_to_int
from typing import Optional

# Modernized mapping of opcode bits to instruction categories
OPCODE_TO_KIND = {
    "0110011": INSTR_TYPES.R,
    "0010011": INSTR_TYPES.I,
    "1101111": INSTR_TYPES.J,
    "1100011": INSTR_TYPES.B,
    "0000011": INSTR_TYPES.LOAD_I,
    "0100011": INSTR_TYPES.S,
    "1111111": INSTR_TYPES.HALT,
}


class DecodedInstruction:
    """Decoder for a 32-bit instruction represented as a bitstring.

    Attributes like `type`, `rs1`, `rd`, `imm`, and `alu_op` are populated
    during initialization via helper parsing methods. Output semantics
    must remain unchanged.
    """

    def reset(self) -> None:
        # Initialize all decoded fields
        self.opcode = None
        self.type = None
        self.control = None
        self.funct3 = None
        self.funct7 = None
        self.rs1 = None
        self.rs2 = None
        self.rd = None
        self.imm = None
        self.alu_op = None

    def __init__(self, instruction: str, endian: str = ENDIAN_TYPES.BIG):
        self.raw_instr = instruction
        self.endian = endian
        self.reset()

        # decoding pipeline
        self.parse_type()
        if self.type == INSTR_TYPES.HALT:
            return
        self.parse_control()
        self.parse_func()
        self.parse_registers()
        self.parse_imm()
        self.parse_alu()

    def parse_type(self) -> None:
        # First, identify the opcode and overall category
        self.opcode = self.slice(0, 6)
        # Prefer new map if imported, else fallback
        mapping = INSTR_CONTROL_MAP and OPCODE_TO_KIND  # type: ignore[truthy-bool]
        self.type = OPCODE_TO_KIND[self.opcode]

    def parse_control(self) -> None:
        self.control = INSTR_TYPE_TO_CONTROL[self.type]

    def parse_func(self) -> None:
        # funct3 exists for all except J-type
        if self.type != INSTR_TYPES.J:
            self.funct3 = self.slice(12, 14)
        # funct7 exists for R-type only
        if self.type == INSTR_TYPES.R:
            self.funct7 = self.slice(25, 31)

    def parse_registers(self) -> None:
        # rs1 is used by everything but J
        if self.type != INSTR_TYPES.J:
            self.rs1 = signed_binary_str_to_int(self.slice(15, 19))
        # rs2 appears for R, S, and B
        if self.type in [INSTR_TYPES.R, INSTR_TYPES.S, INSTR_TYPES.B]:
            self.rs2 = signed_binary_str_to_int(self.slice(20, 24))
        # rd is absent for S and B
        if self.type not in [INSTR_TYPES.S, INSTR_TYPES.B]:
            self.rd = signed_binary_str_to_int(self.slice(7, 11))

    def parse_imm(self) -> None:
        imm_bits = None
        if self.type in [INSTR_TYPES.I, INSTR_TYPES.LOAD_I]:
            imm_bits = self.slice(20, 31)
        elif self.type == INSTR_TYPES.J:
            imm_bits = (
                self.slice(31) + self.slice(12, 19) + self.slice(20) + self.slice(21, 30) + "0"
            )
        elif self.type == INSTR_TYPES.B:
            imm_bits = (
                self.slice(31) + self.slice(7) + self.slice(25, 30) + self.slice(8, 11) + "0"
            )
        elif self.type == INSTR_TYPES.S:
            imm_bits = self.slice(25, 31) + self.slice(7, 11)

        self.imm = signed_binary_str_to_int(sign_ext(imm_bits)) if imm_bits else None

    def parse_alu(self) -> None:
        # default: ADD when funct3 is not present, override for SUB by funct7
        if self.funct3 is not None:
            self.alu_op = FUNCT3_TO_ALU[self.funct3]
        else:
            self.alu_op = ALU_OPs.ADD
        if self.funct7 == "0100000":
            self.alu_op = ALU_OPs.SUB

    def is_beq(self) -> bool:
        return self.type == INSTR_TYPES.B and self.funct3 == "000"

    def is_bne(self) -> bool:
        return self.type == INSTR_TYPES.B and self.funct3 == "001"

    def bit_slice(self, start: int, end: Optional[int] = None) -> str:
        """Extract bit ranges honoring the configured endianness.

        Indices are inclusive. Behavior mirrors the original implementation.
        """
        end = end or start
        assert start >= 0 and end <= 31, "Invalid start or end index"

        if self.endian == ENDIAN_TYPES.BIG:
            return self.raw_instr[::-1][start : end + 1][::-1]
        elif self.endian == ENDIAN_TYPES.SMALL:
            return self.raw_instr[start : end + 1]
        else:
            raise NotImplementedError

    # Backwards-compatible method name
    def slice(self, start: int, end: Optional[int] = None) -> str:  # type: ignore[override]
        return self.bit_slice(start, end)

# Backwards-compatible alias for class and map
Instruction = DecodedInstruction
OPCODE_TO_INSTR_TYPE = OPCODE_TO_KIND
