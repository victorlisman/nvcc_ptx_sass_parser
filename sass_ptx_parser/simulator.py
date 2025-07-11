# simulator.py

from collections import defaultdict
from typing import List, Dict, Any
from evaluator import evaluate_instruction
from utils import check_warp_coalescing

def simulate_launch(ir, grid_dim_x, block_dim_x, base_address) -> List[Dict[str, Any]]:
    accesses = []

    for ctaid_x in range(grid_dim_x):
        for tid_x in range(block_dim_x):
            regs = {
                "ctaid.x": ctaid_x,
                "ntid.x": block_dim_x,
                "tid.x": tid_x,
                "out": base_address,
                "input_size": 1234,
                #"rd1": base_address,
                #"rd2": base_address,
            }
            #print("DEGUG: BASE:", base_address)
            address = None
            written_value = None

            for instr in ir:
                result = evaluate_instruction(instr, regs)
                if result is not None:
                    if isinstance(result, dict) and "address" in result:
                        address = result["address"]
                        written_value = result.get("written_value", "unk")
                    else:
                        address = result


            if address is not None:
                global_idx = ctaid_x * block_dim_x + tid_x
                warp_id = global_idx // 32


                if written_value is not None:
                    accesses.append({
                        "blockIdx.x": ctaid_x,
                        "threadIdx.x": tid_x,
                        "warp_id": warp_id,
                        "globalIdx": global_idx,
                        "address": address,
                        "written_value": written_value,
                        "memory_offset": (address - base_address) // 4  # assume 4-byte words
                    })
                else:
                    accesses.append({
                        "blockIdx.x": ctaid_x,
                        "threadIdx.x": tid_x,
                        "warp_id": warp_id,
                        "globalIdx": global_idx,
                        "address": address
                    })

    #print(f"DEBUG: Accesses: {accesses[0]}")
    return accesses

def analyze_warp_usage(accesses):
    warps = defaultdict(list)

    for entry in accesses:
        warp_key = (entry["blockIdx.x"], entry["warp_id"])
        warps[warp_key].append(entry)

    result = []
    for (block, warp), threads in warps.items():
        thread_ids = sorted(t["threadIdx.x"] for t in threads)
        addresses = sorted(t["address"] for t in threads)
        contiguous = all(
            b - a == 4 for a, b in zip(addresses, addresses[1:])
        )
        coalesced = check_warp_coalescing(threads)

        start_addr = addresses[0]
        end_anddr = addresses[-1]

        result.append({
            "blockIdx.x": block,
            "warp_id": warp,
            "num_threads": len(thread_ids),
            "fully_utilized": len(thread_ids) == 32,
            "address_range": f"0x{start_addr:08x} - 0x{end_anddr:08x}",
            "contiguous": contiguous,
            "coalesced": coalesced,
        })

    return result