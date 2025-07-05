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
        stored_value = regs.get(instr["val"], instr["val"])
        address = regs[instr["addr"]]
        return {"address": address, "value": stored_value}
    elif op.startswith("fsel"):
        global_thread_id = regs.get("ctaid.x", None)+ regs.get("ntid.x", 0) + regs.get("tid.x", 0)
        input_value = regs.get("input_size", 0)

        if global_thread_id == input_value:
            return {"address": regs["out"], "written_value": "unk"}
        else:
            return {"address": regs["out"], "written_value": "unk"} 
    return None