"""The coin cell's parts, its tools and its bench, as mechkit parts: plain meshes to see, simple colliders to touch.

Sizes are from the real products (README, "Sources"). Lengths in metres, masses in kg. Every part's origin is the centre
of its bottom face, so a part's `pos` is where it stands. Pure Python and NumPy.
"""

from __future__ import annotations

import math

import numpy as np

import mechkit as m

# -- the cell ----------------------------------------------------------------------------------------------------------
CAN_OD, CAN_ID, CAN_H, CAN_FLOOR = 0.0200, 0.0195, 0.0029, 0.00025
ZINC_D, ZINC_T, ZINC_MASS = 0.0120, 0.00010, 8.1e-5  # 0.1 mm foil, 7.14 g/cm3
SEP_D, SEP_T, SEP_MASS = 0.0190, 0.00026, 1.5e-5  # Whatman GF/A, 53 g/m2
SPACER_D, SPACER_T, SPACER_MASS = 0.0158, 0.0010, 1.55e-3  # 304SS
SPRING_D, SPRING_H, SPRING_MASS = 0.0150, 0.0012, 3.0e-4
CAP_D, CAP_GASKET_D, CAP_H, CAP_MASS = 0.0185, 0.0193, 0.0020, 1.3e-3

# -- tools ------------------------------------------------------------------------------------------------------------
TW_L = 0.119  # Bergeon 6460: 119 x 15 x 11 mm
TW_LEG_T = 0.0020  # each leg's thickness (across the opening)
TW_LEG_W = 0.0060  # its width
TW_TIP_W, TW_TIP_T, TW_TIP_H = 0.0050, 0.0025, 0.0060  # the flat tip pads
TW_REST_GAP = 0.0300  # between the tips' inner faces, at rest
TW_SPRING = 0.45  # N m/rad on the hinge: about 1 N at the tips, closed
TW_MASS_LEG = 0.0025
TW_GRIP_Z = 0.080  # the gripper holds the legs this far above the tips
TW_GRIP_H, TW_GRIP_PROUD, TW_GRIP_LEAN = 0.040, 0.0005, 5.0  # the ribbed grip on each leg: 40 mm long, 0.5 mm proud, leaned 5 deg

LOOKS = {
    "steel": m.Look(m.rgb(0.78, 0.79, 0.80), metallic=1.0, roughness=0.25),
    "steel_dark": m.Look(m.rgb(0.55, 0.56, 0.58), metallic=1.0, roughness=0.35),
    "zinc": m.Look(m.rgb(0.52, 0.54, 0.57), metallic=0.8, roughness=0.45),
    "glassfibre": m.Look(m.rgb(0.97, 0.97, 0.95), roughness=0.95),
    "glassfibre_wet": m.Look(m.rgb(0.70, 0.72, 0.72), roughness=0.4),
    "gasket": m.Look(m.rgb(0.10, 0.10, 0.11), roughness=0.5),
    "tweezer": m.Look(m.rgb(0.12, 0.12, 0.13), roughness=0.55),
    "pom_white": m.Look(m.rgb(0.93, 0.93, 0.91), roughness=0.5),
    "paper": m.Look(m.rgb(0.98, 0.98, 0.97), roughness=0.9),
    "pad": m.Look(m.rgb(0.95, 0.95, 0.96), roughness=0.95),
    "glass": m.Look(glass=(0.92, 0.96, 0.96)),
    "silicone": m.Look(m.rgb(0.75, 0.80, 0.82), roughness=0.7),
}


def quat_x(deg: float) -> tuple:
    h = math.radians(deg) / 2
    return (math.cos(h), math.sin(h), 0.0, 0.0)


def quat_z(deg: float) -> tuple:
    h = math.radians(deg) / 2
    return (math.cos(h), 0.0, 0.0, math.sin(h))


def disc_colliders(name: str, d: float, t: float, z0: float = 0.0, offset: float = 0.0001, n: int = 7) -> list[str]:
    """A thin disc as the union of `n` strips along y and `n` along x, each strip's corners on the circle: a stepped disc
    that never reaches past the circle, with exact flat faces and no hull cooking (a 0.1 mm convex hull is below
    PhysX's cooking tolerances). The strips through the middle meet a tip's pad at the full radius."""
    r = d / 2
    w = d / n
    out = []
    for k in range(n):
        x0, x1 = -r + k * w, -r + (k + 1) * w
        edge = max(abs(x0), abs(x1)) if x0 * x1 > 0 else 0.0
        half = np.sqrt(max(r * r - edge * edge, 0.0))
        xc = (x0 + x1) / 2
        out.append(m.col_box(f"{name}_y{k}", (w, 2 * half, t), (xc, 0.0, z0 + t / 2), offset=offset))
        out.append(m.col_box(f"{name}_x{k}", (2 * half, w, t), (0.0, xc, z0 + t / 2), offset=offset))
    return out


# -- free parts ------------------------------------------------------------------------------------------------------


