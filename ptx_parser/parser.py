# parser.py

import re
from typing import List, Dict

def clean(s: str) -> str:
    """Strip whitespace and leading '%' from PTX identifiers."""
    return s.strip().lstrip('%')

def parse_ptx_to_ir(ptx_code: str) -> List[Dict]:
    ir = []

    lines = ptx_code.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//') or line.endswith(':'):
            continue 

        tokens = re.split(r'\s+', line, maxsplit=1)
        if len(tokens) < 2:
            continue

        op, args = tokens
        args = args.rstrip(';')

        if op == "ld.param.u64":
            dst, src = map(clean, args.split(','))
            param = src.strip('[]')
            if param.endswith('_param_0'):
                param = "out"
            ir.append({"op": op, "dst": dst, "src": param})

        elif op == "cvta.to.global.u64":
            dst, src = map(clean, args.split(','))
            ir.append({"op": op, "dst": dst, "src": src})

        elif op.startswith("mov"):
            dst, src = map(clean, args.split(','))
            src = int(src) if src.isdigit() else src
            ir.append({"op": op, "dst": dst, "src": src})

        elif op.startswith("mad.lo.s32"):
            dst, src1, src2, src3 = map(clean, args.split(','))
            ir.append({"op": op, "dst": dst, "src1": src1, "src2": src2, "src3": src3})

        elif op.startswith("mul.wide.s32"):
            dst, src1, src2 = map(clean, args.split(','))
            src2 = int(src2) if src2.isdigit() else src2
            ir.append({"op": op, "dst": dst, "src1": src1, "src2": src2})

        elif op.startswith("add.s64"):
            dst, src1, src2 = map(clean, args.split(','))
            ir.append({"op": op, "dst": dst, "src1": src1, "src2": src2})

        elif op.startswith("st.global"):
            m = re.match(r"(.*)\[(.*?)\],\s*(\S+)", args)
            if m:
                _, addr, val = m.groups()
                ir.append({"op": op, "addr": clean(addr), "val": clean(val)})

    return ir