# symbolic_evaluator.py
from typing import Dict, Any

def get_val(table: Dict[str, Any], token: str):
    """Return the symbolic value if we have one, otherwise the raw token."""
    return table.get(token, token)

def evaluate_symbolic(ir) -> str:
    sym: Dict[str, Any] = {}  
    pred: Dict[str, str] = {}  

    for instr in ir:
        op = instr["op"]

        if op == "ld.param.u64":
            sym[instr["dst"]] = "out"

        elif op == "cvta.to.global.u64":
            sym[instr["dst"]] = sym[instr["src"]]

        elif op.startswith("mov"):
            sym[instr["dst"]] = instr["src"]

        elif op.startswith("mad.lo.s32"):
            a = get_val(sym, instr["src1"])
            b = get_val(sym, instr["src2"])
            c = get_val(sym, instr["src3"])
            sym[instr["dst"]] = f"({a} * {b} + {c})"

        elif op.startswith(("mul", "mul.lo", "mul.wide")):
            a = get_val(sym, instr["src1"])
            b = instr["src2"]
            sym[instr["dst"]] = f"{b} * ({a})"

        elif op.startswith("shl"):
            a = get_val(sym, instr["src1"])
            b = instr["src2"]
            sym[instr["dst"]] = f"{a} << {b}"

        elif op.startswith("add"):
            a = get_val(sym, instr["src1"])
            b = get_val(sym, instr["src2"])
            sym[instr["dst"]] = f"{a} + {b}"

        elif op.startswith("setp.eq"):
            a = get_val(sym, instr["src1"])
            b = get_val(sym, instr["src2"])
            pred[instr["dst"]] = f"({a} == {b})"

        elif op.startswith("setp.ne"):
            a = get_val(sym, instr["src1"])
            b = get_val(sym, instr["src2"])
            pred[instr["dst"]] = f"({a} != {b})"

        elif op.startswith("selp"):
            dst  = instr["dst"]
            tval = get_val(sym, instr["src1"])
            fval = get_val(sym, instr["src2"])
            cond = pred.get(instr["src3"], instr["src3"])
            sym[dst] = f"({cond}) ? {tval} : {fval}"
        elif op.startswith("st.global"):
            addr = get_val(sym, instr["addr"])
            return addr

    return None