def zinc(name: str, pos) -> m.Part:
    r = ZINC_D / 2
    vis = m.cylinder(r, ZINC_T, (0, 0, ZINC_T / 2), segments=48)
    inertia = (ZINC_MASS * r * r / 4, ZINC_MASS * r * r / 4, ZINC_MASS * r * r / 2)
    return m.free(name, pos, [("disc", vis, "zinc")], disc_colliders("c", ZINC_D, ZINC_T, offset=0.00005), LOOKS, mass=ZINC_MASS,
                  friction=(0.5, 0.4), torsional_patch=0.002, contact_offset=0.00005, inertia=inertia)


def separator(name: str, pos) -> m.Part:
    r = SEP_D / 2
    vis = m.cylinder(r, SEP_T, (0, 0, SEP_T / 2), segments=64)
    wet = m.cylinder(r - 0.0002, 0.00002, (0, 0, SEP_T + 0.00001), segments=64)
    inertia = (SEP_MASS * r * r / 4, SEP_MASS * r * r / 4, SEP_MASS * r * r / 2)
    return m.free(name, pos, [("disc", vis, "glassfibre"), ("wet", wet, "glassfibre_wet", True)], disc_colliders("c", SEP_D, SEP_T, offset=0.0001), LOOKS,
                  mass=SEP_MASS, friction=(0.7, 0.6), torsional_patch=0.003, contact_offset=0.0001, inertia=inertia)


# -- fixed parts -----------------------------------------------------------------------------------------------------


def can(name: str, pos) -> m.Part:
    """The CR2032 can, open side up, its origin at the centre of its underside. The wall is 32 segments; its top 0.5 mm
    leans out by 0.3 mm, the drawn can's lip."""
    ri, ro = CAN_ID / 2, CAN_OD / 2
    n = 32
    half = math.pi / n
    rv = ri / math.cos(half)
    cols = [m.col_box("floor", (0.022, 0.022, CAN_FLOOR), (0, 0, CAN_FLOOR / 2), offset=0.0005)]
    for k in range(n):
        a0, a1 = 2 * half * k - half, 2 * half * k + half
        pts = []
        for a in (a0, a1):
            c, s = math.cos(a), math.sin(a)
            for r, z in ((rv, CAN_FLOOR), (rv, CAN_H - 0.0005), (rv + 0.0003, CAN_H), (ro / math.cos(half) + 0.0008, CAN_FLOOR), (ro / math.cos(half) + 0.0008, CAN_H)):
                pts.append((r * c, r * s, z))
        hull = m.Mesh(np.array(pts), np.array([[i, (i + 1) % 10, (i + 2) % 10] for i in range(10)]))
        cols.append(m.col_hull(f"wall_{k}", hull, offset=0.0005))
    prof = [(0.0, 0.0), (ro, 0.0), (ro, CAN_H - 0.0002), (ro - 0.0001, CAN_H), (ri + 0.0002, CAN_H), (ri, CAN_H - 0.0004), (ri, CAN_FLOOR), (0.0, CAN_FLOOR)]
    vis = m.lathe(prof, 64)
    return m.fixed(name, pos, [("can", vis, "steel")], cols, LOOKS, friction=(0.4, 0.35))


def liner(name: str, pos, size=(0.080, 0.080, 0.001)) -> m.Part:
    """Weighing paper on 1 mm silicone: gives about 0.3 mm under a 1 N press."""
    vis = m.box(size, (0, 0, size[2] / 2))
    col = m.col_box("c", size, (0, 0, size[2] / 2), offset=0.001)
    return m.fixed(name, pos, [("paper", vis, "paper")], [col], LOOKS, friction=(0.6, 0.5), compliant=(300.0, 1.5))


def block(name: str, pos, size, look: str = "pom_white") -> m.Part:
    vis = m.box(size, (0, 0, size[2] / 2))
    return m.fixed(name, pos, [("b", vis, look)], [m.col_box("c", size, (0, 0, size[2] / 2), offset=0.001)], LOOKS)


# Heathrow Scientific One-Well Tube Rack HS23053A (polystyrene), for a 50 mL tube: published 92 mm round base, 30 mm
# high, 29 mm well. The tweezers stand tips down in the well. Not published, so assumed: a solid round puck, the well
# 25 mm deep with a flat floor.
TW_RACK_D, TW_RACK_H = 0.092, 0.030
TW_WELL_D, TW_WELL_DEPTH = 0.029, 0.025
TW_WELL_FLOOR = TW_RACK_H - TW_WELL_DEPTH
# the tweezers start in the well with leg b closed this far, so that both tips' outer faces (35 mm apart at rest) clear
# the well's wall; the leg's spring then presses them against it
TW_START_CLOSE = 0.0070


