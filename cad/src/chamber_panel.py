"""외함 패널.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 두께 t_panel의 알루미늄 복합판 6장을 골조 바깥면 크기 그대로 덧댄다(사용자 결정 2026-10-07). 패널끼리는 겹치지 않으므로 세로·가로 모서리마다 t_panel × t_panel 홈이 남는다.

구멍은 골조 볼트·도어 개구·포트·글랜드뿐이고 철물을 다는 구멍은 내지 않는다. 볼트 구멍은 패널 뒤 골조 부재(바닥 패널은 보강재 포함)의 중심선 위에, 패널 모서리에서 panel_bolt_edge 띄운 점부터 반대쪽 모서리에서 panel_bolt_edge 띄운 점까지를 panel_bolt_pitch_max 이하의 같은 간격으로 나눠 낸다. 앞면 패널 아래 변은 밀폐재가 지나므로 양 끝 panel_bolt_front_bottom_x에만 낸다(사용자 결정 2026-10-07).

글랜드 구멍은 천장 중심을 가운데로 x 방향 한 줄에 gland_pitch 간격으로 낸다. 지름 gland_hole_dia는 step.parts `cable_gland_panel_hole_cutter_m20`의 안지름이고, 빌드할 때 그 벤더 STEP을 다시 재서 맞는지 확인한다. 글랜드 몸체 STEP은 읽지 않는다.

패널마다 면 안의 두 축(u, v)을 쓴다. 앞·뒤는 (x, z), 옆은 (y, z), 천장·바닥은 (x, y)이고, u·v 값은 그대로 챔버 좌표다. bolt_holes()가 패널마다 볼트 구멍 중심 (u, v)를 돌려주므로, 패널 구멍 자리가 필요한 다른 모델(경첩 받침 블록 등)은 이것을 가져다 쓴다.
"""

from __future__ import annotations

import math
import os

from cadgen import build123d as bd
from cadgen import read_step
from cadgen import step

from params import (
    door_x0,
    door_x1,
    door_z0,
    door_z1,
    exhaust_tube_OD,
    frame_x0,
    frame_x1,
    frame_y0,
    frame_y1,
    frame_z0,
    frame_z1,
    gland_hole_dia,
    gland_x,
    gland_y,
    inlet_tube_OD,
    out_x0,
    out_x1,
    out_y0,
    out_y1,
    out_z0,
    out_z1,
    panel_back_y0,
    panel_back_y1,
    panel_bolt_edge,
    panel_bolt_front_bottom_x,
    panel_bolt_hole_dia,
    panel_bolt_pitch_max,
    panel_bottom_z0,
    panel_bottom_z1,
    panel_front_y0,
    panel_front_y1,
    panel_left_x0,
    panel_left_x1,
    panel_right_x0,
    panel_right_x1,
    panel_top_z0,
    panel_top_z1,
    port_y,
    port_z,
    prof_W,
    stiff_cx,
    t_panel,
)

IMPORTED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step", "imported")
GLAND_CUTTER_ID = "cable_gland_panel_hole_cutter_m20"  # 글랜드 — 패널 구멍 지름(안지름 Ø20)의 출처인 step.parts 부품 (chamber.md 글랜드 행)
GLAND_CUTTER_STEP = os.path.join(IMPORTED, f"{GLAND_CUTTER_ID}.step")

AXIS = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
FRAME = {"x": (frame_x0, frame_x1), "y": (frame_y0, frame_y1), "z": (frame_z0, frame_z1)}  # 골조 바깥 외곽 = 패널 면 안의 외곽


def panel_specs() -> dict:
    """패널마다 면 안의 두 축 (u, v), 두께 방향 축 n과 그 구간 (n0, n1)."""
    return {
        "panel_front": ("x", "z", "y", panel_front_y0, panel_front_y1),
        "panel_back": ("x", "z", "y", panel_back_y0, panel_back_y1),
        "panel_left": ("y", "z", "x", panel_left_x0, panel_left_x1),
        "panel_right": ("y", "z", "x", panel_right_x0, panel_right_x1),
        "panel_top": ("x", "y", "z", panel_top_z0, panel_top_z1),
        "panel_bottom": ("x", "y", "z", panel_bottom_z0, panel_bottom_z1),
    }


def bolt_line(a0: float, a1: float) -> list[float]:
    """a0에서 a1까지를 ceil(길이 / panel_bolt_pitch_max) 구간으로 고르게 나눈 점들(양 끝 포함)."""
    n = math.ceil((a1 - a0) / panel_bolt_pitch_max)
    return [a0 + (a1 - a0) * i / n for i in range(n + 1)]


