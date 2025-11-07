from copy import deepcopy
from pathlib import Path
from typing import Callable

from constants import (
    INSTR_TYPES,
    PERFORMANCE_FILE,
    RF_FILE,
    SS_STATE_RESULT_FILE,
    STAGES,
    WORD_LEN,
)

from instruction import Instruction
from mem import DataMem, InsMem
from misc import signed_int_to_binary_str
from monitors import Monitor
from state import StageManager, State


class RegisterFile(object):
    """Simple 32-entry register file.

    The serialization format in `outputRF` must remain unchanged.
    """

    def __init__(self, outPath: Path):
        self.outputFile: Path = outPath
        self.Registers: list[int] = [0x0 for _ in range(32)]

    def readRF(self, Reg_addr: int) -> int:
        return self.Registers[Reg_addr]

    def writeRF(self, Reg_addr: int, Wrt_reg_data: int) -> None:
        self.Registers[Reg_addr] = Wrt_reg_data

    def outputRF(self, cycle: int) -> None:
        # Keep content identical for grading
        lines = ["-" * 70 + "\n", f"State of RF after executing cycle: {cycle}\n"]
        lines.extend(f"{signed_int_to_binary_str(v)}\n" for v in self.Registers)
        perm = "w" if cycle == 0 else "a"
        with self.outputFile.open(perm) as fh:
            fh.writelines(lines)


class Core(object):
    """Abstract core that wires memories, RF, and monitoring."""

    def __init__(self, core_type: str, outDir: Path, imem: InsMem, dmem: DataMem):
        # Route output paths based on core flavor
        match core_type:
            case "Single Stage":
                outPath = outDir / f"SS_{RF_FILE}"
                self.opFilePath = outDir / SS_STATE_RESULT_FILE

        self.myRF = RegisterFile(outPath)
        self.monitor = Monitor(core_type, outputFile=outDir / PERFORMANCE_FILE)

        # runtime state
        self.cycle: int = 0
        self.halted: bool = False

        # pipeline snapshots
        self.state = State()
        self.nextState = State()

        # external memories
        self.ext_imem: InsMem = imem
        self.ext_dmem: DataMem = dmem

    @staticmethod
    def parse_instruction(instruction: str) -> Instruction:
        """Convert a raw 32-bit string into an `Instruction`."""
        return Instruction(instruction)


class SingleStageCore(Core):
    """Implements a single-cycle datapath using staged bookkeeping.

    Although stages are advanced conceptually, all work is resolved per step.
    """

    def __init__(self, ioDir: Path, imem: InsMem, dmem: DataMem):
        super(SingleStageCore, self).__init__("Single Stage", ioDir, imem, dmem)
        self.stage_manager = StageManager()
        self.instr_type = None  # internal tracker for current op kind

    def IF_forward(self) -> None:
        self.nextState.ID["Instr"] = self.ext_imem.readInstr(self.nextState.IF["PC"])
        self.monitor.update_instr()
        self.stage_manager.forward()

    def ID_forward(self) -> None:
        decoded = self.parse_instruction(self.nextState.ID["Instr"])
        self.nextState.EX["is_I_type"] = (decoded.type == INSTR_TYPES.I)

        # HALT short-circuits execution
        if decoded.type == INSTR_TYPES.HALT:
            self.nextState.IF["nop"] = True
            self.stage_manager.reset()
            return

        # source operand reads (if applicable)
        if decoded.rs1 is not None:
            self.nextState.EX["Read_data1"] = self.myRF.readRF(decoded.rs1)
        if decoded.rs2 is not None:
            self.nextState.EX["Read_data2"] = self.myRF.readRF(decoded.rs2)

        # destination reg and immediate fields
        if decoded.rd is not None:
            self.nextState.EX["Wrt_reg_addr"] = decoded.rd
        if decoded.imm is not None:
            self.nextState.EX["Imm"] = decoded.imm
        if decoded.alu_op is not None:
            self.nextState.EX["alu_op"] = decoded.alu_op

        # jumps and branches update PC here and end the mini-cycle
        if decoded.type == INSTR_TYPES.J:
            self.myRF.writeRF(self.nextState.EX["Wrt_reg_addr"], self.nextState.IF["PC"] + WORD_LEN)
            self.nextState.IF["PC"] += self.nextState.EX["Imm"]
            self.stage_manager.reset()
            return

        if decoded.type == INSTR_TYPES.B:
            same = (self.nextState.EX["Read_data1"] == self.nextState.EX["Read_data2"])
            should_branch = (decoded.is_beq() and same) or (decoded.is_bne() and not same)
            self.nextState.IF["PC"] += (self.nextState.EX["Imm"] if should_branch else WORD_LEN)
            self.stage_manager.reset()
            return

        # otherwise continue through EX/MEM/WB
        self.instr_type = decoded.type
        self.stage_manager.forward()

    def EX_forward(self) -> None:
        src_a = self.nextState.EX["Read_data1"]
        src_b = self.nextState.EX["Read_data2"] if self.instr_type in [INSTR_TYPES.R, INSTR_TYPES.B] else self.nextState.EX["Imm"]

        # compute ALU result
        self.nextState.MEM["ALUresult"] = self.nextState.EX["alu_op"](src_a, src_b)
        self.nextState.MEM["Wrt_reg_addr"] = self.nextState.EX["Wrt_reg_addr"]
        self.nextState.MEM["Store_data"] = self.nextState.EX["Read_data2"]

        self.stage_manager.forward()

    def MEM_forward(self) -> None:
        if self.instr_type == INSTR_TYPES.S:
            self.ext_dmem.writeDataMem(self.nextState.MEM["ALUresult"], self.nextState.MEM["Store_data"])

        if self.instr_type == INSTR_TYPES.LOAD_I:
            addr = self.nextState.MEM["ALUresult"]
            val = self.ext_dmem.readDataMem(addr)
            self.nextState.WB["Wrt_data"] = val
        else:
            self.nextState.WB["Wrt_data"] = self.nextState.MEM["ALUresult"]

        self.nextState.WB["Wrt_reg_addr"] = self.nextState.MEM["Wrt_reg_addr"]
        self.stage_manager.forward()

    def WB_forward(self) -> None:
        if self.instr_type in [INSTR_TYPES.R, INSTR_TYPES.I, INSTR_TYPES.LOAD_I]:
            self.myRF.writeRF(self.nextState.WB["Wrt_reg_addr"], self.nextState.WB["Wrt_data"])

        self.nextState.IF["PC"] += WORD_LEN
        self.stage_manager.reset()

    def step(self) -> None:
        # Determine whether to stop advancing before executing
        if self.state.IF["nop"]:
            self.halted = True
        else:
            if self.stage_manager.is_stage(STAGES.IF):
                self.IF_forward()
            if self.stage_manager.is_stage(STAGES.ID):
                self.ID_forward()
            if self.stage_manager.is_stage(STAGES.EX):
                self.EX_forward()
            if self.stage_manager.is_stage(STAGES.MEM):
                self.MEM_forward()
            if self.stage_manager.is_stage(STAGES.WB):
                self.WB_forward()

        # Persist side effects: RF dump and state log must not change format
        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)

        # Roll the pipeline registers and update metrics
        self.state = deepcopy(self.nextState)
        self.cycle += 1
        self.monitor.update_cycle()

    def printState(self, state: State, cycle: int) -> None:
        # Keep identical content layout for autograding
        printstate = [
            "-" * 70 + "\n",
            "State after executing cycle: " + str(cycle) + "\n",
        ]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        perm = "w" if cycle == 0 else "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)
