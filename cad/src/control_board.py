"""전장 기판.

챔버 좌표계(원점은 챔버 내부 바닥의 도어측 좌측 모서리, Z-up, x 폭, y 깊이, z 높이, mm)에서 조립 위치에 놓인 채로 모델링한다. 자체 PCB pcb_W × pcb_D × pcb_T(80 × 60 × 1.6)를 전장함 가운데(pcb_cx, pcb_cy) = (690, 485), 전장함 바닥 스탠드오프 위(밑면 pcb_z0 = 705, 윗면 pcb_z1 = 706.6)에 놓고, M3 구멍 pcb_hole_dia(Ø3.2) 4개를 각 모서리에서 x·y로 pcb_hole_edge(4)에 뚫는다(`cad/chamber.md` pcb_W pcb_D pcb_T · 전장함 세부 · elec_W elec_D elec_H 행, 사용자 결정 2026-10-07).

기판 윗면에는 ESP32 모듈과 USB-C 외곽 블록만 놓고 나머지 소자는 그리지 않는다(사용자 결정 2026-10-07).

- ESP32 모듈: 벤더 STEP `step/imported/ESP32-S3-WROOM-1.step`(step.parts `esp32_s3_wroom_1`, KiCad 풋프린트 모델)을 그대로 읽어 옮긴다. 벤더 좌표는 원점이 모듈 평면 외곽의 가운데이고 z = 0이 모듈 밑면(패드 면)이며, 외곽은 x ±9, y ±12.75, z 0–3.1이다. 안테나(두께 0.2 박막, y 6.75–12.25)는 +y 끝에 있고 차폐 캔(y −11.7–5.9)과 끝 패드 줄(y −12.75–−11.9)은 −y 쪽이다. 안테나 끝이 기판 앞쪽 변(−y)을 향하도록 z축으로 180° 돌리고, 모듈 가운데 x를 기판 가운데에, 벤더 z = 0을 기판 윗면에, 안테나 끝(벤더 최대 y)을 기판 앞쪽 변에서 ESP_EDGE_INSET 안쪽에 맞춘다.
- USB-C: usbc_W × usbc_D × usbc_H(9 × 7.5 × 3.3) 외곽 블록을 기판 뒤쪽 변(+y) 가운데에 뒷면을 맞춰 기판 윗면 위에 놓는다(params.py usbc_x0…usbc_z1).

label: pcb(솔리드 하나), esp32_module(벤더 솔리드 52개를 담은 compound), usb_c(솔리드 하나).
"""

from __future__ import annotations

import math
import os

from cadgen import build123d as bd
from cadgen import read_step
from cadgen import srgb
from cadgen import step

import style
from params import (
    pcb_cx,
    pcb_D,
    pcb_hole_dia,
    pcb_hole_N,
    pcb_hole_x,
    pcb_hole_y,
    pcb_T,
    pcb_W,
    pcb_x0,
    pcb_x1,
    pcb_y0,
    pcb_y1,
    pcb_z0,
    pcb_z1,
    usbc_x0,
    usbc_x1,
    usbc_y0,
    usbc_y1,
    usbc_z0,
    usbc_z1,
)

ESP32_STEP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "step", "imported", "ESP32-S3-WROOM-1.step")

ESP_EDGE_INSET = 0.0  # 작업 가정 — 사용자 확인 필요. 안테나 끝(모듈 −y 끝)이 기판 앞쪽 변(y 455)에서 안쪽으로 들어온 거리. 0이면 안테나 끝이 앞쪽 변과 같은 선이다. 모듈을 기판 밖으로 내밀지 않는 범위에서 안테나를 가장 바깥에 둔다

_CAN_CLEAR_MIN = 5.0  # 벤더 방향 확인용 문턱값, 형상 치수 아님. 차폐 캔 끝이 모듈 +y 끝에서 이만큼 떨어져 있어야 +y 끝을 안테나 쪽으로 본다(벤더에서 잰 간격은 6.85)


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> bd.Solid:
    return bd.Solid.make_box(x1 - x0, y1 - y0, z1 - z0).moved(bd.Location((x0, y0, z0)))


