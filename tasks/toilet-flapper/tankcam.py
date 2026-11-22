"""Views into the tank for the demo's video only (TASK_TANKCAM=<folder>): not the policy's cameras, and they change
nothing in the trial. ``ears`` hangs above the tank's front wall and looks down and back at the overflow tube's pegs;
``clip`` looks down from above the tank's right-hand wall at the trip lever's clip; ``ear_l`` and ``ear_r`` look along
each peg from low beside it, at the ear's tab. Each saves a 640 x 360 picture every
control step. Isaac Sim's own render products and annotators; imported only when asked for."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

_STATE: dict = {"cams": {}}


def _look_at_matrix(eye, target):
    """Row-vector 4x4 placing a USD camera (looking down its -z, +y up) at ``eye``, looking at ``target``."""
    f = np.asarray(target, float) - np.asarray(eye, float)
    f /= np.linalg.norm(f)
    up = np.array([0.0, 0.0, 1.0])
    x = np.cross(f, up)
    x /= np.linalg.norm(x)
    y = np.cross(x, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3], m[3, :3] = x, y, -f, eye
    return m


def start(env_path: str, views: dict, size=(640, 360)) -> None:
    """``views``: name -> (eye, target, focal length in mm), world frame."""
    import omni.replicator.core as rep
    import omni.usd
    from pxr import Gf, Sdf, UsdGeom

    if _STATE.get("started"):
        return
    stage = omni.usd.get_context().get_stage()
    out = Path(os.environ["TASK_TANKCAM"])
    out.mkdir(parents=True, exist_ok=True)
    for name, (eye, target, focal) in views.items():
        path = f"{env_path}/tank_cam_{name}"
        cam = UsdGeom.Camera.Define(stage, path)
        cam.CreateFocalLengthAttr(float(focal))
        cam.CreateHorizontalApertureAttr(20.955)
        cam.CreateVerticalApertureAttr(20.955 * size[1] / size[0])
        cam.CreateClippingRangeAttr(Gf.Vec2f(0.01, 10.0))
        cam.GetPrim().CreateAttribute("omni:scenePartition", Sdf.ValueTypeNames.Token, True,
                                      Sdf.VariabilityUniform).Set(env_path.rsplit("/", 1)[-1])
        m = _look_at_matrix(eye, target)
        UsdGeom.Xformable(cam.GetPrim()).AddTransformOp().Set(Gf.Matrix4d(*[float(v) for v in m.reshape(-1)]))
        rp = rep.create.render_product(path, size)
        annot = rep.AnnotatorRegistry.get_annotator("rgb")
        annot.attach([rp])
        _STATE["cams"][name] = (annot, rp)
    _STATE.update(started=True, out=out, k=0)


def step() -> None:
    from PIL import Image

    k = _STATE["k"] = _STATE["k"] + 1
    for name, (annot, _) in _STATE["cams"].items():
        data = annot.get_data()
        if data is None or getattr(data, "size", 0) == 0 or np.asarray(data).ndim != 3:
            continue
        img = np.asarray(data)[..., :3].astype(np.uint8)
        Image.fromarray(img).save(_STATE["out"] / f"{name}_{k:05d}.jpg", quality=90)
