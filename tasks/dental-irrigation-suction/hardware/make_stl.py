"""Write the printable parts as STL files (millimetres), from the same numbers as the simulation.

    python hardware/make_stl.py            writes hardware/stl/*.stl

Parts (print in PETG unless noted; 0.2 mm layers, 4 walls, 30 % infill):
  face_shell.stl     the face round the opening, a 4 mm shell of overlapping patches, opening 45 x 64 mm (skin-tone PETG)
  lips.stl           the ring round the opening, 9 mm round section (TPU 95A)
  oral_tray.stl      floor of the mouth, cheeks, the throat sill and both posterior pools, one watertight tray that the
                     lower typodont base sits in (seal the seam with silicone)
  tongue.stl         adult tongue, 60 x 26 x 20 mm (TPU 95A, 15 % gyroid infill, so that it gives a little)
  jaw_spacer.stl     holds the typodont's upper jaw open 28 degrees (45 mm between the incisal edges)
  stand.stl          a 4 mm base plate and a 40 mm block under the back of the head: holds the shell at its height and tilt
  bulb_holder.stl    ring stand with drip cup for the bulb syringe
  ejector_handle.stl 14 mm x 80 mm handle with a 6.6 mm bore: the ejector's straight end and the 1/4 in tubing meet inside it
  ejector_cradle.stl two V-notch posts that hold the handle level

Frames: oral_tray, tongue and jaw_spacer are in mouth millimetres (x toward the throat along the lower occlusal plane,
y to the patient's left, z toward the upper jaw, origin at the lower incisal point): they fit the typodont whatever its
tilt. face_shell, lips and stand are in table millimetres as mounted (x away from the robot, y left, z up, same origin),
so the stand sets the 35 degree tilt. Holders and handle are in their own frames.
"""

from __future__ import annotations

import math
import pathlib
import struct
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import mouth as M  # noqa: E402


def _sphere(rings=16, segs=32):
    v, f = [], []
    for i in range(rings + 1):
        a = math.pi * i / rings - math.pi / 2
        for j in range(segs):
            b = 2 * math.pi * j / segs
            v.append((math.cos(a) * math.cos(b), math.cos(a) * math.sin(b), math.sin(a)))
    for i in range(rings):
        for j in range(segs):
            p, q = i * segs + j, i * segs + (j + 1) % segs
            f += [(p, q, q + segs), (p, q + segs, p + segs)]
    return np.array(v), np.array(f)


def blob(semi, center, e=1.0, rings=16, segs=32):
    v, f = _sphere(rings, segs)
    return np.sign(v) * np.abs(v) ** e * np.asarray(semi) + np.asarray(center), f


def box(size, center):
    return blob(np.asarray(size) / 2, center, e=0.05, rings=8, segs=16)


def cylinder(r, h, center, segs=48):
    th = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    c = np.asarray(center, float)
    v = [(c[0] + r * math.cos(t), c[1] + r * math.sin(t), c[2] - h / 2) for t in th] + [(c[0] + r * math.cos(t), c[1] + r * math.sin(t), c[2] + h / 2) for t in th]
    v += [tuple(c - [0, 0, h / 2]), tuple(c + [0, 0, h / 2])]
    f = []
    for i in range(segs):
        j = (i + 1) % segs
        f += [(i, j, segs + j), (i, segs + j, segs + i), (2 * segs, j, i), (2 * segs + 1, segs + i, segs + j)]
    return np.array(v), np.array(f)


def annulus(r_out, r_in, h, center, segs=48):
    """A tube: outer radius, bore radius, length along z."""
    th = np.linspace(0, 2 * math.pi, segs, endpoint=False)
    c = np.asarray(center, float)
    v = []
    for r in (r_out, r_in):
        for z in (-h / 2, h / 2):
            v += [(c[0] + r * math.cos(t), c[1] + r * math.sin(t), c[2] + z) for t in th]
    f = []
    for i in range(segs):
        j = (i + 1) % segs
        ob, ot, ib, it = 0, segs, 2 * segs, 3 * segs
        f += [(ob + i, ob + j, ot + j), (ob + i, ot + j, ot + i)]  # outside
        f += [(ib + i, it + j, ib + j), (ib + i, it + i, it + j)]  # bore
        f += [(ot + i, ot + j, it + j), (ot + i, it + j, it + i)]  # top
        f += [(ob + i, ib + j, ob + j), (ob + i, ib + i, ib + j)]  # bottom
    return np.array(v), np.array(f)


