from pathlib import Path
from constants import BYTE_LEN, DMEM_FILE, DMEM_RESULT_FILE, IMEM_FILE, WORD_LEN, MemSize
from misc import signed_binary_str_to_int, signed_int_to_binary_str

class InstructionMemory(object):
    """Instruction memory abstraction backed by text files.

    The concatenation order and return format must not be altered.
    """

    def __init__(self, identifier: str, io_dir: Path):
        self.mem_id = identifier
        with open(io_dir / IMEM_FILE) as fh:
            self.instruction_bytes: list[str] = [ln.replace('\n', '') for ln in fh.readlines()]

    def fetch_instruction(self, read_address: int) -> str:
        return ''.join(self.instruction_bytes[read_address:read_address + WORD_LEN])

    # Backwards compatibility with previous API
    def readInstr(self, ReadAddress: int) -> str:  # type: ignore[N802]
        return self.fetch_instruction(ReadAddress)

class DataMemory(object):
    """Byte-addressable data memory with fixed-size backing array.

    Output serialization in `outputDataMem` is kept identical.
    """

    def __init__(self, identifier: str, io_dir: Path, out_dir: Path):
        self.mem_id = identifier
        self.io_dir = io_dir
        self.out_dir = out_dir
        with open(io_dir / DMEM_FILE) as dm:
            self.data_bytes: list[str] = [ln.replace('\n', '') for ln in dm.readlines()]
        self.data_bytes.extend(['00000000'] * (MemSize - len(self.data_bytes)))

    def load_word(self, read_address: int) -> int:
        bits = ''.join(self.data_bytes[read_address:read_address + WORD_LEN])
        return signed_binary_str_to_int(bits)

    def store_word(self, address: int, write_data: int) -> None:
        word_bits = signed_int_to_binary_str(write_data)
        for i in range(WORD_LEN):
            self.data_bytes[address + i] = word_bits[BYTE_LEN * i:BYTE_LEN * (i + 1)]

    def dump_memory(self) -> None:
        res_path = self.out_dir / f'{self.mem_id}_{DMEM_RESULT_FILE}'
        with open(res_path, 'w') as rp:
            rp.writelines([str(b) + '\n' for b in self.data_bytes])

    # Backwards compatibility with previous API
    def readDataMem(self, ReadAddress: int) -> int:  # type: ignore[N802]
        return self.load_word(ReadAddress)

    def writeDataMem(self, Address: int, WriteData: int) -> None:  # type: ignore[N802]
        return self.store_word(Address, WriteData)

    def outputDataMem(self) -> None:  # type: ignore[N802]
        return self.dump_memory()

# Backwards-compatible aliases for class names
InsMem = InstructionMemory
DataMem = DataMemory