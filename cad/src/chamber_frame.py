"""외함 골조.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 3030 B형 슬롯 8 프로파일(step.parts `profile_3030_b_slot8`)의 끝면 단면을 부재 길이만큼 늘여, 통짜 세로재 4개 사이에 폭·깊이 방향 수평재 8개를 넣고 레일 밑 바닥 보강재 2개를 더한다. 골조 안쪽 면이 내부 유효 치수 W_in × D_in × H_in을 이룬다.

이음은 L자 코너 브래킷(step.parts `corner_bracket_3030_single_simple`)을 수평재 끝마다 1개, 챔버 안쪽 직각 모서리에 두 날개의 바깥 면이 두 부재 면에 닿도록 놓는다. 날개 길이·두께는 벤더 STEP 그대로이고 이 소스에 치수를 따로 두지 않는다.
"""

from __future__ import annotations

import os

from cadgen import build123d as bd
from cadgen import read_step
from cadgen import srgb
from cadgen import step

from params import (
    D_in,
    H_in,
    W_in,
    corner_bracket_id,
    frame_beam_x_L,
    frame_beam_y_L,
    frame_post_L,
    frame_x0,
    frame_x1,
    frame_y0,
    frame_y1,
    frame_z0,
    frame_z1,
    prof_W,
    profile_id,
    stiff_cx,
    stiff_L,
    stiff_y0,
    stiff_z0,
)
from style import aluminium

IMPORTED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step", "imported")
PROFILE_STEP = os.path.join(IMPORTED, f"{profile_id}.step")
BRACKET_STEP = os.path.join(IMPORTED, f"{corner_bracket_id}.step")


def profile_section() -> bd.Face:
    """벤더 프로파일의 z = 0 끝면. 단면 가운데가 원점이고 외곽은 x·y ±prof_W/2다."""
    solid = read_step(PROFILE_STEP)
    bb = solid.bounding_box()
    half = prof_W / 2
    if max(abs(bb.min.X + half), abs(bb.max.X - half), abs(bb.min.Y + half), abs(bb.max.Y - half)) > 1e-6:
        raise ValueError(f"{profile_id} 단면 외곽이 {prof_W} × {prof_W}가 아니다: {bb}")
    for face in solid.faces():
        if face.geom_type == bd.GeomType.PLANE and face.normal_at().Z < -0.999999 and abs(face.center().Z - bb.min.Z) < 1e-6:
            return face.moved(bd.Location((0, 0, -bb.min.Z)))
    raise ValueError(f"{profile_id}에서 길이 방향에 수직인 끝면을 찾지 못했다")


def member(section: bd.Face, axis: str, x0: float, y0: float, z0: float, length: float, label: str) -> bd.Solid:
    """단면을 length만큼 늘여 축이 axis인 부재를 만들고, bounding box 최소 모서리를 (x0, y0, z0)에 놓는다."""
    half = prof_W / 2
    prism = bd.Solid.extrude(section, bd.Vector(0, 0, length))  # 단면 가운데가 원점, z 0–length
    if axis == "z":
        placed = prism.moved(bd.Location((x0 + half, y0 + half, z0)))
    elif axis == "x":
        # Y축 +90° 회전으로 길이 방향 +z가 +x가 된다.
        placed = prism.moved(bd.Location((x0, y0 + half, z0 + half), (0, 1, 0), 90))
    elif axis == "y":
        # X축 −90° 회전으로 길이 방향 +z가 +y가 된다.
        placed = prism.moved(bd.Location((x0 + half, y0, z0 + half), (1, 0, 0), -90))
    else:
        raise ValueError(axis)
    placed.label = label
    placed.color = srgb(aluminium)
    return placed


def bracket_prototype() -> bd.Solid:
    """벤더 L자 브래킷을 두 날개의 바깥 면이 x = 0, y = 0 평면에 오도록 옮긴 것.

    벤더 STEP은 날개 하나가 +x, 다른 하나가 +y로 뻗고 폭이 z 0–prof_W이며, 두 날개의 바깥 면이 bounding box의 x·y 최솟값 평면에 있다. 옮긴 뒤에는 x ≥ 0, y ≥ 0, z 0–prof_W를 차지한다.
    """
    solid = read_step(BRACKET_STEP)
    bb = solid.bounding_box()
    if abs(bb.min.Z) > 1e-6 or abs(bb.max.Z - prof_W) > 1e-6:
        raise ValueError(f"{corner_bracket_id} 폭이 z 0–{prof_W}가 아니다: {bb}")
    return solid.moved(bd.Location((-bb.min.X, -bb.min.Y, 0)))


def bracket(proto: bd.Solid, corner: tuple, a: tuple, b: tuple, width_axis: int, label: str) -> bd.Solid:
    """안쪽 직각 모서리에 브래킷을 놓는다.

    corner는 모서리 선 위의 점, a와 b는 두 날개가 뻗는 방향(각각 다른 부재 면을 따라 모서리에서 멀어지는 단위 축)이다. 날개 a의 바깥 면은 −b 쪽 부재 면에, 날개 b의 바깥 면은 −a 쪽 부재 면에 닿는다. 폭 prof_W는 모서리 선(width_axis)을 따라 corner에서 시작해 부재 폭을 채운다. corner의 width_axis 성분은 그 부재 폭 구간의 시작값이다.
    """
    w = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])  # a × b
    origin = list(corner)
    if w[width_axis] < 0:
        origin[width_axis] += prof_W  # 폭 방향이 −축이면 구간의 끝에서 시작한다
    plane = bd.Plane(origin=tuple(origin), x_dir=a, z_dir=w)  # 로컬 x → a, y → b, z → w
    placed = proto.moved(bd.Location(plane))
    placed.label = label
    placed.color = srgb(aluminium)
    return placed