def tube_ring(points, r, sides=16):
    """A closed ring of round section through `points` (closed loop)."""
    pts = np.asarray(points, float)
    n = len(pts)
    v, f = [], []
    for k in range(n):
        d = pts[(k + 1) % n] - pts[k - 1]
        d /= np.linalg.norm(d)
        u = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < 0.9 else np.cross(d, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        w = np.cross(d, u)
        for s in range(sides):
            a = 2 * math.pi * s / sides
            v.append(pts[k] + r * (math.cos(a) * u + math.sin(a) * w))
    for k in range(n):
        for s in range(sides):
            a, b = k * sides + s, k * sides + (s + 1) % sides
            c, d = ((k + 1) % n) * sides + s, ((k + 1) % n) * sides + (s + 1) % sides
            f += [(a, c, b), (b, c, d)]
    return np.array(v), np.array(f)


def write(name, bodies):
    """Several closed bodies in one STL (slicers merge overlapping bodies)."""
    tris = []
    for v, f in bodies:
        for a, b, c in f:
            tris.append((v[a], v[b], v[c]))
    path = HERE / "stl" / name
    path.parent.mkdir(exist_ok=True)
    with open(path, "wb") as out:
        out.write(b"printable part".ljust(80, b" "))
        out.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            n = np.cross(b - a, c - a)
            n = n / (np.linalg.norm(n) or 1.0)
            out.write(struct.pack("<12fH", *n, *a, *b, *c, 0))
    print(f"{path.relative_to(HERE.parent)}: {len(tris)} triangles")


def main():
    # Mouth-frame parts are written in mouth millimetres: x = p (toward the throat), y = l (patient's left), z = c.
    sump_l, sump_r = M.SUMP["left"], M.SUMP["right"]
    fc = M.FLOOR_C
    tray = [box((84, 80, 3), (31, 0, fc - 1.5)),  # floor
            box((84, 3, 44), (31, 39.5, fc + 22)), box((84, 3, 44), (31, -39.5, fc + 22)),  # cheeks
            box((3, 80, 12), (-9.5, 0, fc + 6)),  # front wall under the lower lip
            box((3, 80, 30), (73.5, 0, fc + 15 + 8)),  # back wall above the throat
            box((4, 80, 8.5), (66, 0, fc + 4.25))]  # the throat sill: pools behind M2 hold SUMP_CAP below its top
    for (pp, ll, r, f0) in (sump_l, sump_r):
        tray.append(cylinder(r + 2, 2, (pp, ll, fc - 4)))  # pool bowl, recessed 2 mm below the floor
    write("oral_tray.stl", tray)
    t = M.TONGUE
    write("tongue.stl", [blob(t["semi"], t["center"], rings=24, segs=48)])
    write("jaw_spacer.stl", [box((8, 20, 45), (-2, 0, 22))])
    # face and lips, in world millimetres relative to the lower incisal point (the stand puts that point 60 mm above the table)
    import parts as P

    _, sectors = P._face()  # closed convex patches, 4 mm thick, that overlap into the shell round the opening
    write("face_shell.stl", [(sec.v * 1000, sec.f) for sec in sectors])
    write("lips.stl", [tube_ring(P._lip_outline(scale_out=0.0045) * 1000, 4.5)])
    write("stand.stl", [box(tuple(v * 1000 for v in size), (c[0] * 1000, c[1] * 1000, (M.TOP + c[2] - M.O[2]) * 1000)) for size, c in (P.STAND_PLATE, P.STAND_BLOCK)])
    write("bulb_holder.stl", [tube_ring([(19 * math.cos(a), 19 * math.sin(a), 70) for a in np.linspace(0, 2 * math.pi, 40, endpoint=False)], 3),
                              box((10, 10, 70), (0, -42, 35)), box((10, 26, 6), (0, -32, 70)), cylinder(50, 6, (0, 0, 3)),
                              annulus(32, 30, 14, (0, 0, 13))])
    write("ejector_handle.stl", [annulus(7, 3.3, 80, (0, 0, 40))])
    write("ejector_cradle.stl", [box((26, 12, 105), (0, -35, 52.5)), box((26, 12, 105), (0, 35, 52.5)), box((50, 90, 6), (0, 0, 3))])


if __name__ == "__main__":
    main()
