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

CMEM_OFFSETS = {                      
    0x28: "out",                      
    0x160: "out",          
    0x0: "ntid.x",                
    0x168: "input_size",
}

def _cmem_alias(offset: int) -> str:
    """Translate c[0x0][offset] into a symbolic name."""
    return CMEM_OFFSETS.get(offset, f"cmem_{offset:x}")

def parse_sass_to_ir(sass_code: str) -> List[Dict]:
    """
    Very small, purpose-built SASS→IR mapper for the write kernel
    (enough to prove out the pipeline; extend as you need).
    """
    ir: List[Dict] = []

    for raw in sass_code.splitlines():
        line = raw.split(';')[0]                 
        line = re.sub(r'^\s*/\*.*?\*/\s*', "", line)  
        line = line.strip()
        if not line or line.startswith(('//', '.', 'arch', 'code', 'host',
                                        'compile_size', '=', 'Function')):
            continue

        # Skip predicated instructions with @!PT or @P0
        if line.startswith('@'):
            continue

        # IMAD.MOV.U32 - Load constant with MOV variant
        m = re.match(r'IMAD\.MOV\.U32\s+R(\d+),\s*RZ,\s*RZ,\s*c\[0x0\]\[0x([0-9a-f]+)\]', line, re.I)
        if m:
            dst = f"r{m.group(1)}"
            src = _cmem_alias(int(m.group(2), 16))
            ir.append({"op": "mov.u32", "dst": dst, "src": src})
            continue

        # IMAD.MOV.U32 - Load immediate constant
        m = re.match(r'IMAD\.MOV\.U32\s+R(\d+),\s*RZ,\s*RZ,\s*0x([0-9a-f]+)', line, re.I)
        if m:
            ir.append({"op": "mov.u32",
                       "dst": f"r{m.group(1)}",
                       "src": int(m.group(2), 16)})
            continue

        # LDC.U16 - Load constant 16-bit
        m = re.match(r'LDC\.U16\s+R(\d+),\s*c\[0x0\]\[0x([0-9a-f]+)\]', line, re.I)
        if m:
            dst = f"r{m.group(1)}"
            src = _cmem_alias(int(m.group(2), 16))
            ir.append({"op": "mov.u16", "dst": dst, "src": src})
            continue

        # PRMT - Permute bytes (simplified - just move source)
        m = re.match(r'PRMT\s+R(\d+),\s*R(\d+),\s*0x([0-9a-f]+),\s*RZ', line, re.I)
        if m:
            ir.append({"op": "mov.u32",
                       "dst": f"r{m.group(1)}",
                       "src": f"r{m.group(2)}"})
            continue

        # ISETP.GT.AND - Set predicate (skip for now)
        m = re.match(r'ISETP\.(GT|NE)\.AND\s+P\d+,\s*PT,.*', line, re.I)
        if m:
            continue

        # FSEL - Floating point select (conditional assignment)
        m = re.match(r'FSEL\s+R(\d+),\s*RZ,\s*([0-9]+),\s*P\d+', line, re.I)
        if m:
            ir.append({"op": "mov.u32",
                       "dst": f"r{m.group(1)}",
                       "src": int(m.group(2))})
            continue

        # STG.E.SYS - Store global with cache modifiers
        m = re.match(r'STG[\.\w]*\s+\[R(\d+)\],\s*R(\d+)', line, re.I)
        if m:
            ir.append({"op": "st.global.u32",
                       "addr": f"r{m.group(1)}",
                       "val": f"r{m.group(2)}"})
            continue

        # EXIT and BRA - Control flow (skip)
        if re.match(r'(EXIT|BRA)', line, re.I):
            continue

        # Existing patterns...
        m = re.match(r'MOV\s+R(\d+),\s*c\[0x0\]\[0x([0-9a-f]+)\]', line, re.I)
        if m:
            dst = f"r{m.group(1)}"
            src = _cmem_alias(int(m.group(2), 16))
            ir.append({"op": "mov.u32", "dst": dst, "src": src})
            continue

        m = re.match(r'MOV\s+R(\d+),\s*0x([0-9a-f]+)', line, re.I)
        if m:
            ir.append({"op": "mov.u32",
                       "dst": f"r{m.group(1)}",
                       "src": int(m.group(2), 16)})
            continue

        m = re.match(r'S2R\s+R(\d+),\s*SR_(\w+)\.([A-Z]+)', line, re.I)
        if m:
            sr = f"{m.group(2).lower()}.{m.group(3).lower()}"
            ir.append({"op": "mov.u32", "dst": f"r{m.group(1)}", "src": sr})
            continue

        m = re.match(r'IMAD\s+R(\d+),\s*R(\d+),\s*c\[0x0\]\[0x0\],\s*R(\d+)',
                     line, re.I)
        if m:
            ir.append({"op": "mad.lo.s32",
                       "dst": f"r{m.group(1)}",
                       "src1": f"r{m.group(2)}",
                       "src2": "ntid.x",
                       "src3": f"r{m.group(3)}"})
            continue

        # IMAD.WIDE - Multiply-add wide (64-bit result)
        m = re.match(r'IMAD\.WIDE\s+R(\d+),\s*R(\d+),\s*R(\d+),\s*c\[0x0\]\[0x([0-9a-f]+)\]', line, re.I)
        if m:
            dst_reg = f"r{m.group(1)}"
            src1_reg = f"r{m.group(2)}" 
            src2_reg = f"r{m.group(3)}"
            offset = int(m.group(4), 16)
            base = _cmem_alias(offset)
            ir.extend([
                {"op": "mul.wide.s32", "dst": dst_reg, "src1": src1_reg, "src2": src2_reg},
                {"op": "add.s64", "dst": dst_reg, "src1": dst_reg, "src2": base}
            ])
            continue
        
        m = re.match(r'STG[\.\w]*\s+\[R(\d+)\],\s*R(\d+)', line, re.I)
        if m:
            ir.append({"op": "st.global.u32",
                       "addr": "rd4",
                       "val": f"r{m.group(2)}"})
            continue
        
        m = re.match(r'FSEL\s+R(\d+),\s*RZ,\s*([0-9]+),\s*P\d+', line, re.I)
        if m:
            ir.append({"op": "fsel",
                       "dst": f"r{m.group(1)}",
                       "src": int(m.group(2))})
            continue

    return ir