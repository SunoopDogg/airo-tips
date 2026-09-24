"""케이블 글랜드.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. M20 케이블 글랜드 3개를 천장 중심 기준 x 방향 한 줄(gland_x, gland_y)에 축을 z 방향으로 단다(`cad/chamber.md` 글랜드 · 케이블 관통 위치 행, 사용자 결정 2026-10-07). step.parts `cable_gland_body_m20`은 외경 44 × 높이 28의 관 하나로 된 외곽 모델이라 간격 30에도 전장함 안에도 들어가지 않아 쓰지 않고, 흔한 M20 플라스틱 케이블 글랜드(돔 너트 + 육각 몸체 + M20 나사부 + 잠금 너트)를 단순 솔리드로 본뜬 대표 형상을 직접 그린다. 돔 너트·몸체 육각·나사부 길이·잠금 너트·가운데 구멍의 크기는 아래의 작업 가정이다. 나사산과 안쪽 실(seal)은 그리지 않는다.

z 방향으로 쌓인 순서: 몸체 육각의 윗면이 천장 패널 안쪽 면 panel_top_z0(690)에 닿고, 그 아래(챔버 안쪽)에 돔 너트의 육각과 돔이 매달린다. 몸체 육각 윗면에서 나사부(Ø THREAD_OD 원통, 나사산 없음)가 위로 올라가 천장 패널 구멍(z 690–693)과 전장함 바닥 구멍(z 693–695)을 지나고, 잠금 너트가 전장함 바닥 윗면(z 695) 위에 놓여 천장 패널과 전장함 바닥을 함께 조인다. 나사부 지름은 패널·전장함 바닥 구멍 gland_hole_dia와 같아 구멍 벽과 면으로 닿는다. 잠금 너트 윗면과 나사부 끝은 전장 기판 밑면(스탠드오프 윗면, z 705)보다 낮다.

육각은 모두 맞변 방향이 x다(두 맞변이 x = 축 ± 맞변 거리/2). 이웃 글랜드끼리 맞변이 마주 보아 틈이 gland_pitch − 맞변 거리가 된다. 전장함 안쪽 벽과 스탠드오프 자리는 아직 전장함 STEP이 없으므로 params.py 상수로 계산해 빌드할 때 assert로 피한다.

label: gland_1, gland_2, gland_3(x가 작은 쪽부터)은 각각 돔 너트·몸체(육각 + 나사부)·잠금 너트 세 솔리드(gland_N_dome, gland_N_body, gland_N_locknut)를 담은 compound다. 세 솔리드는 면으로만 맞닿고 부피로 겹치지 않는다(돔 너트 윗면 ↔ 몸체 육각 밑면, 잠금 너트 구멍 벽 ↔ 나사부 원통면). 돔 너트와 몸체에는 케이블이 지나는 가운데 구멍 Ø BORE_DIA를 축을 따라 뚫는다.
"""

import math

from cadgen import build123d as bd
from cadgen import srgb
from cadgen import step

from params import (
    elec_floor_T,
    elec_standoff_dia,
    elec_wall,
    elec_x0,
    elec_x1,
    elec_y0,
    elec_y1,
    elec_z0,
    gland_hole_dia,
    gland_N,
    gland_pitch,
    gland_x,
    gland_y,
    panel_top_z0,
    pcb_hole_x,
    pcb_hole_y,
    pcb_z0,
)
from style import nylon

THREAD_OD = gland_hole_dia  # 나사부 지름 — M20의 호칭 지름 20, 나사산 없는 원통으로 그린다. 패널·전장함 바닥 구멍 gland_hole_dia(Ø20)와 같다 (chamber.md 글랜드 행 "M20 글랜드", 명세 "단순 원통 Ø20")

