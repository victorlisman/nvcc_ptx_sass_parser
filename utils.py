# utils.py

from typing import List, Dict

def coalesce_addresses(addresses: List[int], access_size: int = 4) -> List[Dict]:
    addresses = sorted(set(addresses))
    ranges = []

    start = prev = addresses[0]

    for addr in addresses[1:]:
        if addr == prev + access_size:
            prev = addr
        else:
            ranges.append((start, prev + access_size))
            start = prev = addr

    ranges.append((start, prev + access_size))

    return [
        {
            "address_range": f"0x{start:x} - 0x{end:x}",
            "coalesced": True
        }
        for start, end in ranges
    ]

def analyze_stride(addresses: List[int]) -> Dict:
    if len(addresses) < 2:
        return {"stride": None, "pattern": "undetermined", "density": None}

    addresses = sorted(addresses)
    diffs = [b - a for a, b in zip(addresses, addresses[1:])]
    stride_set = set(diffs)

    stride = diffs[0] if len(stride_set) == 1 else None
    pattern = "unit-strided" if stride == 4 else "irregular"
    density = len(addresses) * 4 / (addresses[-1] + 4 - addresses[0])

    return {
        "stride": stride,
        "pattern": pattern,
        "density": round(density, 2)
    }

def estimate_footprint(addresses: List[int], access_size: int = 4) -> Dict:
    addresses = sorted(set(addresses))
    if not addresses:
        return {"footprint_bytes": 0, "used_bytes": 0, "wasted_bytes": 0, "efficiency": 1.0}

    first = addresses[0]
    last = addresses[-1] + access_size
    footprint = last - first
    used = len(addresses) * access_size
    wasted = footprint - used
    efficiency = round(used / footprint, 3) if footprint > 0 else 1.0

    return {
        "footprint_bytes": footprint,
        "used_bytes": used,
        "wasted_bytes": wasted,
        "efficiency": efficiency
    }

def check_warp_coalescing(warp_entries, access_size=4, segment_size=128):
    addresses = sorted(e["address"] for e in warp_entries)
    if not addresses:
        return False

    base = addresses[0]
    max_addr = addresses[-1] + access_size

    span = max_addr - base
    aligned = (base % segment_size) == 0
    within_segment = span <= segment_size

    return aligned and within_segment