def bolt_holes() -> dict:
    """패널마다 볼트 구멍 중심 (u, v) 목록.

    네 변의 줄은 패널 변 뒤 골조 부재의 중심선(패널 외곽에서 prof_W / 2 안쪽)을 따라가고, 패널 모서리에서 panel_bolt_edge 띄운 점에서 시작해 반대쪽 모서리에서 panel_bolt_edge 띄운 점에서 끝난다. 바닥 패널은 보강재 중심선 stiff_cx에도 같은 규칙의 줄을 둔다.
    """
    holes = {}
    for label, (u, v, _n, _n0, _n1) in panel_specs().items():
        u0, u1 = FRAME[u]
        v0, v1 = FRAME[v]
        u_lo, u_hi = u0 + prof_W / 2, u1 - prof_W / 2  # 변 쪽 부재 중심선 — 예: x −15 · 1395
        v_lo, v_hi = v0 + prof_W / 2, v1 - prof_W / 2
        u_run = bolt_line(u0 + panel_bolt_edge, u1 - panel_bolt_edge)  # 예: x 0–1380
        v_run = bolt_line(v0 + panel_bolt_edge, v1 - panel_bolt_edge)  # 예: z 0–660
        pts = []
        if label == "panel_front":
            pts += [(a, v_lo) for a in panel_bolt_front_bottom_x]  # 아래 변 — 밀폐재 밖인 양 끝만
        else:
            pts += [(a, v_lo) for a in u_run]  # 아래(앞) 변
        pts += [(a, v_hi) for a in u_run]  # 위(뒤) 변
        pts += [(u_lo, b) for b in v_run]  # 왼쪽(앞) 변
        pts += [(u_hi, b) for b in v_run]  # 오른쪽(뒤) 변
        if label == "panel_bottom":
            for cx in stiff_cx:
                pts += [(cx, b) for b in v_run]  # 바닥 보강재 중심선
        holes[label] = pts
    return holes


def round_cutouts() -> dict:
    """패널마다 둥근 구멍 (지름, [(u, v), …]) 목록. 볼트 구멍, 포트 구멍, 글랜드 구멍."""
    cut = {label: [(panel_bolt_hole_dia, pts)] for label, pts in bolt_holes().items()}
    cut["panel_right"].append((inlet_tube_OD, [(port_y, port_z)]))  # 주입 포트, 관 외경
    cut["panel_left"].append((exhaust_tube_OD, [(port_y, port_z)]))  # 배기 포트, 관 외경
    cut["panel_top"].append((gland_hole_dia, [(gx, gland_y) for gx in gland_x]))  # 글랜드 구멍 3개
    return cut


def check_gland_hole() -> None:
    """params.py의 글랜드 구멍 지름이 cutter STEP의 안지름(가장 작은 원통의 지름)과 같은지 확인한다."""
    cutter = read_step(GLAND_CUTTER_STEP)
    radii = sorted(f.radius for f in cutter.faces() if f.geom_type == bd.GeomType.CYLINDER)
    if not radii or abs(2 * radii[0] - gland_hole_dia) > 1e-6:
        raise ValueError(f"{GLAND_CUTTER_ID} 안지름 {[2 * r for r in radii]}이 gland_hole_dia {gland_hole_dia}와 다르다")


def panel(label: str) -> bd.Solid:
    """패널 한 장. 면 안 외곽은 골조 바깥면 그대로이고, 두께 방향은 panel_specs()의 (n0, n1)이다."""
    u, v, n, n0, n1 = panel_specs()[label]
    u0, u1 = FRAME[u]
    v0, v1 = FRAME[v]
    sketch = bd.Pos(u0, v0) * bd.Rectangle(u1 - u0, v1 - v0, align=(bd.Align.MIN, bd.Align.MIN))
    for dia, pts in round_cutouts()[label]:
        sketch -= [bd.Pos(a, b) * bd.Circle(dia / 2) for a, b in pts]
    if label == "panel_front":
        sketch -= bd.Pos(door_x0, door_z0) * bd.Rectangle(door_x1 - door_x0, door_z1 - door_z0, align=(bd.Align.MIN, bd.Align.MIN))  # 도어 개구
    faces = sketch.faces()
    if len(faces) != 1:
        raise ValueError(f"{label} 판 윤곽이 면 {len(faces)}개로 나뉘었다")
    du, dv = bd.Vector(AXIS[u]), bd.Vector(AXIS[v])
    dn = du.cross(dv)  # 로컬 z — 앞·뒤는 −y, 옆은 +x, 천장·바닥은 +z
    start = n1 if dn.dot(bd.Vector(AXIS[n])) < 0 else n0  # 로컬 z를 따라 t_panel만큼 늘이면 n0–n1을 채우는 면
    origin = bd.Vector(AXIS[n]) * start
    slab = bd.Solid.extrude(faces[0], bd.Vector(0, 0, t_panel))
    placed = slab.moved(bd.Location(bd.Plane(origin=origin, x_dir=du, z_dir=dn)))
    placed.label = label
    return placed


@step(out="../step/chamber_panel.step")
def chamber_panel():
    check_gland_hole()
    panels = [panel(label) for label in panel_specs()]
    for p, (u, v, n, n0, n1) in zip(panels, panel_specs().values()):
        bb = p.bounding_box()
        lo, hi = {"x": bb.min.X, "y": bb.min.Y, "z": bb.min.Z}, {"x": bb.max.X, "y": bb.max.Y, "z": bb.max.Z}
        want = {u: FRAME[u], v: FRAME[v], n: (n0, n1)}
        if max(abs(lo[a] - want[a][0]) + abs(hi[a] - want[a][1]) for a in "xyz") > 1e-6:
            raise ValueError(f"{p.label} 외곽 {bb}이 {want}와 다르다")
    result = bd.Compound(children=panels)
    bb = result.bounding_box()
    want = (out_x0, out_y0, out_z0, out_x1, out_y1, out_z1)
    got = (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z)
    if max(abs(g - w) for g, w in zip(got, want)) > 1e-6:
        raise ValueError(f"패널 외곽 {got}이 {want}와 다르다")
    return result


if __name__ == "__main__":
    chamber_panel()
