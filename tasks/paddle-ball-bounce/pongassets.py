"""The task's bodies as plain-text USD, written when the task file loads: the bat, the ball, the egg cup, the board and the
bat stand. Visual meshes from usdkit; colliders are separate, invisible prims (purpose "guide") with their own physics
materials. Pure Python and NumPy, plus Pillow for the board's ruled face.

Sizes are from real products: an ITTF 40+ ball (40 mm, 2.7 g), a recreational bat (blade 157 x 150 mm, 6 mm with its
rubbers, handle 100 x 30 x 23 mm, 160 g), a porcelain egg cup (50 mm tall, rim 30 mm inside, 34 mm outside) and a
600 x 400 x 5 mm foam board.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

import usdkit as uk

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets"

# -- dimensions (m, kg) ---------------------------------------------------------------------
BALL_R = 0.020
BALL_MASS = 0.0027
BLADE_L, BLADE_W, BLADE_T = 0.157, 0.150, 0.006  # along the handle (x), across (y), thickness with rubbers
HANDLE_L, HANDLE_W, HANDLE_T = 0.100, 0.030, 0.023
TAPE_L = 0.036
BAT_MASS = 0.160
BAT_COM_X = -0.035  # the bat's centre of mass, from the blade's centre towards the handle (balanced on a finger)
CUP_H, CUP_RIM_IN, CUP_RIM_OUT = 0.050, 0.015, 0.017
BOARD = (0.005, 0.600, 0.400)
STAND = (0.120, 0.090, 0.060)

LOOKS = {
    "red_rubber": uk.Look(color=(0.55, 0.02, 0.02), roughness=0.55),
    "black_rubber": uk.Look(color=(0.02, 0.02, 0.02), roughness=0.6),
    "wood": uk.Look(color=(0.62, 0.43, 0.24), roughness=0.55),
    "handle_wood": uk.Look(color=(0.55, 0.36, 0.19), roughness=0.45),
    "tape": uk.Look(color=(0.05, 0.05, 0.06), roughness=0.8),
    "ball": uk.Look(color=(0.92, 0.92, 0.90), roughness=0.45),
    "porcelain": uk.Look(color=(0.90, 0.90, 0.88), roughness=0.15),
    "board": uk.Look(color=(1.0, 1.0, 1.0), roughness=0.85, texture="board_face.png", tile=0.6),
    "board_edge": uk.Look(color=(0.92, 0.92, 0.92), roughness=0.85),
    "stand_wood": uk.Look(color=(0.45, 0.30, 0.17), roughness=0.6),
}


def _phys_material(name: str, static: float, dynamic: float, restitution: float = 0.0) -> str:
    return f"""
    def Material "{name}" (
        prepend apiSchemas = ["PhysicsMaterialAPI"]
    )
    {{
        float physics:staticFriction = {static:.4f}
        float physics:dynamicFriction = {dynamic:.4f}
        float physics:restitution = {restitution:.4f}
    }}"""


def _box_collider(name, size, center, root, material, quat_wxyz=(1.0, 0.0, 0.0, 0.0), offset=0.002) -> str:
    sx, sy, sz = size
    cx, cy, cz = center
    w, x, y, z = quat_wxyz
    return f"""
    def Cube "{name}" (
        prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "MaterialBindingAPI"]
    )
    {{
        rel material:binding:physics = </{root}/{material}>
        uniform token purpose = "guide"
        double size = 1
        float physxCollision:contactOffset = {offset}
        float physxCollision:restOffset = 0
        double3 xformOp:translate = ({cx:.6f}, {cy:.6f}, {cz:.6f})
        quatf xformOp:orient = ({w:.6f}, {x:.6f}, {y:.6f}, {z:.6f})
        float3 xformOp:scale = ({sx:.6f}, {sy:.6f}, {sz:.6f})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:orient", "xformOp:scale"]
    }}"""


def _convex_collider(name, mesh: uk.Mesh, root, material, offset=0.002) -> str:
    v, f = mesh.v, mesh.f
    return f"""
    def Mesh "{name}" (
        prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "PhysicsMeshCollisionAPI", "PhysxConvexHullCollisionAPI", "MaterialBindingAPI"]
    )
    {{
        rel material:binding:physics = </{root}/{material}>
        uniform token purpose = "guide"
        uniform token physics:approximation = "convexHull"
        int physxConvexHullCollision:hullVertexLimit = 64
        float physxCollision:contactOffset = {offset}
        float physxCollision:restOffset = 0
        int[] faceVertexCounts = [{", ".join("3" for _ in range(len(f)))}]
        int[] faceVertexIndices = [{", ".join(str(int(i)) for i in f.reshape(-1))}]
        point3f[] points = [{uk._fmt(v)}]
    }}"""


def _write(path: Path, root: str, parts, colliders: list[str], materials: str, body: str = "", schemas: str = "") -> str:
    used = sorted({p[2] for p in parts})
    looks = "".join(uk._material_usda(m, root, LOOKS[m]) for m in used)
    meshes = "".join(uk._mesh_usda(p[0], p[1], p[2], root, LOOKS[p[2]], 35.0) for p in parts)
    head = f""" (
    prepend apiSchemas = [{schemas}]
)""" if schemas else ""
    text = f"""#usda 1.0
