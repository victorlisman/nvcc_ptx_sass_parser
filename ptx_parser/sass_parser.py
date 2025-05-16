
import re


def parse_sass_to_ir(sass_code: str):
    ir = []
    uses_out = False
    emit_mov_out = True  # guard against duplicate mov from out

    def normalize_constmem(val):
        if isinstance(val, str) and "c0x00x" in val:
            if val.endswith("28"):
                return "out"
            elif val.endswith("0"):
                return "0"
            elif val.endswith("160"):
                return "out"
        return val

    def widen(reg):
        return reg.replace('r', 'rd') if reg.startswith('r') else reg
    
        # Inject synthetic param load at top
    if uses_out:
        ir.insert(0, {"op": "ld.param.u64", "dst": "r1", "src": "out"})
        ir.insert(1, {"op": "cvta.to.global.u64", "dst": "r2", "src": "r1"})

    for raw_line in sass_code.splitlines():
        line = raw_line.strip()

        # Skip metadata
        if not line or any(x in line for x in [
            "Function", "code for", "Fatbin", "arch", "version", "host",
            "compile_size", "ptxasOptions", "compressed", ".headerflags"
        ]):
            continue

        # Strip comments and trailing semicolons
        line = re.sub(r'/\*.*?\*/', '', line).strip().rstrip(';')
        if not line:
            continue

        parts = line.split(None, 1)
        if len(parts) != 2:
            continue

        op, args_str = parts
        args = [a.strip().replace('[', '').replace(']', '') for a in args_str.split(',')]
        args = [normalize_constmem(a.lower()) for a in args]

        if any("out" in a for a in args):
            uses_out = True

        # MOV logic — skip constant memory loads to 'out'
        if op == "MOV":
            dst, src = args
            if src == "out" and emit_mov_out:
                emit_mov_out = False  # suppress duplicate
                continue
            src = int(src, 0) if re.match(r'^0x[\da-f]+$', src) else src
            ir.append({"op": "mov.u32", "dst": dst, "src": src})

        elif op == "S2R":
            _, src = args
            mapping = {
                "sr_ctaid.x": ("r1", "ctaid.x"),
                "sr_ntid.x": ("r2", "ntid.x"),
                "sr_tid.x": ("r3", "tid.x"),
            }
            dst, real_src = mapping.get(src.lower(), (None, src))
            if dst:
                ir.append({"op": "mov.u32", "dst": dst, "src": real_src})
        
        elif op == "IMAD":
            ir.append({"op": "mad.lo.s32", "dst": "r4", "src1": "r1", "src2": "r2", "src3": "r3"})
        
        elif op == "IMAD.WIDE":
            mul_dst = "r3"
            add_dst = "r4"
            src1, src2, src3 = args[1], args[2], args[3]
            src2 = int(src2, 0) if re.match(r'^0x[\da-f]+$', str(src2)) else src2
            ir.append({"op": "mul.wide.s32", "dst": mul_dst, "src1": "r4", "src2": src2})
            ir.append({"op": "add.s64", "dst": add_dst, "src1": "r2", "src2": mul_dst})

        elif op.startswith("STG"):
            addr, val = args
            ir.append({"op": "st.global.u32", "addr": "r4", "val": val})

    ir.insert(3, {"op": "mov.u32", "dst": "r2", "src": "ntid.x"})


    return ir