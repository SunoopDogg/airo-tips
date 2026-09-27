"""외함 패널 6장의 가공 도면.

`chamber_panel()`을 불러 패널마다 챔버 바깥에서 본 면 하나를 골라 `flatten.flatten_face`로 XY에 눕힌다. 도면 위쪽이 cad/CLAUDE.md가 정한 챔버 방향(세로 판은 +z, 천장·바닥은 +y)이 되도록 Z축으로만 돌리고(뒤집지 않는다), 판 외곽의 왼쪽 아래 모서리가 (0, 0)이 되도록 옮긴다. 회전각은 면의 평면에서, 이동량은 돌린 면의 bounding box에서 계산하므로 도면의 길이와 좌표는 모두 모델 형상에서 온다. 바깥면을 고르는 좌표만 params.py에서 가져온다.

반환은 면 하나이고 엔진이 CUT 레이어에 둔다. kerf는 0이다.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import dxf
from cadgen import flatten

from chamber_panel import chamber_panel
from params import (
    panel_back_y1,
    panel_bottom_z0,
    panel_front_y0,
    panel_left_x0,
    panel_right_x1,
    panel_top_z1,
)

AXIS = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}

# 패널 label → (바깥면 법선 축, 법선 부호, 바깥면 좌표, 도면 위쪽이 될 챔버 축)
OUTER_FACE = {
    "panel_front": ("y", -1.0, panel_front_y0, "z"),
    "panel_back": ("y", 1.0, panel_back_y1, "z"),
    "panel_left": ("x", -1.0, panel_left_x0, "z"),
    "panel_right": ("x", 1.0, panel_right_x1, "z"),
    "panel_top": ("z", 1.0, panel_top_z1, "y"),
    "panel_bottom": ("z", -1.0, panel_bottom_z0, "y"),
}


def outer_face(label: str) -> bd.Face:
    """패널 label의 바깥면. 조립품에서 그 패널만 꺼내 법선과 좌표로 고른다."""
    axis, sign, coordinate, _up = OUTER_FACE[label]
    panel = next(p for p in chamber_panel().children if p.label == label)
    faces = flatten.planar_faces(panel, normal_axis=axis, normal_sign=sign, coordinate_axis=axis, coordinate=coordinate)
    if len(faces) != 1:
        raise ValueError(f"{label} 바깥면이 {len(faces)}개 골라졌다")
    return faces[0]


def up_angle(face: bd.Face, up: str) -> int:
    """눕힌 면에서 챔버 up 축이 도면 +Y를 향하게 하는 Z축 회전각(0·90·180·270)."""
    plane = bd.Plane(face)  # flatten_face가 면을 XY로 옮길 때 쓰는 평면
    d = bd.Vector(AXIS[up])
    if abs(d.dot(plane.z_dir)) > 1e-9:
        raise ValueError(f"챔버 {up} 축이 면 안에 있지 않다")
    angle = 90.0 - math.degrees(math.atan2(d.dot(plane.y_dir), d.dot(plane.x_dir)))
    quarter = round(angle / 90.0)
    if abs(angle - 90.0 * quarter) > 1e-6:
        raise ValueError(f"회전각 {angle}이 90°의 배수가 아니다")
    return (90 * quarter) % 360


def panel_drawing(label: str) -> bd.Face:
    """바깥에서 본 면을 위쪽에 맞춰 돌리고, 외곽의 왼쪽 아래를 원점으로 옮긴다."""
    face = outer_face(label)
    flat = flatten.flatten_face(face).rotate(bd.Axis.Z, up_angle(face, OUTER_FACE[label][3]))
    lo = flat.bounding_box().min
    return flat.moved(bd.Location((-lo.X, -lo.Y, 0)))


@dxf(out="../dxf/panel_front.dxf")
def panel_front():
    return panel_drawing("panel_front")


@dxf(out="../dxf/panel_back.dxf")
def panel_back():
    return panel_drawing("panel_back")


@dxf(out="../dxf/panel_left.dxf")
def panel_left():
    return panel_drawing("panel_left")


@dxf(out="../dxf/panel_right.dxf")
def panel_right():
    return panel_drawing("panel_right")


@dxf(out="../dxf/panel_top.dxf")
def panel_top():
    return panel_drawing("panel_top")


@dxf(out="../dxf/panel_bottom.dxf")
def panel_bottom():
    return panel_drawing("panel_bottom")


if __name__ == "__main__":
    panel_front()
    panel_back()
    panel_left()
    panel_right()
    panel_top()
    panel_bottom()
