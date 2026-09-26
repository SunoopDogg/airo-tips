"""P82B715 센서측 기판 외곽의 가공 도면.

기판 3장(extender_1 · extender_2 · extender_3)이 같은 형상이므로 도면은 하나다(cad/CLAUDE.md). `extender_board()`를 불러 compound에서 label `extender_1`인 기판 솔리드만 꺼내고, 브래킷에서 먼 큰 면 하나를 골라 `flatten.flatten_face`로 XY에 눕힌다. 그 면은 기판 자기 좌표에서 z = ext_T인 면이다(`extender_board.py` docstring: z = 0 면이 브래킷 뒤 벽 바깥면에 닿는다). 뒤 두 기판은 챔버 축에 나란하지 않으므로 면은 챔버 축이 아니라 `sen55_bracket.extender_location(i)`가 정하는 기판 자기 좌표축으로 고른다. 기판의 긴 변(자기 좌표 +x)이 도면 +x를 향하도록 Z축으로만 돌리고(뒤집지 않는다), 판 외곽의 왼쪽 아래 모서리가 (0, 0)이 되도록 옮긴다. 회전각은 면의 평면에서, 이동량은 돌린 면의 bounding box에서 계산하므로 도면의 길이와 좌표는 모두 모델 형상에서 온다. 면을 고르는 좌표 ext_T만 params.py에서 가져온다.

도면은 기판 외곽과 M3 구멍 2개다. 반환은 면 하나이고 엔진이 CUT 레이어에 둔다. kerf는 0이다.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import dxf
from cadgen import flatten

from extender_board import extender_board
from params import ext_T
from sen55_bracket import extender_location

# 같은 형상 3장 중 도면으로 펼치는 기판의 번호
BOARD = 1

# 면 선택 허용치 — flatten.planar_faces와 같은 값
TOL = 0.02


def board_frame(i: int) -> bd.Plane:
    """기판 i의 자기 좌표를 챔버 좌표에 놓은 평면. x 긴 변, y 짧은 변, z 두께(브래킷에서 멀어지는 쪽)."""
    return bd.Plane(extender_location(i))


def far_face(i: int) -> bd.Face:
    """기판 i에서 브래킷에서 먼 큰 면. compound에서 기판 i만 꺼내 자기 좌표의 법선 +z와 z = ext_T로 고른다."""
    board = next(p for p in extender_board().children if p.label == f"extender_{i}")
    frame = board_frame(i)
    faces = [
        f
        for f in board.faces()
        if f.geom_type == bd.GeomType.PLANE
        and abs(f.normal_at().dot(frame.z_dir) - 1.0) <= TOL
        and abs(frame.to_local_coords(f.center()).Z - ext_T) <= TOL
    ]
    if len(faces) != 1:
        raise ValueError(f"extender_{i}의 브래킷에서 먼 면이 {len(faces)}개 골라졌다")
    return faces[0]


def long_side_angle(face: bd.Face, long_dir: bd.Vector) -> int:
    """눕힌 면에서 기판의 긴 변 방향 long_dir이 도면 +X를 향하게 하는 Z축 회전각(0·90·180·270)."""
    plane = bd.Plane(face)  # flatten_face가 면을 XY로 옮길 때 쓰는 평면
    if abs(long_dir.dot(plane.z_dir)) > 1e-9:
        raise ValueError("기판의 긴 변이 면 안에 있지 않다")
    angle = -math.degrees(math.atan2(long_dir.dot(plane.y_dir), long_dir.dot(plane.x_dir)))
    quarter = round(angle / 90.0)
    if abs(angle - 90.0 * quarter) > 1e-6:
        raise ValueError(f"회전각 {angle}이 90°의 배수가 아니다")
    return (90 * quarter) % 360


def board_flat(i: int) -> bd.Face:
    """기판 i의 먼 면을 눕혀 긴 변을 도면 +X에 맞춰 돌리고, 외곽의 왼쪽 아래를 원점으로 옮긴다."""
    face = far_face(i)
    flat = flatten.flatten_face(face).rotate(bd.Axis.Z, long_side_angle(face, board_frame(i).x_dir))
    lo = flat.bounding_box().min
    return flat.moved(bd.Location((-lo.X, -lo.Y, 0)))


@dxf(out="../dxf/extender_board.dxf")
def extender_board_drawing():
    """extender_1의 브래킷에서 먼 면. 세 기판이 같은 형상이라 하나만 낸다."""
    return board_flat(BOARD)


if __name__ == "__main__":
    extender_board_drawing()