def tweezer_rack(name: str, pos) -> m.Part:
    """The one-well rack: a round puck with a 29 mm well, the tweezers standing in it tips down."""
    R, H, r, fl = TW_RACK_D / 2, TW_RACK_H, TW_WELL_D / 2, TW_WELL_FLOOR
    vis = m.lathe([(0.0, fl), (r, fl), (r, H), (R - 0.002, H), (R, H - 0.002), (R, 0.0), (0.0, 0.0)][::-1], 64)
    cols = [m.col_cylinder("floor_c", R, fl, (0, 0, fl / 2), offset=0.001)]
    n = 20
    for k in range(n):
        a = 2 * math.pi * k / n
        cols.append(m.col_box(f"wall_{k}", (0.004, 0.0050, H - fl), ((r + 0.002) * math.cos(a), (r + 0.002) * math.sin(a), fl + (H - fl) / 2),
                              offset=0.0005, quat_wxyz=quat_z(math.degrees(a))))
    for k in range(8):  # the puck's body outside the well
        a = 2 * math.pi * (k + 0.5) / 8
        cols.append(m.col_box(f"body_{k}", (R - r - 0.004, 0.024, H - fl), ((R + r + 0.004) / 2 * math.cos(a), (R + r + 0.004) / 2 * math.sin(a), fl + (H - fl) / 2),
                              offset=0.001, quat_wxyz=quat_z(math.degrees(a))))
    return m.fixed(name, pos, [("puck", vis, "rack_ps")], cols, LOOKS, friction=(0.3, 0.25))


# -- the tweezers ----------------------------------------------------------------------------------------------------


TW_PAD_SET = 4.5  # deg: each tip pad is set at this angle on its leg, so that its face stands upright and its bottom lies
#                   flat with the tips closed on a 12 mm disc (each leg has then turned by about this much)


def tip_pad_points(side: float) -> np.ndarray:
    """The 8 corners of one tip pad in the tweezers' frame at rest: (x -/+) x (inner bottom, outer bottom, inner top,
    outer top). The pad is turned about its inner bottom edge by TW_PAD_SET."""
    yi, yo = side * TW_REST_GAP / 2, side * (TW_REST_GAP / 2 + TW_TIP_T)
    a = math.radians(side * TW_PAD_SET)
    c, s_ = math.cos(a), math.sin(a)
    out = []
    for x in (-TW_TIP_W / 2, TW_TIP_W / 2):
        for y, z in ((yi, 0.0), (yo, 0.0), (yi, TW_TIP_H), (yo, TW_TIP_H)):
            dy, dz = y - yi, z
            out.append((x, yi + c * dy - s_ * dz, s_ * dy + c * dz))
    return np.array(out)


def _leg(side: float):
    """One leg at rest, in the tweezers' frame (origin between the tips' bottoms, z up, the legs apart along y):
    (meshes, colliders, the leg's tilt in degrees). `side` +1 is the frame's own leg, -1 the hinged one."""
    top, bottom = TW_L, TW_TIP_H
    y_top = side * TW_LEG_T / 2
    y_bot = side * (TW_REST_GAP / 2 + TW_LEG_T / 2)
    length = math.hypot(y_bot - y_top, top - bottom)
    tilt = math.degrees(math.atan2(y_bot - y_top, top - bottom))  # about +x, from z
    centre = (0.0, (y_top + y_bot) / 2, (top + bottom) / 2)
    leg_mesh = m.box((TW_LEG_W, TW_LEG_T, length)).turned(tilt, "x").moved(centre)
    pts = tip_pad_points(side)
    tip_mesh = m.Mesh(pts, np.array([[0, 1, 3], [0, 3, 2], [4, 7, 5], [4, 6, 7], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6],
                                     [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]]))
    if side > 0:
        tip_mesh = m.Mesh(tip_mesh.v, tip_mesh.f[:, ::-1])
    tag = "a" if side > 0 else "b"
    # the ribbed grip: its outer face stands upright at rest, where the gripper's pads bear
    yc = y_top + (y_bot - y_top) * (top - TW_GRIP_Z) / (top - bottom) + side * TW_GRIP_PROUD
    grip_c = (0.0, yc, TW_GRIP_Z)
    lean = side * TW_GRIP_LEAN  # leaned in at the top, so that the faces stand upright with the tips closed on a zinc disc
    grip_mesh = m.box((TW_LEG_W, TW_LEG_T + 2 * TW_GRIP_PROUD, TW_GRIP_H)).turned(lean, "x").moved(grip_c)
    cols = [m.col_box(f"leg_{tag}", (TW_LEG_W, TW_LEG_T, length), centre, offset=0.001, quat_wxyz=quat_x(tilt)),
            m.col_hull(f"tip_{tag}", tip_mesh, offset=0.001),
            m.col_box(f"grip_{tag}", (TW_LEG_W, TW_LEG_T + 2 * TW_GRIP_PROUD, TW_GRIP_H), grip_c, offset=0.001, quat_wxyz=quat_x(lean))]
    return [(f"leg_{tag}", leg_mesh, "tweezer"), (f"tip_{tag}", tip_mesh, "tweezer"), (f"grip_{tag}", grip_mesh, "tweezer")], cols


