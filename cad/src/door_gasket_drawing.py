"""도어 밀폐재의 치수 도면.

`door_gasket()`을 불러 label `door_gasket`인 EPDM 사각 링을 꺼내, 챔버 바깥에서 본 도어 판 쪽 앞면을 `front` 뷰 하나로 그린다. 주 뷰는 같은 판의 가공 도면(`door_gasket_dxf.py`)과 같은 면 · 같은 방향이고, 링 외곽의 왼쪽 아래 모서리가 DXF 원점이다(cad/CLAUDE.md). 치수는 `overall()`의 바깥 크기, 안쪽 개구의 폭 · 높이, 개구가 기준점 쪽 변(왼쪽 · 아래)에서 들어온 거리 둘이고, 점은 params.py의 밀폐재 위치 상수에서, 값은 cadgen이 형상에서 잰다. 링의 폭은 1:5에서 3 mm라 띠를 가로질러 재지 않는다 — 개구까지 들어온 거리가 같은 정보다. 두께는 도곽의 재질 칸이 담는다.

치수 줄의 배치는 cadgen의 동작에 맞춘다. 위쪽 · 왼쪽은 `overall()`이 맨 바깥 줄을 쓰므로, 그 두 쪽에는 판 변에서 잰 들어온 거리만 첫 줄에 두고(1:5에서 3 mm라 글자가 보조선 사이에 들어가지 않으므로 보조선이 글자 밑만 스치는 쪽), 개구의 폭 · 높이는 아래쪽 · 오른쪽 첫 줄에 둔다. 들어온 거리의 두 점은 가로 · 세로로 같은 15만큼 떨어져 있어 어느 쪽 치수인지 형상으로 정해지지 않으므로 방향을 준다.

뷰 자리는 링의 bounding box에서 계산해, 뷰가 용지 가로 가운데에 오고 아래쪽이 노트 · 도곽 위로 떨어지게 둔다.
"""

from __future__ import annotations

from cadgen.eng_drawing import Sheet, eng_drawing

from door_gasket import door_gasket
from params import (
    gasket_T,
    gasket_in_x0,
    gasket_in_x1,
    gasket_in_z0,
    gasket_in_z1,
    gasket_out_x0,
    gasket_out_x1,
    gasket_out_z0,
    gasket_out_z1,
    gasket_y0,
)

SCALE = 0.2  # 1:5
ROW = 12.0  # 치수 줄 하나의 폭(도면 mm). cadgen이 자리를 정하지 않은 치수를 쌓는 간격과 같다
ORIGIN = (82.5, 113.0)  # 뷰 왼쪽 아래 모서리의 도면 위치 mm
MATERIAL = f"EPDM SPONGE {gasket_T:g} mm"
NOTES = ["DOOR-SIDE FACE SHOWN. DATUM: LOWER LEFT CORNER (= DXF ORIGIN)."]


def face(x: float, z: float) -> tuple[float, float, float]:
    """도어 판 쪽 앞면(y = gasket_y0, front 뷰가 보는 면) 위의 점."""
    return (x, gasket_y0, z)


@eng_drawing(out="../pdf/door_gasket.pdf")
def door_gasket_drawing():
    ring = next(p for p in door_gasket().children if p.label == "door_gasket")
    size = ring.bounding_box().size  # front 뷰의 가로가 챔버 x, 세로가 챔버 z
    sheet = Sheet("A3", scale=SCALE, title="DOOR GASKET", material=MATERIAL, revision="A",
                  general_tolerance="ISO 2768-m", notes=NOTES)
    view = sheet.view(ring, "front", at=(ORIGIN[0] + size.X * SCALE / 2, ORIGIN[1] + size.Z * SCALE / 2))
    view.overall()

    # cadgen의 offset은 두 점 가운데 바깥쪽 점에서 잰 도면 mm다. 반올림은 줄 수를 세는 cadgen의 `//`가 부동소수 오차로 한 줄 적게 세지 않게 한다
    # 위쪽 첫 줄: 개구가 왼쪽 변에서 들어온 거리(위 변의 바깥 · 안쪽 모서리)
    view.dim(face(gasket_out_x0, gasket_out_z1), face(gasket_in_x0, gasket_in_z1), orientation="h",
             offset=round(ROW, 6))
    # 왼쪽 첫 줄: 개구가 아래 변에서 들어온 거리(왼쪽 아래의 바깥 · 안쪽 모서리)
    view.dim(face(gasket_out_x0, gasket_out_z0), face(gasket_in_x0, gasket_in_z0), orientation="v",
             offset=round(-ROW, 6))
    # 아래쪽 첫 줄: 개구 폭
    view.dim(face(gasket_in_x0, gasket_in_z0), face(gasket_in_x1, gasket_in_z0), orientation="h",
             offset=round(-(ROW + (gasket_in_z0 - gasket_out_z0) * SCALE), 6))
    # 오른쪽 첫 줄: 개구 높이
    view.dim(face(gasket_in_x1, gasket_in_z0), face(gasket_in_x1, gasket_in_z1), orientation="v",
             offset=round(ROW + (gasket_out_x1 - gasket_in_x1) * SCALE, 6))
    return sheet


if __name__ == "__main__":
    door_gasket_drawing()
