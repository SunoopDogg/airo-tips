"""전장함.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. PETG 3D 프린트 몸체와 뚜껑이고, 바깥 elec_W × elec_D(94 × 74)를 천장 중심 (elec_cx, elec_cy) = (690, 485)에 맞춰 천장 패널 윗면(elec_z0 = 693) 위에 놓는다(`cad/chamber.md` 전장함 세부 · elec_W elec_D elec_H · 글랜드 행, 사용자 결정 2026-10-07).

- 몸체: 바닥 두께 elec_floor_T(z 693–695), 벽 elec_wall(2), 안쪽 90 × 70 × elec_in_H(25)로 위가 열린 상자다. 벽 윗면은 z 720이다.
- 스탠드오프 4개: Ø elec_standoff_dia(6), 높이 elec_standoff_H(10, z 695–705), 축은 전장 기판의 M3 구멍 축(pcb_hole_x × pcb_hole_y = 654 · 726 × 459 · 511)이다. 윗면에 기판 밑면(pcb_z0 = 705)이 얹힌다. 가운데에 M3 나사를 바로 박는 구멍 Ø STANDOFF_HOLE_DIA를 스탠드오프 윗면에서 바닥 윗면까지 뚫고, 바닥은 뚫지 않는다.
- 바닥 글랜드 구멍 3개: 천장 패널의 글랜드 구멍과 같은 지름 gland_hole_dia(Ø20)와 같은 중심(gland_x, gland_y)이다. 글랜드 나사부가 이 구멍을 지나고 잠금 너트가 바닥 윗면에 얹혀 천장 패널과 바닥을 함께 조인다.
- 뒤쪽 벽(y 520–522) USB 구멍: elec_usb_hole_W × elec_usb_hole_H(12 × 7, x × z)의 각진 직사각형, 중심은 전장 기판 USB-C 블록의 중심 (x 690, z usbc_cz = 708.25)이다.
- 뚜껑: 두께 elec_lid_T(2), z 720–722, 바깥 94 × 74의 판이다. 뚜껑을 몸체에 고정하는 방식은 정해지지 않았으므로 판만 그리고 나사 구멍·걸림 턱을 내지 않는다.

label: box_body(솔리드 하나), box_lid(솔리드 하나). 둘은 벽 윗면 z 720에서 면으로만 맞닿는다.
"""

from __future__ import annotations

import math

from cadgen import build123d as bd
from cadgen import step

from params import (
    elec_clr,
    elec_D,
    elec_floor_T,
    elec_H,
    elec_in_H,
    elec_lid_T,
    elec_standoff_dia,
    elec_standoff_H,
    elec_usb_hole_H,
    elec_usb_hole_W,
    elec_W,
    elec_wall,
    elec_x0,
    elec_x1,
    elec_y0,
    elec_y1,
    elec_z0,
    elec_z1,
    gland_hole_dia,
    gland_N,
    gland_x,
    gland_y,
    panel_top_z1,
    pcb_D,
    pcb_hole_dia,
    pcb_hole_x,
    pcb_hole_y,
    pcb_W,
    pcb_x0,
    pcb_x1,
    pcb_y0,
    pcb_y1,
    pcb_z0,
    usbc_cz,
    usbc_x0,
    usbc_x1,
    usbc_z0,
    usbc_z1,
)

STANDOFF_HOLE_DIA = 2.5  # 작업 가정 — 사용자 확인 필요. 스탠드오프의 M3 나사 구멍 지름. M3 × 0.5의 탭 드릴 지름 2.5로, M3 나사를 PETG에 바로 박아 나사산을 내는 구멍이다. 열압입 인서트 구멍(약 Ø4)은 Ø6 스탠드오프에 벽 1 mm만 남겨 쓰지 않았다
STANDOFF_HOLE_DEPTH = elec_standoff_H  # 작업 가정 — 사용자 확인 필요. 스탠드오프 나사 구멍 깊이. 스탠드오프 윗면(z 705)에서 바닥 윗면(z 695)까지로, 바닥을 뚫으면 상자 안이 천장 패널 윗면으로 열리므로 바닥은 남긴다

# z — 아래에서 위로
FLOOR_Z0 = elec_z0  # 바닥 밑면, 천장 패널 윗면 (693)
FLOOR_Z1 = elec_z0 + elec_floor_T  # 바닥 윗면 = 스탠드오프 밑면 = 잠금 너트 밑면 (695)
STANDOFF_Z1 = FLOOR_Z1 + elec_standoff_H  # 스탠드오프 윗면 = 기판 밑면 (705)
WALL_Z1 = FLOOR_Z1 + elec_in_H  # 벽 윗면 = 뚜껑 밑면 (720)

# 안쪽 벽
IN_X0, IN_X1 = elec_x0 + elec_wall, elec_x1 - elec_wall  # (645, 735)
IN_Y0, IN_Y1 = elec_y0 + elec_wall, elec_y1 - elec_wall  # (450, 520)

# USB 구멍 — 뒤쪽 벽, USB-C 블록 중심에 맞춘다
USB_CX = (usbc_x0 + usbc_x1) / 2  # USB-C 블록 중심 x (690)
USB_X0, USB_X1 = USB_CX - elec_usb_hole_W / 2, USB_CX + elec_usb_hole_W / 2  # (684, 696)
USB_Z0, USB_Z1 = usbc_cz - elec_usb_hole_H / 2, usbc_cz + elec_usb_hole_H / 2  # (704.75, 711.75)

