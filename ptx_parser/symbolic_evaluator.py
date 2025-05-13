# symbolic_evaluator.py

from typing import Dict, Any


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
            a = sym[instr["src1"]]
            b = sym[instr["src2"]]
            c = sym[instr["src3"]]
            sym[instr["dst"]] = f"({a} * {b} + {c})"

        elif op.startswith("mul") or op.startswith("mul.lo") or op.startswith("mul.wide"):
            a = sym[instr["src1"]]
            b = instr["src2"]
            sym[instr["dst"]] = f"{b} * ({a})"

        elif op.startswith("shl"):
            a = sym[instr["src1"]]
            b = instr["src2"]
            sym[instr["dst"]] = f"{a} << {b}"

        elif op.startswith("add"):
            a = sym[instr["src1"]]
            b = sym[instr["src2"]]
            sym[instr["dst"]] = f"{a} + {b}"

        elif op.startswith("setp.eq"):
            a = sym[instr["src1"]]
            b = sym[instr["src2"]]
            pred[instr["dst"]] = f"({a} == {b})"

        elif op.startswith("setp.ne"):
            a = sym[instr["src1"]]
            b = sym[instr["src2"]]
            pred[instr["dst"]] = f"({a} != {b})"

        elif op.startswith("selp"):
            dst = instr["dst"]
            tval = sym.get(instr["src1"], instr["src1"])
            fval = sym.get(instr["src2"], instr["src2"])
            cond = pred.get(instr["src3"], instr["src3"])
            sym[dst] = f"({cond}) ? {tval} : {fval}"

        elif op.startswith("st.global"):
            addr = sym[instr["addr"]]
            return addr
    return None