def board() -> bd.Solid:
    """구멍 4개를 뚫은 기판 솔리드."""
    body = _box(pcb_x0, pcb_x1, pcb_y0, pcb_y1, pcb_z0, pcb_z1)
    for hx in pcb_hole_x:
        for hy in pcb_hole_y:
            body = body - bd.Solid.make_cylinder(pcb_hole_dia / 2, pcb_T + 2, plane=bd.Plane(origin=(hx, hy, pcb_z0 - 1)))
    solids = body.solids()
    if not body.is_valid or len(solids) != 1:
        raise ValueError(f"기판 솔리드가 올바르지 않다 (solids {len(solids)})")
    pcb = solids[0]
    pcb.label = "pcb"
    pcb.color = srgb(style.pcb)
    return pcb


def esp32_module() -> bd.Compound:
    """벤더 ESP32 모듈을 기판 윗면 앞쪽 변에 안테나가 −y를 향하게 놓은 compound."""
    vendor = read_step(ESP32_STEP)
    vb = vendor.bounding_box()
    # 벤더 STEP의 방향 확인: 가장 높은 솔리드(차폐 캔)가 +y 끝까지 오지 않아야 +y 끝이 안테나 쪽이다.
    can = max(vendor.solids(), key=lambda s: s.bounding_box().max.Z)
    if can.bounding_box().max.Y > vb.max.Y - _CAN_CLEAR_MIN:
        raise ValueError(f"벤더 ESP32 STEP의 차폐 캔이 +y 끝까지 온다 — 안테나 방향을 다시 재야 한다: {can.bounding_box()}")
    vx_c = (vb.min.X + vb.max.X) / 2
    # z축 180° 회전: (x, y, z) → (−x + tx, −y + ty, z + tz)
    tx = pcb_cx + vx_c  # 모듈 가운데 x → 기판 가운데
    ty = pcb_y0 + ESP_EDGE_INSET + vb.max.Y  # 안테나 끝(벤더 최대 y) → 앞쪽 변 + ESP_EDGE_INSET
    tz = pcb_z1 - vb.min.Z  # 모듈 밑면 → 기판 윗면
    module = vendor.moved(bd.Location((tx, ty, tz), (0, 0, 1), 180))
    module.label = "esp32_module"
    return module


def usb_c() -> bd.Solid:
    block = _box(usbc_x0, usbc_x1, usbc_y0, usbc_y1, usbc_z0, usbc_z1)
    block.label = "usb_c"
    block.color = srgb(style.usb_c)
    return block


def _rect_clear_of_holes(bb: bd.BoundBox, what: str) -> None:
    """평면 외곽 bb가 기판 안에 있고, 어느 구멍 원에도 닿지 않는지 확인한다."""
    assert pcb_x0 <= bb.min.X and bb.max.X <= pcb_x1 and pcb_y0 <= bb.min.Y and bb.max.Y <= pcb_y1, f"{what}가 기판 외곽을 벗어난다: {bb}"
    for hx in pcb_hole_x:
        for hy in pcb_hole_y:
            dx = max(bb.min.X - hx, 0.0, hx - bb.max.X)
            dy = max(bb.min.Y - hy, 0.0, hy - bb.max.Y)
            assert math.hypot(dx, dy) > pcb_hole_dia / 2, f"{what}가 구멍 ({hx}, {hy})에 걸린다"


@step(out="../step/control_board.step")
def control_board():
    assert pcb_hole_N == len(pcb_hole_x) * len(pcb_hole_y) == 4
    assert abs((pcb_x1 - pcb_x0) - pcb_W) < 1e-9 and abs((pcb_y1 - pcb_y0) - pcb_D) < 1e-9
    pcb = board()
    module = esp32_module()
    usb = usb_c()
    mb, ub = module.bounding_box(), usb.bounding_box()
    _rect_clear_of_holes(mb, "ESP32 모듈")
    _rect_clear_of_holes(ub, "USB-C 블록")
    assert mb.max.Y < ub.min.Y, "ESP32 모듈과 USB-C 블록이 y로 겹친다"
    return bd.Compound(children=[pcb, module, usb])


if __name__ == "__main__":
    control_board()