@step(out="../step/chamber_frame.step")
def chamber_frame():
    section = profile_section()
    post_x = {"L": frame_x0, "R": W_in}  # 세로재 x 시작 — 왼쪽 −30, 오른쪽 1380
    post_y = {"F": frame_y0, "B": D_in}  # 세로재 y 시작 — 앞 −30, 뒤 970
    beam_z = {"B": frame_z0, "T": H_in}  # 수평재 z 시작 — 아래 −30, 위 660
    members = []
    # 세로재 4개, 통짜 z −30–690
    for fb in ("F", "B"):
        for lr in ("L", "R"):
            members.append(member(section, "z", post_x[lr], post_y[fb], frame_z0, frame_post_L, f"post_{fb}{lr}"))
    # 폭 방향 수평재 4개, 세로재 사이 x 0–1380
    for fb in ("F", "B"):
        for bt in ("B", "T"):
            members.append(member(section, "x", 0.0, post_y[fb], beam_z[bt], frame_beam_x_L, f"beam_x_{fb}{bt}"))
    # 깊이 방향 수평재 4개, 세로재 사이 y 0–970
    for lr in ("L", "R"):
        for bt in ("B", "T"):
            members.append(member(section, "y", post_x[lr], 0.0, beam_z[bt], frame_beam_y_L, f"beam_y_{lr}{bt}"))
    # 바닥 보강재 2개, 레일 중심과 같은 x, 바닥 앞뒤 수평재 사이
    for cx, lr in zip(stiff_cx, ("L", "R")):
        members.append(member(section, "y", cx - prof_W / 2, stiff_y0, stiff_z0, stiff_L, f"floor_rib_{lr}"))

    # 안쪽 코너 브래킷 20개 — 수평재 끝마다 1개. (모서리 점, 날개 a, 날개 b, 폭 축)
    face_z = {"B": 0.0, "T": H_in}  # 아래 수평재 윗면 z 0, 위 수평재 아랫면 z 660
    toward_inside_z = {"B": (0, 0, 1), "T": (0, 0, -1)}
    corners = []
    # 폭 방향 수평재: 수평재 윗면(아랫면)과 세로재 옆면 사이. 모서리 선은 y 방향
    for fb in ("F", "B"):
        for bt in ("B", "T"):
            corners.append(((0.0, post_y[fb], face_z[bt]), (1, 0, 0), toward_inside_z[bt], 1))  # 왼쪽 끝, post_*L의 +x 면
            corners.append(((W_in, post_y[fb], face_z[bt]), (-1, 0, 0), toward_inside_z[bt], 1))  # 오른쪽 끝, post_*R의 −x 면
    # 깊이 방향 수평재: 수평재 윗면(아랫면)과 세로재 옆면 사이. 모서리 선은 x 방향
    for lr in ("L", "R"):
        for bt in ("B", "T"):
            corners.append(((post_x[lr], 0.0, face_z[bt]), (0, 1, 0), toward_inside_z[bt], 0))  # 앞 끝, post_F*의 +y 면
            corners.append(((post_x[lr], D_in, face_z[bt]), (0, -1, 0), toward_inside_z[bt], 0))  # 뒤 끝, post_B*의 −y 면
    # 바닥 보강재: 챔버 가운데 쪽 옆면과 바닥 앞뒤 수평재 안쪽 면 사이, 수평면 안의 직각. 모서리 선은 z 방향
    for cx in stiff_cx:
        inward = 1 if cx < W_in / 2 else -1  # 챔버 가운데(x W_in/2) 쪽
        side_x = cx + inward * prof_W / 2  # 가운데 쪽 옆면 x — 215, 1115
        corners.append(((side_x, stiff_y0, stiff_z0), (0, 1, 0), (inward, 0, 0), 2))  # 앞 끝, beam_x_FB 안쪽 면 y 0
        corners.append(((side_x, stiff_y0 + stiff_L, stiff_z0), (0, -1, 0), (inward, 0, 0), 2))  # 뒤 끝, beam_x_BB 안쪽 면 y 970

    proto = bracket_prototype()
    brackets = [bracket(proto, c, a, b, ax, f"bracket_{i:02d}") for i, (c, a, b, ax) in enumerate(corners, start=1)]

    frame = bd.Compound(children=members + brackets)
    bb = frame.bounding_box()
    want = (frame_x0, frame_y0, frame_z0, frame_x1, frame_y1, frame_z1)
    got = (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)
    if max(abs(g - w) for g, w in zip(got, want)) > 1e-6:
        raise ValueError(f"골조 외곽 {got}이 {want}와 다르다")
    return frame


if __name__ == "__main__":
    chamber_frame()