# 크기는 모두 작업 가정 — 사용자 확인 필요. 흔한 M20 × 1.5 플라스틱 케이블 글랜드(조임 범위 약 6–12 mm)를 본뜬 대표값이다.
BODY_AF = 24.0  # 작업 가정 — 사용자 확인 필요. 몸체 육각 맞변 거리. 꼭짓점 간 거리 27.71 < 30(간격)
BODY_HEX_H = 7.0  # 작업 가정 — 사용자 확인 필요. 몸체 육각 높이(z)
THREAD_L = 12.0  # 작업 가정 — 사용자 확인 필요. 나사부 길이(몸체 육각 윗면 z 690부터). 잠금 너트를 다 물려면 5 + LOCKNUT_H 이상, 끝이 전장 기판 밑면(z 705) 아래이려면 15 이하
DOME_AF = 24.0  # 작업 가정 — 사용자 확인 필요. 돔 너트 육각 맞변 거리
DOME_HEX_H = 8.0  # 작업 가정 — 사용자 확인 필요. 돔 너트 육각 높이(z)
DOME_DIA = 22.0  # 작업 가정 — 사용자 확인 필요. 돔 너트 육각 아래 돔 부분의 지름. 육각 맞변(24)보다 작게 해 육각 변과 접하지 않게 했다
DOME_H = 6.0  # 작업 가정 — 사용자 확인 필요. 돔 부분 높이(z)
DOME_FILLET = 4.0  # 작업 가정 — 사용자 확인 필요. 돔 부분 아래 모서리 둥글림 반지름
LOCKNUT_AF = 24.0  # 작업 가정 — 사용자 확인 필요. 잠금 너트 육각 맞변 거리
LOCKNUT_H = 5.0  # 작업 가정 — 사용자 확인 필요. 잠금 너트 높이(z). 10 미만이어야 한다
BORE_DIA = 13.0  # 작업 가정 — 사용자 확인 필요. 케이블이 지나는 가운데 구멍(실 입구) 지름. 조임 범위 상한(약 12)보다 조금 크게 골랐다

# z — 아래(챔버 안쪽)에서 위로
BODY_Z1 = panel_top_z0  # 몸체 육각 윗면, 천장 패널 안쪽 면 (690)
BODY_Z0 = BODY_Z1 - BODY_HEX_H  # 몸체 육각 밑면 = 돔 너트 윗면 (683)
DOME_HEX_Z0 = BODY_Z0 - DOME_HEX_H  # 돔 너트 육각 밑면 = 돔 부분 윗면 (675)
DOME_Z0 = DOME_HEX_Z0 - DOME_H  # 돔 부분 밑면, 글랜드 맨 아래 (669)
THREAD_Z1 = BODY_Z1 + THREAD_L  # 나사부 끝 (702)
LOCK_Z0 = elec_z0 + elec_floor_T  # 잠금 너트 밑면, 전장함 바닥 윗면 (695)
LOCK_Z1 = LOCK_Z0 + LOCKNUT_H  # 잠금 너트 윗면 (700)

# 전장함 안쪽 — 잠금 너트가 피해야 할 자리 (params.py에서 계산). 전장 기판 밑면은 pcb_z0(705), 스탠드오프 축은 pcb_hole_x × pcb_hole_y(654 · 726 × 459 · 511)
BOX_IN_X = (elec_x0 + elec_wall, elec_x1 - elec_wall)  # 전장함 안쪽 벽 x (645, 735)
BOX_IN_Y = (elec_y0 + elec_wall, elec_y1 - elec_wall)  # 전장함 안쪽 벽 y (450, 520)


def _corner(af: float) -> float:
    """맞변 거리 af인 정육각형의 꼭짓점 간 거리."""
    return af / math.cos(math.radians(30))


def _hex_prism(cx: float, cy: float, af: float, z0: float, z1: float) -> bd.Solid:
    """축이 z 방향이고 (cx, cy)를 지나는 정육각 기둥, z0–z1. 맞변이 x 방향이다(꼭짓점은 ±y 쪽)."""
    rc = _corner(af) / 2
    pts = [(cx + rc * math.cos(math.radians(30 + 60 * k)), cy + rc * math.sin(math.radians(30 + 60 * k)), z0) for k in range(6)]
    face = bd.Face(bd.Wire.make_polygon(pts, close=True))
    return bd.Solid.extrude(face, bd.Vector(0, 0, z1 - z0))


def _cyl_z(cx: float, cy: float, dia: float, z0: float, z1: float) -> bd.Solid:
    """축이 z 방향이고 (cx, cy)를 지나는 원기둥, z0–z1."""
    return bd.Solid.make_cylinder(dia / 2, z1 - z0, plane=bd.Plane(origin=(cx, cy, z0)))