def tweezers(name: str, pos, close: float = 0.0) -> m.Part:
    """Plastic battery tweezers: leg a and the joined head are the frame; leg b turns on a sprung hinge at the head,
    joint zero at rest (tips 24 mm apart), positive closing, up to the tips meeting."""
    parts_a, cols_a = _leg(+1.0)
    parts_b, cols_b = _leg(-1.0)
    head = ((TW_LEG_W, 2 * TW_LEG_T, 0.010), (0.0, 0.0, TW_L - 0.005))
    parts_a.append(("head", m.box(*head), "tweezer"))
    cols_a.append(m.col_box("head_c", *head, offset=0.001))
    close_deg = math.degrees(2 * math.atan2(TW_REST_GAP / 2, TW_L - TW_TIP_H / 2))
    leg_i = TW_MASS_LEG * TW_L**2 / 12
    link = m.hinge("leg_b", "X", (0.0, 0.0, TW_L), 0.0, close_deg, parts_b, cols_b, mass=TW_MASS_LEG, spring=TW_SPRING, damping=0.002,
                   friction=0.0, gravity=True, com=(0.0, -0.007, TW_L / 2), inertia=(leg_i, leg_i, 2e-8))
    start = (("leg_b", close / (TW_L - TW_TIP_H / 2)),) if close else ()
    return m.mechanism(name, pos, [link], LOOKS, frame_parts=parts_a, frame_colliders=cols_a, free_mass=TW_MASS_LEG + 0.0005, start=start,
                       frame_inertia=(leg_i, leg_i, 3e-8), friction=(0.9, 0.8), solver_iters=64)


def tweezers_in_well(name: str, pos) -> m.Part:
    """The tweezers standing tips down in the one-well rack's well, centred on `pos`: leg b starts closed by
    TW_START_CLOSE and the frame (leg a) shifted by half of it, so that both tips sit inside the 29 mm well."""
    return tweezers(name, (pos[0], pos[1] - TW_START_CLOSE / 2, pos[2]), close=TW_START_CLOSE)


def grip_width_for(tip_gap: float) -> float:
    """The pads' gap on the legs' grips that puts the tips `tip_gap` apart (rigid legs, the head as the pivot)."""
    frac = (TW_L - TW_GRIP_Z) / (TW_L - TW_TIP_H)
    return 2 * (TW_LEG_T + 2 * TW_GRIP_PROUD) + tip_gap * frac


# -- the pipette, its holder, the tube ---------------------------------------------------------------------------------
PIP_GRIP_Z = 0.120  # the left gripper holds the body this far above the tip's end
PIP_COLLAR_Z = 0.185  # the finger hook's underside, above the tip's end: it rests on the stand's upper shelf
PIP_COLLAR_R = 0.0175  # the finger hook's collar: 35 mm across, as wide as a real pipette's finger rest
PIP_BUTTON_Z = 0.262  # the plunger button's top at rest
PIP_FIRST_STOP, PIP_BLOWOUT = 0.0060, 0.0080  # plunger travel to the first stop and to the blow-out stop
PIP_SPRING = 500.0  # N/m: 3 N at the first stop
PIP_MASS = 0.10
# Heathrow Scientific 3-Place Pipette Stand HS206203 (clear acrylic): published 153 x 172 x 206 mm, upper slots 28 mm
# wide, lower slots 20 mm. Not published, so assumed: 5 mm acrylic, the upper shelf's top at the full 206 mm, the lower
# shelf's top at 80 mm, 45 mm between places, and each place's two slots in line (the real stand leans a pipette a few
# degrees). The pipette hangs by its finger hook on the upper shelf in the place nearest the work.
PIP_STAND = (0.172, 0.153, 0.206)
PIP_STAND_T = 0.005
PIP_SLOTS = ((0.028, 0.206, 0.014), (0.020, 0.080, 0.010))  # (width, the shelf's top, the slot's closed end past the pipette's axis)
PIP_PLACE_PITCH = 0.045
HOLDER_CRADLE_Z = PIP_SLOTS[0][1]  # where the finger hook's collar rests
# Corning CoolRack M6, cat. 432036 (aluminium), for six 1.5/2 mL tubes: published 60 x 43 x 38 mm, wells 11.1 mm wide
# and 32.7 mm deep at 17.8 mm pitch, so its floor is 5.3 mm thick. The tube stands in a middle well of the row nearer
# the dishes.
RACK = (0.060, 0.043, 0.038)
RACK_WELL_D, RACK_PITCH = 0.0111, 0.0178
TUBE_XY_IN_RACK = (0.0, RACK_PITCH / 2)
TUBE_OD, TUBE_ID, TUBE_H, TUBE_SEAT = 0.0108, 0.0087, 0.039, RACK[2] - 0.0327  # a 1.5 mL tube on the well's floor
LIQUID_TOP = 0.030  # the electrolyte's surface above the tube's bottom (1.0 mL)

