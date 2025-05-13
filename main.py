# main.py

import argparse
import json
import os 
from parser import parse_ptx_to_ir
from simulator import simulate_launch, analyze_warp_usage
from utils import coalesce_addresses, analyze_stride, estimate_footprint
from symbolic_evaluator import evaluate_symbolic

def main():
    parser = argparse.ArgumentParser(description="Symbolic PTX memory analyzer")
    parser.add_argument("ptx_file", help="Path to the .ptx file to analyze")
    parser.add_argument("--grid", type=int, default=4, help="Grid dimension (default: 4)")
    parser.add_argument("--block", type=int, default=128, help="Block dimension (default: 128)")
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0x1000, help="Base address (hex or int, default: 0x1000)")
    parser.add_argument("--json_out", type=str, default="output.json", help="Output JSON file (default: output.json)")
    args = parser.parse_args()

    with open(args.ptx_file, "r") as f:
        ptx_code = f.read()

    ir = parse_ptx_to_ir(ptx_code)

    addresses = simulate_launch(ir, args.grid, args.block, args.base)
    accessess = addresses.copy()
    addresses = [a["address"] for a in addresses]
    footprint_info = estimate_footprint(addresses)
    ranges = coalesce_addresses(addresses)
    stride_info = analyze_stride(addresses)
    print("First 10 addresses:")
    for addr in addresses[:10]:
        print(f"0x{addr:x}")

    symbolic_expr = evaluate_symbolic(ir)

    warp_stats = analyze_warp_usage(accessess)
    print("Warp Usage:")
    for stat in warp_stats:
        print(stat)

    print("Memory Events:")
    for r in ranges:
        event = {
            "instruction": "st.global.u32",
            "access_type": "write",
            "access_size": 4,
            "address_range": r["address_range"],
            "coalesced": r["coalesced"],
            "address_expr": symbolic_expr,
            **stride_info,
            **footprint_info
        }
        print(event)

    ouput = {
        "kernel": os.path.basename(args.ptx_file).split(".")[0],
        "grid_dim_x": args.grid,
        "block_dim_x": args.block,
        "base_address": hex(args.base),
        "num_threads": args.grid * args.block,
        "num_warps": args.block // 32,
        "warp_stats": warp_stats,
        "memory_events": [
            {
                "instruction": "st.global.u32",
                "access_type": "write",
                "access_size": 4,
                "address_range": r["address_range"],
                "coalesced": r["coalesced"],
                "address_expr": symbolic_expr,
                **stride_info,
                **footprint_info
            }
            for r in ranges
        ]
    }

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(ouput, f, indent=4)
        print(f"Output written to {args.json_out}")

if __name__ == "__main__":
    main()