"""전장 기판 외곽의 가공 도면.

`control_board()`를 불러 compound에서 label `pcb`인 기판 솔리드만 꺼내고, 소자를 싣는 면(윗면) 하나를 골라 `flatten.flatten_face`로 XY에 눕힌다. ESP32 모듈과 USB-C 블록은 쓰지 않는다. 도면 위쪽이 챔버 +y가 되도록 Z축으로만 돌려(뒤집지 않는다) cad/CLAUDE.md가 정한 대로 기판의 긴 변을 도면 x축에 두고, 판 외곽의 왼쪽 아래 모서리가 (0, 0)이 되도록 옮긴다. 회전각은 면의 평면에서, 이동량은 돌린 면의 bounding box에서 계산하므로 도면의 길이와 좌표는 모두 모델 형상에서 온다. 윗면을 고르는 좌표만 params.py에서 가져온다.

도면은 KiCad Edge.Cuts로 가져갈 기판 외곽과 M3 구멍 4개다. 반환은 면 하나이고 엔진이 CUT 레이어에 둔다. kerf는 0이다.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import dxf
from cadgen import flatten

from control_board import control_board
from params import pcb_z1

AXIS = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}

# 소자면 법선 축, 법선 부호, 소자면 좌표, 도면 위쪽이 될 챔버 축
OUTER_FACE = ("z", 1.0, pcb_z1, "y")


def outer_face() -> bd.Face:
    """기판의 소자면. compound에서 기판만 꺼내 법선과 좌표로 고른다."""
    axis, sign, coordinate, _up = OUTER_FACE
    pcb = next(p for p in control_board().children if p.label == "pcb")
    faces = flatten.planar_faces(pcb, normal_axis=axis, normal_sign=sign, coordinate_axis=axis, coordinate=coordinate)
    if len(faces) != 1:
        raise ValueError(f"기판 소자면이 {len(faces)}개 골라졌다")
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


@dxf(out="../dxf/control_board.dxf")
def control_board_drawing():
    """소자면을 위쪽에 맞춰 돌리고, 외곽의 왼쪽 아래를 원점으로 옮긴다."""
    face = outer_face()
    flat = flatten.flatten_face(face).rotate(bd.Axis.Z, up_angle(face, OUTER_FACE[3]))
    lo = flat.bounding_box().min
    return flat.moved(bd.Location((-lo.X, -lo.Y, 0)))


if __name__ == "__main__":
    control_board_drawing()