def _one(shape, label: str) -> bd.Solid:
    solids = shape.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{label} 솔리드가 올바르지 않다 (solids {len(solids)})")
    s = solids[0]
    s.label = label
    s.color = srgb(nylon)
    return s


def dome_nut(i: int, cx: float, cy: float) -> bd.Solid:
    hexa = _hex_prism(cx, cy, DOME_AF, DOME_HEX_Z0, BODY_Z0)
    cap = _cyl_z(cx, cy, DOME_DIA, DOME_Z0, DOME_HEX_Z0)
    bottom = min(cap.edges().filter_by(bd.GeomType.CIRCLE), key=lambda e: e.center().Z)
    cap = cap.fillet(DOME_FILLET, [bottom])
    nut = (hexa + cap) - _cyl_z(cx, cy, BORE_DIA, DOME_Z0, BODY_Z0)
    return _one(nut, f"gland_{i}_dome")


def body(i: int, cx: float, cy: float) -> bd.Solid:
    hexa = _hex_prism(cx, cy, BODY_AF, BODY_Z0, BODY_Z1)
    thread = _cyl_z(cx, cy, THREAD_OD, BODY_Z1, THREAD_Z1)
    b = (hexa + thread) - _cyl_z(cx, cy, BORE_DIA, BODY_Z0, THREAD_Z1)
    return _one(b, f"gland_{i}_body")


def lock_nut(i: int, cx: float, cy: float) -> bd.Solid:
    nut = _hex_prism(cx, cy, LOCKNUT_AF, LOCK_Z0, LOCK_Z1) - _cyl_z(cx, cy, THREAD_OD, LOCK_Z0, LOCK_Z1)
    return _one(nut, f"gland_{i}_locknut")


def gland(i: int, cx: float, cy: float) -> bd.Compound:
    parts = [dome_nut(i, cx, cy), body(i, cx, cy), lock_nut(i, cx, cy)]
    return bd.Compound(children=parts, label=f"gland_{i}")


def _check_layout() -> None:
    assert len(gland_x) == gland_N
    assert THREAD_OD == gland_hole_dia, "나사부 지름이 패널·전장함 바닥 구멍 지름과 다르다"
    assert BORE_DIA < THREAD_OD and DOME_DIA < DOME_AF and DOME_FILLET < DOME_H
    assert DOME_DIA / 2 - DOME_FILLET > BORE_DIA / 2, "돔 둥글림이 가운데 구멍까지 먹는다"
    assert max(_corner(BODY_AF), _corner(DOME_AF), _corner(LOCKNUT_AF)) < gland_pitch, "육각 꼭짓점 간 거리가 글랜드 간격 이상이다"
    assert LOCKNUT_H < pcb_z0 - LOCK_Z0, "잠금 너트 높이가 전장함 바닥 윗면에서 기판 밑면까지보다 크다"
    assert LOCK_Z1 <= THREAD_Z1 <= pcb_z0, "나사부 끝이 잠금 너트 윗면보다 낮거나 기판 밑면보다 높다"
    half_x, half_y = LOCKNUT_AF / 2, _corner(LOCKNUT_AF) / 2
    assert BOX_IN_X[0] < min(gland_x) - half_x and max(gland_x) + half_x < BOX_IN_X[1], "잠금 너트가 전장함 안쪽 벽(x)에 걸린다"
    assert BOX_IN_Y[0] < gland_y - half_y and gland_y + half_y < BOX_IN_Y[1], "잠금 너트가 전장함 안쪽 벽(y)에 걸린다"
    for gx in gland_x:
        for sx in pcb_hole_x:
            for sy in pcb_hole_y:
                d = math.hypot(sx - gx, sy - gland_y)
                assert d > half_y + elec_standoff_dia / 2, f"잠금 너트 ({gx}, {gland_y})가 스탠드오프 ({sx}, {sy})에 걸린다"


@step(out="../step/cable_gland.step")
def cable_gland():
    _check_layout()
    return bd.Compound(children=[gland(i, gx, gland_y) for i, gx in enumerate(gland_x, 1)])


if __name__ == "__main__":
    cable_gland()