LOOKS.update({
    "pip_body": m.Look(m.rgb(0.90, 0.90, 0.88), roughness=0.45),
    "pip_blue": m.Look(m.rgb(0.15, 0.35, 0.75), roughness=0.4),
    "pip_grey": m.Look(m.rgb(0.35, 0.36, 0.38), roughness=0.5),
    "pip_tip": m.Look(m.rgb(0.92, 0.93, 0.90), roughness=0.2, opacity=0.55),
    "liquid": m.Look(m.rgb(0.80, 0.88, 0.95), roughness=0.1, opacity=0.6),
    "tube": m.Look(m.rgb(0.95, 0.95, 0.93), roughness=0.2, opacity=0.45),
    "acrylic": m.Look(m.rgb(0.90, 0.95, 0.97), roughness=0.08, opacity=0.35),
    "rack_ps": m.Look(m.rgb(0.95, 0.80, 0.20), roughness=0.5),
    "alu": m.Look(m.rgb(0.70, 0.72, 0.75), metallic=0.9, roughness=0.4),
    "hole": m.Look(m.rgb(0.08, 0.08, 0.09), roughness=0.9),
})


def _hull_cyl(name: str, r: float, z0: float, z1: float, offset: float = 0.001, r1: float | None = None, patch: float = 0.0) -> str:
    mesh = m.lathe([(0.0, z0), (r, z0), (r if r1 is None else r1, z1), (0.0, z1)], 24)
    text = m.col_hull(name, mesh, offset=offset)
    if patch:  # a held body resists turning in the pads, as a rubber-gripped handle does
        text = text.replace("float physxCollision:restOffset = 0", f"float physxCollision:restOffset = 0\n        float physxCollision:torsionalPatchRadius = {patch}\n        float physxCollision:minTorsionalPatchRadius = {0.8 * patch}")
    return text


def pipette(name: str, pos) -> m.Part:
    """An air-displacement micropipette (10-100 uL) with a 200 uL tip, upright, its origin at the tip's end. The plunger
    is a sprung slide: 3 N at the first stop (6 mm), the blow-out stop at 8 mm."""
    body_prof = [(0.0, 0.045), (0.0028, 0.045), (0.0042, 0.075), (0.0090, 0.080), (0.0090, 0.150), (0.0100, 0.155),
                 (0.0100, 0.240), (0.0070, 0.248), (0.0035, 0.248), (0.0, 0.248)]
    parts = [
        ("tip", m.lathe([(0.0, 0.0), (0.0004, 0.0), (0.0026, 0.050), (0.0, 0.050)], 24), "pip_tip"),
        ("body", m.lathe(body_prof, 32), "pip_body"),
        ("collar", m.cylinder(PIP_COLLAR_R, 0.006, (0, 0, PIP_COLLAR_Z + 0.003), segments=32), "pip_grey"),
        ("hook", m.box((0.012, 0.024, 0.010), (0.016, 0.0, PIP_COLLAR_Z + 0.008)), "pip_grey"),
        ("band", m.cylinder(0.0101, 0.010, (0, 0, 0.205), segments=32), "pip_blue"),
        ("window", m.box((0.002, 0.008, 0.020), (-0.0098, 0.0, 0.215)), "pip_grey"),
    ]
    cols = [
        m.col_hull("tip_c", m.lathe([(0.0, 0.0), (0.0006, 0.0), (0.0026, 0.050), (0.0, 0.050)], 16), offset=0.001),
        _hull_cyl("nose_c", 0.0028, 0.045, 0.075, r1=0.0042),
        _hull_cyl("lower_c", 0.0090, 0.075, 0.152, patch=0.012),
        _hull_cyl("upper_c", 0.0100, 0.152, 0.248),
        _hull_cyl("collar_c", PIP_COLLAR_R, PIP_COLLAR_Z, PIP_COLLAR_Z + 0.006),
    ]
    b0 = PIP_BUTTON_Z
    plunger = m.slider("plunger", "Z", -PIP_BLOWOUT, 0.0,
                       [("rod", m.cylinder(0.0025, 0.016, (0, 0, b0 - 0.012 - 0.008)), "pip_grey"),
                        ("button", m.cylinder(0.0055, 0.012, (0, 0, b0 - 0.006), segments=32), "pip_blue")],
                       [_hull_cyl("button_c", 0.0055, b0 - 0.012, b0)],
                       at=(0.0, 0.0, b0), mass=0.01, spring=PIP_SPRING, damping=3.0, friction=0.0, gravity=False)
    return m.mechanism(name, pos, [plunger], LOOKS, frame_parts=parts, frame_colliders=cols, free_mass=PIP_MASS,
                       frame_inertia=(6e-4, 6e-4, 6e-6), friction=(0.9, 0.8), solver_iters=32)