_CUT = 1.0  # 빼기용 공구를 면 너머로 늘이는 길이, 형상 치수 아님


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> bd.Solid:
    return bd.Solid.make_box(x1 - x0, y1 - y0, z1 - z0).moved(bd.Location((x0, y0, z0)))


def _cyl_z(cx: float, cy: float, dia: float, z0: float, z1: float) -> bd.Solid:
    """축이 z 방향이고 (cx, cy)를 지나는 원기둥, z0–z1."""
    return bd.Solid.make_cylinder(dia / 2, z1 - z0, plane=bd.Plane(origin=(cx, cy, z0)))


def _one(shape, label: str) -> bd.Solid:
    solids = shape.solids()
    if len(solids) != 1 or not solids[0].is_valid:
        raise ValueError(f"{label} 솔리드가 올바르지 않다 (solids {len(solids)})")
    s = solids[0]
    s.label = label
    return s


def body() -> bd.Solid:
    """바닥 · 벽 · 스탠드오프를 한 솔리드로 만들고 글랜드 구멍 · 나사 구멍 · USB 구멍을 뺀다."""
    shell = _box(elec_x0, elec_x1, elec_y0, elec_y1, FLOOR_Z0, WALL_Z1) - _box(IN_X0, IN_X1, IN_Y0, IN_Y1, FLOOR_Z1, WALL_Z1 + _CUT)
    for gx in gland_x:
        shell = shell - _cyl_z(gx, gland_y, gland_hole_dia, FLOOR_Z0 - _CUT, FLOOR_Z1 + _CUT)
    for hx in pcb_hole_x:
        for hy in pcb_hole_y:
            shell = shell + _cyl_z(hx, hy, elec_standoff_dia, FLOOR_Z1, STANDOFF_Z1)
    for hx in pcb_hole_x:
        for hy in pcb_hole_y:
            shell = shell - _cyl_z(hx, hy, STANDOFF_HOLE_DIA, STANDOFF_Z1 - STANDOFF_HOLE_DEPTH, STANDOFF_Z1 + _CUT)
    shell = shell - _box(USB_X0, USB_X1, IN_Y1 - _CUT, elec_y1 + _CUT, USB_Z0, USB_Z1)
    return _one(shell, "box_body")


def lid() -> bd.Solid:
    """고정 방식이 정해지지 않은 뚜껑 판."""
    return _one(_box(elec_x0, elec_x1, elec_y0, elec_y1, WALL_Z1, elec_z1), "box_lid")


def _check_layout() -> None:
    assert abs((elec_x1 - elec_x0) - elec_W) < 1e-9 and abs((elec_y1 - elec_y0) - elec_D) < 1e-9 and abs((elec_z1 - elec_z0) - elec_H) < 1e-9
    assert elec_z0 == panel_top_z1, "전장함 밑면이 천장 패널 윗면과 다르다"
    assert abs(WALL_Z1 + elec_lid_T - elec_z1) < 1e-9, "벽 윗면 + 뚜껑 두께가 전장함 윗면과 다르다"
    assert abs(STANDOFF_Z1 - pcb_z0) < 1e-9, "스탠드오프 윗면이 기판 밑면과 다르다"
    assert len(gland_x) == gland_N and len(pcb_hole_x) * len(pcb_hole_y) == 4
    # 기판 둘레와 안쪽 벽 사이 여유
    for gap in (pcb_x0 - IN_X0, IN_X1 - pcb_x1, pcb_y0 - IN_Y0, IN_Y1 - pcb_y1):
        assert abs(gap - elec_clr) < 1e-9, f"기판 둘레 여유 {gap}가 elec_clr {elec_clr}와 다르다"
    assert abs((pcb_x1 - pcb_x0) - pcb_W) < 1e-9 and abs((pcb_y1 - pcb_y0) - pcb_D) < 1e-9
    # 나사 구멍은 기판 구멍보다 작고 스탠드오프 안에 있다
    assert STANDOFF_HOLE_DIA < pcb_hole_dia < elec_standoff_dia and 0 < STANDOFF_HOLE_DEPTH <= elec_standoff_H
    # 글랜드 구멍은 바닥 안쪽에 있고 스탠드오프에 닿지 않는다
    r = gland_hole_dia / 2
    assert IN_X0 < min(gland_x) - r and max(gland_x) + r < IN_X1 and IN_Y0 < gland_y - r and gland_y + r < IN_Y1, "글랜드 구멍이 안쪽 벽에 걸린다"
    for gx in gland_x:
        for hx in pcb_hole_x:
            for hy in pcb_hole_y:
                assert math.hypot(hx - gx, hy - gland_y) > r + elec_standoff_dia / 2, f"글랜드 구멍 ({gx}, {gland_y})이 스탠드오프 ({hx}, {hy})에 걸린다"
    # USB 구멍은 뒤쪽 벽 안에 있고 USB-C 블록을 x · z로 감싼다
    assert IN_X0 < USB_X0 and USB_X1 < IN_X1 and FLOOR_Z1 < USB_Z0 and USB_Z1 < WALL_Z1, "USB 구멍이 뒤쪽 벽을 벗어난다"
    assert USB_X0 < usbc_x0 and usbc_x1 < USB_X1 and USB_Z0 < usbc_z0 and usbc_z1 < USB_Z1, "USB 구멍이 USB-C 블록을 감싸지 않는다"


@step(out="../step/electronics_box.step")
def electronics_box():
    _check_layout()
    return bd.Compound(children=[body(), lid()])


if __name__ == "__main__":
    electronics_box()