(
    defaultPrim = "{root}"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "{root}"{head}
{{{body}{materials}
{"".join(colliders)}

    def Scope "Looks"
    {{{looks}
    }}

    def Xform "visual"
    {{{meshes}
    }}
}}
"""
    # textures by a path relative to this file, not the machine's absolute path that usdkit writes
    text = text.replace(f"@{(HERE / 'textures').as_posix()}/", "@../textures/")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        tmp = path.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(text)
        os.replace(tmp, path)
    return str(path.relative_to(HERE))


RIGID = '"PhysicsRigidBodyAPI", "PhysicsMassAPI", "PhysxRigidBodyAPI", "PhysxContactReportAPI"'
FIXED = '"PhysicsRigidBodyAPI", "PhysxRigidBodyAPI"'
FIXED_BODY = """
    bool physics:kinematicEnabled = 1
"""


def oval(a: float, b: float, n: int = 28) -> np.ndarray:
    th = np.linspace(0.0, 2 * np.pi, n, endpoint=False)
    return np.c_[a * np.cos(th), b * np.sin(th)]


def blade_outline(n: int = 28) -> np.ndarray:
    return oval(BLADE_L / 2, BLADE_W / 2, n)


def handle_outline() -> np.ndarray:
    """The handle seen from above, counter-clockwise: 30 mm wide at the throat, slimmer in the middle, flared to 34 mm at
    the butt."""
    x0 = -BLADE_L / 2 + 0.004  # tucked 4 mm into the blade
    xs = np.array([0.0, 0.02, 0.05, 0.08, 0.104])
    ws = np.array([0.030, 0.029, 0.028, 0.031, 0.034])
    right = [(x0 - x, -w / 2) for x, w in zip(xs, ws)]
    left = [(x0 - x, w / 2) for x, w in zip(xs[::-1], ws[::-1])]
    return np.array(right[::-1] + left[::-1])[::-1]


def bat() -> str:
    """Origin at the blade's centre, x towards the blade's tip (the handle at -x), z out of the red face."""
    root = "Bat"
    t = BLADE_T
    core = uk.prism(blade_outline(40), -t / 2 + 0.0015, t / 2 - 0.0015)
    red = uk.prism(oval(BLADE_L / 2 - 0.0005, BLADE_W / 2 - 0.0005, 40), t / 2 - 0.0015, t / 2, bevel=0.0004)
    black = uk.prism(oval(BLADE_L / 2 - 0.0005, BLADE_W / 2 - 0.0005, 40), -t / 2, -t / 2 + 0.0015, bevel=0.0004)
    out = handle_outline()
    out = out if _ccw(out) else out[::-1]
    handle = uk.prism(out, -HANDLE_T / 2, HANDLE_T / 2, bevel=0.004)
    throat = -BLADE_L / 2
    tape = uk.box((TAPE_L, HANDLE_W + 0.0016, HANDLE_T + 0.0016), center=(throat - TAPE_L / 2 + 0.002, 0.0, 0.0), bevel=0.003, round_xy=0.003)
    parts = [("core", core, "wood"), ("red_face", red, "red_rubber"), ("black_face", black, "black_rubber"),
             ("handle", handle, "handle_wood"), ("tape", tape, "tape")]
    mats = _phys_material("Rubber", 0.9, 0.9, 0.85) + _phys_material("Wood", 0.9, 0.8, 0.5) + _phys_material("Grip", 1.2, 1.0, 0.0)
    blade_hull = uk.prism(blade_outline(28), -t / 2, t / 2)
    hl = HANDLE_L
    cols = [
        _convex_collider("blade_collider", blade_hull, root, "Rubber"),
        _box_collider("handle_collider", (hl, HANDLE_W, HANDLE_T), (throat - hl / 2 + 0.004, 0.0, 0.0), root, "Grip"),
    ]
    a, b = BLADE_L / 2, BLADE_W / 2
    m_blade, m_handle = 0.120, 0.040
    xb, xh = 0.0 - BAT_COM_X, throat - hl / 2 - BAT_COM_X
    ixx = m_blade * b * b / 4 + m_handle * (HANDLE_W**2 + HANDLE_T**2) / 12
    iyy = m_blade * a * a / 4 + m_blade * xb * xb + m_handle * (hl * hl / 12 + xh * xh)
    izz = m_blade * (a * a + b * b) / 4 + m_blade * xb * xb + m_handle * (hl * hl / 12 + xh * xh)
    body = f"""
    float physics:mass = {BAT_MASS}
    point3f physics:centerOfMass = ({BAT_COM_X}, 0, 0)
    float3 physics:diagonalInertia = ({ixx:.3e}, {iyy:.3e}, {izz:.3e})
    float physxRigidBody:sleepThreshold = 0
    float physxRigidBody:stabilizationThreshold = 0
    float physxRigidBody:maxDepenetrationVelocity = 1
    int physxRigidBody:solverPositionIterationCount = 32
    int physxRigidBody:solverVelocityIterationCount = 4
    float physxContactReport:threshold = 0
"""
    return _write(OUT / "bat.usda", root, parts, cols, mats, body, RIGID)


def _ccw(outline) -> bool:
    x, y = outline[:, 0], outline[:, 1]
    return float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) > 0


def ball() -> str:
    """A thin-shell sphere: I = 2/3 m r^2. Linear damping stands in for air drag (about 4 % of its weight at 1.5 m/s)."""
    root = "Ball"
    inertia = 2.0 / 3.0 * BALL_MASS * BALL_R**2
    mats = _phys_material("Celluloid", 0.9, 0.9, 0.85)
    look = uk._material_usda("ball", root, LOOKS["ball"])
    text = f"""#usda 1.0
(
    defaultPrim = "{root}"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "{root}" (
    prepend apiSchemas = [{RIGID}]
)
{{
    float physics:mass = {BALL_MASS}
    point3f physics:centerOfMass = (0, 0, 0)
    float3 physics:diagonalInertia = ({inertia:.3e}, {inertia:.3e}, {inertia:.3e})
    float physxRigidBody:sleepThreshold = 0
    float physxRigidBody:stabilizationThreshold = 0
    float physxRigidBody:linearDamping = 0.26
    float physxRigidBody:angularDamping = 0.02
    float physxRigidBody:maxDepenetrationVelocity = 1
    int physxRigidBody:solverPositionIterationCount = 16
    int physxRigidBody:solverVelocityIterationCount = 4
    float physxContactReport:threshold = 0
{mats}

    def Scope "Looks"
    {{{look}
    }}

    def Sphere "collider" (
        prepend apiSchemas = ["PhysicsCollisionAPI", "PhysxCollisionAPI", "MaterialBindingAPI"]
    )
    {{
        double radius = {BALL_R}
        rel material:binding = </{root}/Looks/ball>
        rel material:binding:physics = </{root}/Celluloid>
        float physxCollision:contactOffset = 0.002
        float physxCollision:restOffset = 0
    }}
}}
"""
    path = OUT / "ball.usda"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        tmp = path.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(text)
        os.replace(tmp, path)
    return str(path.relative_to(HERE))


def egg_cup() -> str:
    """Origin at the centre of its foot. The ball rests on the rim: four walls just outside a 30 mm circle cradle it."""
    root = "EggCup"
    h = CUP_H
    prof = [(0.0, 0.0), (0.022, 0.0), (0.022, 0.004), (0.016, 0.008), (0.009, 0.014), (0.008, 0.020), (0.012, 0.026),
            (0.016, 0.034), (CUP_RIM_OUT, 0.043), (CUP_RIM_OUT, h), (CUP_RIM_IN, h), (CUP_RIM_IN - 0.001, 0.044),
            (0.010, 0.036), (0.0, 0.034)]
    cup = uk.lathe(prof, 40)
    mats = _phys_material("Porcelain", 0.6, 0.5, 0.5)
    cols = [_box_collider("foot", (0.03, 0.03, 0.036), (0.0, 0.0, 0.018), root, "Porcelain")]
    wall_h = 0.012
    for k in range(8):
        a = k * np.pi / 4
        c, s = np.cos(a), np.sin(a)
        r = CUP_RIM_IN + 0.001
        q = (np.cos(a / 2), 0.0, 0.0, np.sin(a / 2))
        cols.append(_box_collider(f"wall{k}", (0.002, 0.0125, wall_h), (r * c, r * s, h - wall_h / 2), root, "Porcelain", q))
    return _write(OUT / "egg_cup.usda", root, [("cup", cup, "porcelain")], cols, mats, FIXED_BODY, FIXED)


def board_texture() -> None:
    """The board's face: white, a grey rule every 1 cm, darker every 5 cm, blue at 15 cm and red at 25 cm above its foot.
    1,024 px for 0.6 m; the bottom 0.4 m is the board."""
    from PIL import Image, ImageDraw

    path = HERE / "textures" / "board_face.png"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 1024
    px = n / 0.6
    img = Image.new("RGB", (n, n), (250, 250, 248))
    d = ImageDraw.Draw(img)

    def row(z):  # image rows run from the top; v = 0 is the bottom
        return n - 1 - int(round(z * px))

    for k in range(0, 61):
        z = k * 0.01
        width, colour = (2, (150, 150, 150)) if k % 5 == 0 else (1, (200, 200, 200))
        d.line([(0, row(z)), (n, row(z))], fill=colour, width=width)
        d.line([(int(round(z * px)), 0), (int(round(z * px)), n)], fill=colour, width=width)
    for z, colour in ((0.15, (20, 60, 210)), (0.25, (210, 20, 20))):
        half = int(round(0.004 * px))
        d.rectangle([0, row(z) - half, n, row(z) + half], fill=colour)
    img.save(path)


def board() -> str:
    """Origin at the centre of its foot."""
    board_texture()
    root = "Board"
    tx, wy, hz = BOARD
    face = uk.Mesh(np.array([[-tx / 2, wy / 2, 0.0], [-tx / 2, -wy / 2, 0.0], [-tx / 2, -wy / 2, hz], [-tx / 2, wy / 2, hz]]) + [0, 0, 0],
                   np.array([[0, 1, 2], [0, 2, 3]]))
    # uv from usdkit's box projection: (y, z) / tile for a face along x. Shift y so that u runs 0..1 across the board.
    face = uk.Mesh(face.v + np.array([0.0, wy / 2, 0.0]), face.f)
    slab = uk.box((tx * 0.98, wy, hz), center=(0.0, wy / 2, hz / 2))
    parts = [("face", face, "board"), ("slab", slab, "board_edge")]
    mats = _phys_material("Foam", 0.5, 0.4, 0.3)
    cols = [_box_collider("collider", (tx, wy, hz), (0.0, wy / 2, hz / 2), root, "Foam")]
    return _write(OUT / "board.usda", root, parts, cols, mats, FIXED_BODY, FIXED)


def stand() -> str:
    """A wooden block the bat lies on at the start, its handle over the near edge. Origin at the centre of its foot."""
    root = "Stand"
    sx, sy, sz = STAND
    block = uk.box((sx, sy, sz), center=(0.0, 0.0, sz / 2), bevel=0.002, round_xy=0.003)
    mats = _phys_material("Wood", 0.6, 0.5, 0.2)
    cols = [_box_collider("collider", (sx, sy, sz), (0.0, 0.0, sz / 2), root, "Wood")]
    return _write(OUT / "stand.usda", root, [("block", block, "stand_wood")], cols, mats, FIXED_BODY, FIXED)


def write_all() -> dict[str, str]:
    return {"bat": bat(), "ball": ball(), "egg_cup": egg_cup(), "board": board(), "stand": stand()}
