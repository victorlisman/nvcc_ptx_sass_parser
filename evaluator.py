# evaluator.py

from typing import Dict, Union

def evaluate_instruction(instr, regs: Dict[str, Union[int, str]]):
    op = instr["op"]

    if op == "ld.param.u64":
        regs[instr["dst"]] = regs[instr["src"]]
    elif op == "cvta.to.global.u64":
        regs[instr["dst"]] = regs[instr["src"]]
    elif op.startswith("mov"):
        regs[instr["dst"]] = regs[instr["src"]] if isinstance(instr["src"], str) else instr["src"]
    elif op.startswith("mad.lo.s32"):
        regs[instr["dst"]] = regs[instr["src1"]] * regs[instr["src2"]] + regs[instr["src3"]]
    elif op.startswith("mul.wide.s32"):
        regs[instr["dst"]] = regs[instr["src1"]] * instr["src2"]
    elif op.startswith("add.s64"):
        regs[instr["dst"]] = regs[instr["src1"]] + regs[instr["src2"]]
    elif op.startswith("st.global"):
        return regs[instr["addr"]]
    return None