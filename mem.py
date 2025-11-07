from pathlib import Path

from constants import (
    BYTE_LEN,
    DMEM_FILE,
    DMEM_RESULT_FILE,
    IMEM_FILE,
    WORD_LEN,
    MemSize,
)
from misc import signed_binary_str_to_int, signed_int_to_binary_str


class InsMem(object):
    """Instruction memory abstraction backed by text files.

    The concatenation order and return format must not be altered.
    """

    def __init__(self, name: str, ioDir: Path):
        self.id = name
        with open(ioDir / IMEM_FILE) as im:
            # strip trailing newlines while preserving raw byte strings
            self.IMem: list[str] = [ln.replace("\n", "") for ln in im.readlines()]

    def readInstr(self, ReadAddress: int) -> str:
        # read instruction memory (4 bytes)
        # return 32-bit binary string assembled from 4 consecutive lines
        return "".join(self.IMem[ReadAddress : ReadAddress + WORD_LEN])


class DataMem(object):
    """Byte-addressable data memory with fixed-size backing array.

    Output serialization in `outputDataMem` is kept identical.
    """

    def __init__(self, name: str, ioDir: Path, outDir: Path):
        self.id = name
        self.ioDir = ioDir
        self.outDir = outDir
        with open(ioDir / DMEM_FILE) as dm:
            self.DMem: list[str] = [ln.replace("\n", "") for ln in dm.readlines()]
        # pad remaining capacity with zero bytes
        self.DMem.extend(["00000000"] * (MemSize - len(self.DMem)))

    def readDataMem(self, ReadAddress: int) -> int:
        # fetch 4 bytes and interpret as signed integer
        bits = "".join(self.DMem[ReadAddress : ReadAddress + WORD_LEN])
        return signed_binary_str_to_int(bits)

    def writeDataMem(self, Address: int, WriteData: int) -> None:
        # encode signed int into 32-bit string then split into bytes
        word_bits = signed_int_to_binary_str(WriteData)
        for i in range(WORD_LEN):
            self.DMem[Address + i] = word_bits[BYTE_LEN * i : BYTE_LEN * (i + 1)]

    def outputDataMem(self) -> None:
        resPath = self.outDir / f"{self.id}_{DMEM_RESULT_FILE}"
        with open(resPath, "w") as rp:
            rp.writelines([str(b) + "\n" for b in self.DMem])
