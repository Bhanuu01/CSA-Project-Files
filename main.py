from copy import deepcopy
from arg_utils import Args, get_args
from core import SingleStageCore
from mem import DataMem, InsMem


def process_testcase(TC_args: Args):
    imem = InsMem("Imem", TC_args.iodir)
    dmem_ss = DataMem("SS", TC_args.iodir, TC_args.output_dir)
    ssCore = SingleStageCore(TC_args.output_dir, imem, dmem_ss)
    while not ssCore.halted:
        ssCore.step()
    dmem_ss.outputDataMem()
    ssCore.myRF.outputRF(ssCore.cycle)
    ssCore.printState(ssCore.nextState, ssCore.cycle)
    ssCore.monitor.writePerformance(mode='w')


if __name__ == "__main__":
    args = get_args()

    for testcase_folder in args.iodir.glob('*'):
        if testcase_folder.name.startswith('.'):
            continue

        print(f"Processing {testcase_folder} ...")
        testcase_args = deepcopy(args)
        testcase_args.iodir = testcase_folder
        testcase_args.output_dir = args.output_dir / testcase_folder.name
        testcase_args.output_dir.mkdir(parents=True, exist_ok=True)

        process_testcase(testcase_args)

    print("Done!")
