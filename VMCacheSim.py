#!/usr/bin/env python3
"""CS 3853 Computer Architecture - VM & Cache Simulator (Milestone #1)."""
import sys
import math

TEAM_NUMBER = "05"
COST_PER_KB = 0.07
PAGE_SIZE = 4096            # 4 KB pages
PT_ENTRIES = 512 * 1024     # 31-bit virtual addresses -> 512K PTEs

VALID_CACHE_KB = [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
VALID_BLOCK = [4, 8, 16, 32, 64]   # 4 allowed for the experiment runs
VALID_ASSOC = [1, 2, 4, 8, 16]
VALID_PHYS_MB = [128, 256, 512, 1024, 2048, 4096]


def usage(msg):
    sys.stderr.write(f"Error: {msg}\n")
    sys.stderr.write("Usage: VMCacheSim.py -s <KB> -b <bytes> -a <assoc> -r <RR|RND> "
                     "-p <MB> -u <%> -n <instr|-1> -f <trace> [-f <trace>] [-f <trace>]\n")
    sys.exit(1)


def parse_args(argv):
    opts = {"files": []}
    i = 0
    while i < len(argv):
        flag = argv[i].lstrip("-\u2013\u2014").lower()   # tolerate en-dash from PDFs
        if i + 1 >= len(argv):
            usage(f"missing value for {argv[i]}")
        val = argv[i + 1]
        if flag == "f":
            opts["files"].append(val)
        elif flag in ("s", "b", "a", "p", "n"):
            try:
                opts[flag] = int(val)
            except ValueError:
                usage(f"-{flag} expects an integer")
        elif flag == "u":
            try:
                opts["u"] = float(val)
            except ValueError:
                usage("-u expects a number")
        elif flag == "r":
            opts["r"] = val.upper()
        else:
            usage(f"unknown option {argv[i]}")
        i += 2

    for k in ("s", "b", "a", "r", "p", "u", "n"):
        if k not in opts:
            usage(f"missing -{k}")
    if opts["s"] not in VALID_CACHE_KB:
        usage("cache size must be 8..8192 KB, power of 2")
    if opts["b"] not in VALID_BLOCK:
        usage("block size must be 4, 8, 16, 32, or 64")
    if opts["a"] not in VALID_ASSOC:
        usage("associativity must be 1, 2, 4, 8, or 16")
    if opts["r"] not in ("RR", "RND"):
        usage("replacement policy must be RR or RND")
    if opts["p"] not in VALID_PHYS_MB:
        usage("physical memory must be 128..4096 MB, power of 2")
    if not 0 <= opts["u"] <= 100:
        usage("-u must be 0..100")
    if opts["n"] != -1 and opts["n"] < 1:
        usage("-n must be >= 1 or -1 for max")
    if not 1 <= len(opts["files"]) <= 3:
        usage("provide 1 to 3 trace files")
    if opts["s"] * 1024 >= opts["p"] * 1024 * 1024:
        usage("cache must be smaller than physical memory")
    return opts


def compute(o):
    c = {}
    cache_bytes = o["s"] * 1024
    phys_bytes = o["p"] * 1024 * 1024

    c["blocks"] = cache_bytes // o["b"]
    c["rows"] = c["blocks"] // o["a"]
    c["offset_bits"] = int(math.log2(o["b"]))
    c["index_bits"] = int(math.log2(c["rows"]))
    c["phys_addr_bits"] = int(math.log2(phys_bytes))
    c["tag_bits"] = c["phys_addr_bits"] - c["index_bits"] - c["offset_bits"]
    # overhead: tag + 1 valid bit per block
    c["overhead"] = c["blocks"] * (c["tag_bits"] + 1) // 8
    c["impl_bytes"] = cache_bytes + c["overhead"]
    c["impl_kb"] = c["impl_bytes"] / 1024
    c["cost"] = c["impl_kb"] * COST_PER_KB

    c["phys_pages"] = phys_bytes // PAGE_SIZE
    c["sys_pages"] = int(c["phys_pages"] * o["u"] / 100)
    c["ppn_bits"] = int(math.log2(c["phys_pages"]))
    c["pte_bits"] = c["ppn_bits"] + 1
    c["pt_ram"] = PT_ENTRIES * len(o["files"]) * c["pte_bits"] // 8
    return c


def report(o, c):
    out = []
    p = out.append

    def row(label, value):
        # values line up at column 32, like the spec example
        p(f"{label:<32}{value}")

    p(f"Cache Simulator - CS 3853 - Team #{TEAM_NUMBER}")
    p("")
    p("Trace File(s):")
    for f in o["files"]:
        p(f"\t{f}")
    p("")
    p("***** Cache Input Parameters *****")
    p("")
    row("Cache Size:", f"{o['s']} KB")
    row("Block Size:", f"{o['b']} bytes")
    row("Associativity:", o["a"])
    row("Replacement Policy:", "Round Robin" if o["r"] == "RR" else "Random")
    row("Physical Memory:", f"{o['p']} MB")
    row("Percent Memory Used by System:", f"{o['u']:.1f}%")
    row("Instructions / Time Slice:", "max" if o["n"] == -1 else o["n"])
    p("")
    p("***** Cache Calculated Values *****")
    p("")
    row("Total # Blocks:", c["blocks"])
    row("Tag Size:", f"{c['tag_bits']} bits")
    row("Index Size:", f"{c['index_bits']} bits")
    row("Total # Rows:", c["rows"])
    row("Overhead Size:", f"{c['overhead']} bytes")
    row("Implementation Memory Size:", f"{c['impl_kb']:.2f} KB  ({c['impl_bytes']} bytes)")
    row("Cost:", f"${c['cost']:.2f} @ ${COST_PER_KB:.2f} per KB")
    p("")
    p("***** Physical Memory Calculated Values *****")
    p("")
    row("Number of Physical Pages:", c["phys_pages"])
    row("Number of Pages for System:", c["sys_pages"])
    row("Size of Page Table Entry:", f"{c['pte_bits']} bits")
    row("Total RAM for Page Table(s):", f"{c['pt_ram']} bytes")
    return "\n".join(out)


def main():
    o = parse_args(sys.argv[1:])
    c = compute(o)
    print(report(o, c))


if __name__ == "__main__":
    main()
