"""Write the printed parts of the practice hand, and the cone, as STL files in ./stl (millimetres), from the same
shapes the simulation uses: python export_stl.py

The files are the outer shapes. Before printing, add on each joint axis a 3 mm hole for the steel pin, and the cord
channels described in the README (1.5 mm, at the stated moment arms). MIT licence, like the rest of this folder.
"""

from __future__ import annotations

import pathlib

import numpy as np

import handmodel as hm


def box(centre, size):
    c, h = np.asarray(centre, float), np.asarray(size, float) / 2
    p = np.array([[sx, sy, sz] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)], float) * h + c
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4),
         (1, 5, 7), (1, 7, 3)]
    return p, f


def capsule(p0, p1, r):
    p, f, _ = hm._capsule_mesh(p0, p1, r)
    return p, f


def write(path: pathlib.Path, parts) -> None:
    """ASCII STL of several closed meshes (overlapping solids, unioned by the slicer), metres in, millimetres out."""
    lines = [f"solid {path.stem}"]
    for pts, faces in parts:
        pts = np.asarray(pts, float) * 1000.0
        for a, b, c in faces:
            n = np.cross(pts[b] - pts[a], pts[c] - pts[a])
            n = n / (np.linalg.norm(n) or 1.0)
            lines.append(f"facet normal {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}\n outer loop")
            for k in (a, b, c):
                lines.append(f"  vertex {pts[k][0]:.4f} {pts[k][1]:.4f} {pts[k][2]:.4f}")
            lines.append(" endloop\nendfacet")
    lines.append(f"endsolid {path.stem}")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    out = pathlib.Path(__file__).resolve().parent / "stl"
    out.mkdir(exist_ok=True)
    uvn = hm.uvn
    palm = [box(uvn(0.0265, 0.0, 0.0), (hm.PALM_W_PROX, 0.037, 2 * hm.HALF_T)),
            box(uvn((0.045 + hm.PALM_LEN) / 2, 0.0, 0.0), (hm.PALM_W, hm.PALM_LEN - 0.045, 2 * hm.HALF_T)),
            capsule(uvn(hm.KNUCKLE_U, -0.032, 0.0), uvn(hm.KNUCKLE_U, 0.032, 0.0), hm.HALF_T)]
    (tu0, tv0, tn0), (tu1, tv1, tn1), tr = hm.THUMB
    palm.append(capsule(uvn(tu0, tv0, tn0), uvn(tu1, tv1, tn1), tr))
    write(out / "palm_with_thumb.stl", palm)
    for i, f in enumerate(hm.FINGERS):
        l1 = hm.LENGTHS[i][0]
        r = hm.RADII[i]
        write(out / f"{f}_proximal.stl", [capsule((0, 0, 0), (0, -l1, 0), r)])
        dip, tip = hm.distal_local(i)
        write(out / f"{f}_middle_distal.stl", [capsule((0, 0, 0), tuple(dip), r), capsule(tuple(dip), tuple(tip), r * 0.95)])
    pts, faces, _ = hm.cone_mesh()
    write(out / "hand_cone.stl", [(pts, faces)])
    print(f"wrote {len(list(out.glob('*.stl')))} STL files to {out}")


if __name__ == "__main__":
    main()
