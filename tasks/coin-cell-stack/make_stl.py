"""Write the one printed part, the assembly mould, as an STL file (millimetres) into stl/, at the size the simulation
uses.  python make_stl.py

A closed solid for a slicer: one block with its round pocket. The tool holders are standard products (README).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def mould(side=60.0, height=20.0, pocket_d=20.3, depth=2.0, n=96):
    """A square block with a round pocket in its top."""
    r, h, z1 = pocket_d / 2, side / 2, height - depth
    v, f = [], []

    def add(p):
        v.append(p)
        return len(v) - 1

    # the top: a square ring round the pocket, fanned from the square's outline to the circle
    ang = [2 * math.pi * k / n for k in range(n)]
    circ_top = [add((r * math.cos(a), r * math.sin(a), height)) for a in ang]
    circ_bot = [add((r * math.cos(a), r * math.sin(a), z1)) for a in ang]
    sq = [add((h * max(-1, min(1, math.cos(a) * math.sqrt(2))), h * max(-1, min(1, math.sin(a) * math.sqrt(2))), height)) for a in ang]
    for k in range(n):
        j = (k + 1) % n
        f += [(sq[k], sq[j], circ_top[j]), (sq[k], circ_top[j], circ_top[k])]
        f += [(circ_top[k], circ_top[j], circ_bot[j]), (circ_top[k], circ_bot[j], circ_bot[k])]  # the pocket's wall
    c = add((0.0, 0.0, z1))
    f += [(c, circ_bot[(k + 1) % n], circ_bot[k]) for k in range(n)]  # the pocket's floor
    base = [add((p[0], p[1], 0.0)) for p in (v[i] for i in sq)]
    for k in range(n):
        j = (k + 1) % n
        f += [(sq[k], base[k], base[j]), (sq[k], base[j], sq[j])]  # the sides
    cb = add((0.0, 0.0, 0.0))
    f += [(cb, base[k], base[(k + 1) % n]) for k in range(n)]  # the bottom
    return np.array(v), np.array(f)


def write(path: Path, v, f, name):
    lines = [f"solid {name}"]
    for tri in f:
        a, b, c = v[tri[0]], v[tri[1]], v[tri[2]]
        nrm = np.cross(b - a, c - a)
        nrm = nrm / max(np.linalg.norm(nrm), 1e-12)
        lines.append(f"  facet normal {nrm[0]:.6f} {nrm[1]:.6f} {nrm[2]:.6f}\n    outer loop")
        lines += [f"      vertex {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}" for p in (a, b, c)]
        lines.append("    endloop\n  endfacet")
    lines.append(f"endsolid {name}")
    path.write_text("\n".join(lines) + "\n")


def main():
    import cellparts as cp

    out = HERE / "stl"
    out.mkdir(exist_ok=True)
    mm = 1000.0
    write(out / "assembly_mould.stl", *mould(cp.MOULD[0] * mm, cp.MOULD[2] * mm, cp.MOULD_POCKET[0] * mm, cp.MOULD_POCKET[1] * mm), "assembly_mould")
    print("wrote", ", ".join(sorted(p.name for p in out.glob("*.stl"))))


if __name__ == "__main__":
    main()
