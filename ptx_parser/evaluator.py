# evaluator.py

from typing import Dict, Union

def resolve(val, regs):
    if isinstance(val, str):
        return regs.get(val, val)
    return val
    
def evaluate_instruction(instr, regs: Dict[str, Union[int, str]]):
    op = instr["op"]
    #print(f"Evaluating instruction: {op} with args {instr}")
    if op == "ld.param.u64":
        regs[instr["dst"]] = regs[instr["src"]]
    elif op == "cvta.to.global.u64":
        regs[instr["dst"]] = regs[instr["src"]]
    elif op.startswith("mov"):
        regs[instr["dst"]] = regs[instr["src"]] if isinstance(instr["src"], str) else instr["src"]
    elif op.startswith("mad.lo.s32"):
        regs[instr["dst"]] = resolve(regs[instr["src1"]], regs) * resolve(regs[instr["src2"]], regs) + resolve(regs[instr["src3"]], regs)
    elif op.startswith("mul.wide.s32"):
        src2 = instr["src2"]
        src2_val = regs[src2] if isinstance(src2, str) else src2
        regs[instr["dst"]] = regs[instr["src1"]] * src2_val
    elif op.startswith("add.s64"):
        regs[instr["dst"]] = resolve(regs[instr["src1"]], regs) + resolve(regs[instr["src2"]], regs)
    elif op.startswith("st.global"):
        return regs[instr["addr"]]
    return None