def _shelf(z_top: float, slot_w: float, slot_end: float, front: float, back: float, y0: float, y1: float, n: int):
    """Boxes for a shelf from x `front` to `back` and y `y0` to `y1`, its top at `z_top`, with `n` slots `slot_w` wide,
    open towards -x and closed at `slot_end`, centred at y = 0, PITCH, 2 PITCH ..."""
    t, zc = PIP_STAND_T, z_top - PIP_STAND_T / 2
    out = [((back - slot_end, y1 - y0, t), ((back + slot_end) / 2, (y0 + y1) / 2, zc))]
    edges = [y0] + [v for k in range(n) for v in (k * PIP_PLACE_PITCH - slot_w / 2, k * PIP_PLACE_PITCH + slot_w / 2)] + [y1]
    for a, b in zip(edges[::2], edges[1::2]):
        out.append(((slot_end - front, b - a, t), ((slot_end + front) / 2, (a + b) / 2, zc)))
    return out


def pipette_holder(name: str, pos) -> m.Part:
    """The 3-place acrylic pipette stand, its origin under the axis of the place nearest the work (-y): a base, an
    upright back at +x, an upper shelf whose 28 mm slots carry the pipettes' finger hooks, and a lower shelf whose 20 mm
    slots keep their noses in line. The slots open towards -x."""
    dx, dy, h = PIP_STAND
    t = PIP_STAND_T
    front, back = -0.035, 0.025
    y0 = -(dy - 2 * PIP_PLACE_PITCH) / 2
    y1 = y0 + dy
    pieces = [((dx, dy, t), (front + dx / 2, (y0 + y1) / 2, t / 2)),
              ((t, dy, h - t), (back + t / 2, (y0 + y1) / 2, t + (h - t) / 2))]
    for w, z, end in PIP_SLOTS:
        pieces += _shelf(z, w, end, front, back, y0, y1, 3)
    parts = [(f"p{k}", m.box(*p), "acrylic") for k, p in enumerate(pieces)]
    cols = [m.col_box(f"c{k}", *p, offset=0.001) for k, p in enumerate(pieces)]
    return m.fixed(name, pos, parts, cols, LOOKS)


def tube_rack(name: str, pos) -> m.Part:
    """The CoolRack M6, its origin under the well that holds the open 1.5 mL tube with 1.0 mL of electrolyte. Every well
    but that one is seen only (a dark disc on the top); the colliders leave that one open."""
    sx, sy, sz = RACK
    tx, ty = TUBE_XY_IN_RACK
    cx, cy = -tx, -ty  # the rack's centre from its origin
    hole = RACK_WELL_D / 2
    fl = TUBE_SEAT
    x0, x1, y0, y1 = cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2
    pieces = [((sx, sy, fl), (cx, cy, fl / 2)),
              ((sx, y1 - hole, sz - fl), (cx, (y1 + hole) / 2, (sz + fl) / 2)),
              ((sx, -hole - y0, sz - fl), (cx, (y0 - hole) / 2, (sz + fl) / 2)),
              ((x1 - hole, 2 * hole, sz - fl), ((x1 + hole) / 2, 0, (sz + fl) / 2)),
              ((-hole - x0, 2 * hole, sz - fl), ((x0 - hole) / 2, 0, (sz + fl) / 2))]
    parts = [(f"p{k}", m.box(*p), "alu") for k, p in enumerate(pieces)]
    cols = [m.col_box(f"c{k}", *p, offset=0.001) for k, p in enumerate(pieces)]
    # round the open well's square corners, just under the top
    parts.append(("well", m.lathe([(hole, fl), (hole * 1.45, fl), (hole * 1.45, sz - 0.0002), (hole, sz - 0.0002), (hole, fl)], 32), "alu"))
    for i in (-1, 0, 1):
        for j in (-0.5, 0.5):
            wx, wy = cx + i * RACK_PITCH, cy + j * RACK_PITCH
            if abs(wx) < 1e-6 and abs(wy) < 1e-6:
                continue
            parts.append((f"hole{i + 1}{int(j + 0.5)}", m.cylinder(hole, 0.0002, (wx, wy, sz + 0.0001), segments=32), "hole"))
    ro, ri = TUBE_OD / 2, TUBE_ID / 2
    z0 = TUBE_SEAT
    tube_prof = [(0.0, z0), (0.0015, z0), (ro, z0 + 0.018), (ro, z0 + TUBE_H), (ro + 0.0007, z0 + TUBE_H), (ro + 0.0007, z0 + TUBE_H + 0.002),
                 (ri, z0 + TUBE_H + 0.002), (ri, z0 + 0.019), (0.0010, z0 + 0.0008), (0.0, z0 + 0.0008)]
    parts.append(("tube", m.lathe(tube_prof, 32), "tube"))
    liq = m.lathe([(0.0, z0 + 0.001), (0.0009, z0 + 0.001), (ri - 0.0001, z0 + 0.019), (ri - 0.0001, z0 + LIQUID_TOP), (0.0, z0 + LIQUID_TOP)], 32)
    parts.append(("liquid", liq, "liquid"))
    n = 16
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = [(r * math.cos(a), r * math.sin(a), z) for a in (a0, a1) for r in (ri / math.cos(math.pi / n), ro + 0.0005) for z in (z0 + 0.019, z0 + TUBE_H + 0.002)]
        cols.append(m.col_hull(f"tw{k}", m.Mesh(np.array(pts), np.array([[i, (i + 1) % 8, (i + 2) % 8] for i in range(8)])), offset=0.0005))
    cols.append(m.col_box("tb", (0.006, 0.006, 0.002), (0, 0, z0 + 0.001), offset=0.0005))
    return m.fixed(name, pos, parts, cols, LOOKS)


