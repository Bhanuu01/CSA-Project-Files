# from copy import deepcopy
# from arg_utils import Args, get_args
# from core import SingleStageCore
# from mem import DataMem, InsMem


# def process_testcase(TC_args: Args):
#     imem = InsMem("Imem", TC_args.iodir)
#     dmem_ss = DataMem("SS", TC_args.iodir, TC_args.output_dir)
#     ssCore = SingleStageCore(TC_args.output_dir, imem, dmem_ss)
#     while not ssCore.halted:
#         ssCore.step()
#     dmem_ss.outputDataMem()
#     ssCore.myRF.outputRF(ssCore.cycle)
#     ssCore.printState(ssCore.nextState, ssCore.cycle)
#     ssCore.monitor.writePerformance(mode='w')


# if __name__ == "__main__":
#     args = get_args()

#     for testcase_folder in args.iodir.glob('*'):
#         if testcase_folder.name.startswith('.'):
#             continue

#         print(f"Processing {testcase_folder} ...")
#         testcase_args = deepcopy(args)
#         testcase_args.iodir = testcase_folder
#         testcase_args.output_dir = args.output_dir / testcase_folder.name
#         testcase_args.output_dir.mkdir(parents=True, exist_ok=True)

#         process_testcase(testcase_args)

#     print("Done!")



from copy import deepcopy
from pathlib import Path

from constants import (INSTR_TYPES, PERFORMANCE_FILE,
                       RF_FILE, SS_STATE_RESULT_FILE, STAGES, WORD_LEN)

from instruction import Instruction
from mem import DataMem, InsMem
from misc import signed_int_to_binary_str
from monitors import Monitor
from state import StageManager, State

from arg_utils import Args, get_args
from core import SingleStageCore


def execute_case(cfg: Args):
    instr_mem = InsMem("InstrMemObj", cfg.iodir)
    data_mem = DataMem("DataMemObj", cfg.iodir, cfg.output_dir)
    processor = SingleStageCore(cfg.output_dir, instr_mem, data_mem)

    while not processor.halted:
        processor.step()

    data_mem.outputDataMem()
    processor.myRF.outputRF(processor.cycle)
    processor.printState(processor.nextState, processor.cycle)
    processor.monitor.writePerformance(mode='w')


if __name__ == "__main__":
    params = get_args()
    print("🔧 Simulation starting... preparing environments\n")

    for case_path in params.iodir.glob("*"):
        if case_path.name.startswith("."):
            continue

        print(f"➡️  Executing scenario located at: {case_path}")
        case_args = deepcopy(params)
        case_args.iodir = case_path
        case_args.output_dir = params.output_dir / case_path.name
        case_args.output_dir.mkdir(parents=True, exist_ok=True)

        execute_case(case_args)
        print(f"✅ Completed processing: {case_path.name}\n")

    print("🎉 All simulations have finished successfully!")