# -- the remaining cell parts ------------------------------------------------------------------------------------------
CAP_TOP_T = 0.00025
CAP_SKIRT_IN = 0.0175  # the skirt's inside diameter: clears the spacer and the spring
SPRING_ID = 0.0100


def spacer(name: str, pos) -> m.Part:
    r = SPACER_D / 2
    vis = m.lathe([(0.0, 0.0), (r - 0.0002, 0.0), (r, 0.0002), (r, SPACER_T - 0.0002), (r - 0.0002, SPACER_T), (0.0, SPACER_T)], 64)
    inertia = (SPACER_MASS * r * r / 4,) * 2 + (SPACER_MASS * r * r / 2,)
    return m.free(name, pos, [("disc", vis, "steel")], disc_colliders("c", SPACER_D, SPACER_T, offset=0.0002), LOOKS, mass=SPACER_MASS,
                  friction=(0.4, 0.35), torsional_patch=0.003, contact_offset=0.0002, inertia=inertia)


def wave_spring(name: str, pos) -> m.Part:
    """A wave spring washer: three waves, 15 mm across, 1.2 mm free height. It collides as a flat 1.2 mm disc whose
    contacts are soft (about 20 N per mm), standing in for its waves' give."""
    ro, ri = SPRING_D / 2, SPRING_ID / 2
    n, t = 96, 0.0003
    v, f = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        zc = (SPRING_H - t) / 2 * (1 - math.cos(3 * a))
        for r, z in ((ri, zc), (ro, zc), (ro, zc + t), (ri, zc + t)):
            v.append((r * math.cos(a), r * math.sin(a), z))
    for k in range(n):
        a0, a1 = 4 * k, 4 * ((k + 1) % n)
        for i in range(4):
            j = (i + 1) % 4
            f += [(a0 + i, a1 + i, a1 + j), (a0 + i, a1 + j, a0 + j)]
    vis = m.Mesh(np.array(v), np.array(f)[:, ::-1])
    inertia = (SPRING_MASS * ro * ro / 4,) * 2 + (SPRING_MASS * ro * ro / 2,)
    return m.free(name, pos, [("ring", vis, "steel_dark")], disc_colliders("c", SPRING_D, SPRING_H, offset=0.0002), LOOKS, mass=SPRING_MASS,
                  friction=(0.4, 0.35), torsional_patch=0.003, contact_offset=0.0002, inertia=inertia, compliant=(20000.0, 40.0))


def cap(name: str, pos) -> m.Part:
    """The CR2032 cap with its fitted polypropylene gasket, open side down, its origin at the centre of the skirt's
    bottom. The gasket's lower outside edge is chamfered 0.3 mm, as it is moulded, to lead it into the can's mouth."""
    rt, rg, ri = CAP_D / 2, CAP_GASKET_D / 2, CAP_SKIRT_IN / 2
    h = CAP_H
    steel = m.lathe([(0.0, h), (rt - 0.0005, h), (rt - 0.0002, h - 0.0003), (rt - 0.0002, 0.0004), (ri, 0.0004), (ri, h - CAP_TOP_T), (0.0, h - CAP_TOP_T)][::-1], 64)
    gasket = m.lathe([(rg - 0.0003, 0.0), (rg, 0.0003), (rg, h - 0.0006), (rt - 0.0002, h - 0.0003), (rt - 0.0002, 0.0004), (ri, 0.0004), (ri, 0.0), (rg - 0.0003, 0.0)], 64)
    cols = disc_colliders("top", CAP_D - 0.001, CAP_TOP_T, z0=h - CAP_TOP_T, offset=0.0002)
    n = 24
    half = math.pi / n
    for k in range(n):
        a0, a1 = 2 * half * k - half, 2 * half * k + half
        pts = []
        for a in (a0, a1):
            c, s = math.cos(a), math.sin(a)
            for r, z in ((ri, 0.0), (ri, h - CAP_TOP_T), (rg - 0.0003, 0.0), (rg, 0.0003), (rg, h - 0.0003)):
                pts.append((r * c / math.cos(half) if r == rg else r * c, r * s / math.cos(half) if r == rg else r * s, z))
        cols.append(m.col_hull(f"skirt_{k}", m.Mesh(np.array(pts), np.array([[i, (i + 1) % 10, (i + 2) % 10] for i in range(10)])), offset=0.0002))
    inertia = (CAP_MASS * rt * rt / 4,) * 2 + (CAP_MASS * rt * rt / 2,)
    return m.free(name, pos, [("steel", steel, "steel"), ("gasket", gasket, "gasket")], cols, LOOKS, mass=CAP_MASS,
                  friction=(0.6, 0.5), torsional_patch=0.004, contact_offset=0.0002, inertia=inertia)


# -- the bench ----------------------------------------------------------------------------------------------------------
DISH_D, DISH_H, DISH_GLASS, DISH_LINER = 0.090, 0.014, 0.0015, 0.0010
MOULD = (0.060, 0.060, 0.020)
MOULD_POCKET = (0.0203, 0.002)
PAD = (0.300, 0.400, 0.001)


def dish(name: str, pos) -> m.Part:
    """A glass petri dish lined with weighing paper on 1 mm silicone, taped down. The lining gives about 0.3 mm under a
    1 N press (soft contacts)."""
    r = DISH_D / 2
    glass = m.lathe([(0.0, 0.0), (r, 0.0), (r, DISH_H), (r - 0.0012, DISH_H), (r - 0.0012, DISH_GLASS), (0.0, DISH_GLASS)][::-1], 64)
    lining = m.cylinder(r - 0.0025, DISH_LINER, (0, 0, DISH_GLASS + DISH_LINER / 2), segments=64)
    top = DISH_GLASS + DISH_LINER
    cols = [m.col_box("lining_c", (0.070, 0.050, top), (0, 0, top / 2), offset=0.001)]
    for k in range(16):
        a = 2 * math.pi * k / 16
        cols.append(m.col_box(f"wall_{k}", (0.0015, 0.018, DISH_H), ((r - 0.0008) * math.cos(a), (r - 0.0008) * math.sin(a), DISH_H / 2),
                              offset=0.001, quat_wxyz=quat_z(math.degrees(a))))
    return m.fixed(name, pos, [("glass", glass, "glass"), ("lining", lining, "paper")], cols, LOOKS, friction=(0.6, 0.5), compliant=(300.0, 1.5))


def mould(name: str, pos) -> m.Part:
    """NPL's assembly mould: a white POM block with a 20.3 mm pocket, 2 mm deep, for the can."""
    sx, sy, sz = MOULD
    pd, pdepth = MOULD_POCKET
    vis = [("block", m.box((sx, sy, sz - pdepth), (0, 0, (sz - pdepth) / 2)), "pom_white"),
           ("rim", m.lathe([(pd / 2, sz - pdepth), (0.0299, sz - pdepth), (0.0299, sz), (pd / 2, sz)], 64), "pom_white")]
    for k, (cx, cy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        vis.append((f"corner{k}", m.box((0.012, 0.012, pdepth), (cx * 0.024, cy * 0.024, sz - pdepth / 2)), "pom_white"))
    cols = [m.col_box("base", (sx, sy, sz - pdepth), (0, 0, (sz - pdepth) / 2), offset=0.001)]
    w = (sx - 0.0205) / 2
    for k, sgn in enumerate((1, -1)):
        cols.append(m.col_box(f"side{k}", (w, sy, pdepth), (sgn * (w / 2 + 0.01025), 0, sz - pdepth / 2), offset=0.001))
    for k, sgn in enumerate((1, -1)):
        cols.append(m.col_box(f"end{k}", (0.0205, w, pdepth), (0, sgn * (w / 2 + 0.01025), sz - pdepth / 2), offset=0.001))
    return m.fixed(name, pos, vis, cols, LOOKS)


def bench_pad(name: str, pos) -> m.Part:
    vis = m.box(PAD, (0, 0, PAD[2] / 2))
    return m.fixed(name, pos, [("pad", vis, "pad")], [m.col_box("c", PAD, (0, 0, PAD[2] / 2), offset=0.001)], LOOKS)


def phone_rig(name: str, pos, height: float) -> m.Part:
    """The scoring camera: a phone on a clamp arm, looking straight down from `height` over `pos`, inside a 25 cm ring
    light. Seen only: no colliders. The clamp's pole stands at +x, beyond the arms' work."""
    parts = [
        ("phone", m.box((0.075, 0.150, 0.008), (0, 0, height + 0.004)), "pip_grey"),
        ("ring", m.lathe([(0.105, height - 0.006), (0.125, height - 0.006), (0.125, height + 0.004), (0.105, height + 0.004)], 64), "pom_white"),
        ("arm", m.box((0.26, 0.016, 0.016), (0.13 + 0.03, 0, height + 0.016)), "pip_grey"),
        ("pole", m.cylinder(0.008, height + 0.03, (0.29, 0, (height + 0.03) / 2)), "pip_grey"),
        ("foot", m.box((0.05, 0.06, 0.02), (0.29, 0, 0.01)), "pip_grey"),
    ]
    return m.fixed(name, pos, parts, [], LOOKS)
